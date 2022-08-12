import os
import re
import time
from enum import Enum
from datetime import datetime, tzinfo, timedelta
from xmlrpc.client import Boolean
from dateutil import parser

from views import scheduler_view
from utils import discord, dynamodb

os.putenv("TZ", "America/Los_Angeles")
time.tzset()

# TODO seems like a bad import
from constants.emojis import AvailabilityEmoji, ClassEmoji, DPS_CLASSES, SUPPORT_CLASSES


class EventStatus(str, Enum):
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"


class PacificTime(tzinfo):
    def tzname(self, **kwargs):
        return "PT"

    def utcoffset(self, dt):
        return timedelta(hours=-8) + self.dst(dt)

    def dst(self, dt):
        tt = time.localtime()

        if tt.tm_isdst:
            return timedelta(hours=1)
        return timedelta(hours=0)


BLANK = "\u200b"
DOT = "\u2022"

SCHEDULE_TABLE = "lost_ark_schedule"
PKEY = "pk"


# event table schema
COMMITMENT_PKEY = "event:{}user:{}"
EVENT_INFO_PKEY = "event:{}info"
EVENT_TYPE_COLUMN = "event_type"
EVENT_ID_COLUMN = "event_id"
USER_COLUMN = "user_id"
STATUS_COLUMN = "status_str"
CLASS_COLUMN = "char_class"
TIME_COLUMN = "start_time"
CHANNEL_COLUMN = "channel_id"
MESSAGE_COLUMN = "message_id"
THREAD_COLUMN = "thread_id"

EVENT_ID_INDEX = "event_id-index"
USER_INDEX = "user_id-index"

# class table schema = "lost_ark_sc
CLASS_PKEY = "user_class"

EIGHT_PPL_RAIDS = "(?:{})".format(
    "|".join(
        [
            r".*argos.*",
            r".*valtan.*",
            r".*vykas.*",
        ]
    )
)

FOUR_PPL_RAIDS = "(?:{})".format("|".join([r".*oreha.*"]))


def _is_event_full(event_id: str, event_name: str) -> bool:
    tally = sum(_tally_classes(event_id))
    if re.match(EIGHT_PPL_RAIDS, event_name, flags=re.IGNORECASE):
        return tally >= 8
    elif re.match(FOUR_PPL_RAIDS, event_name, flags=re.IGNORECASE):
        return tally >= 4
    else:
        return False


def schedule_embed(event_id: str, server_id, is_full=False) -> dict:
    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_name = event_info[EVENT_TYPE_COLUMN]
    start_time = parser.parse(event_info[TIME_COLUMN]).replace(tzinfo=PacificTime())
    event_status = event_info[STATUS_COLUMN]
    creator = event_info[USER_COLUMN]

    start_time_iso = start_time.isoformat()
    start_time_pretty = f"<t:{int(start_time.timestamp())}>"

    all_rows = dynamodb.query_index(
        SCHEDULE_TABLE,
        EVENT_ID_INDEX,
        {EVENT_ID_COLUMN: event_id},
        filterExpression=f"attribute_exists({STATUS_COLUMN})",
    )

    statuses = {state.name: "" for state in AvailabilityEmoji}
    for row in all_rows:
        status = row[STATUS_COLUMN]
        if status not in statuses.keys():
            continue

        user = row[USER_COLUMN]
        user_class = row.get(CLASS_COLUMN)

        if user_class:
            class_emoji = f"<:{ClassEmoji[user_class].emoji_name}:{ClassEmoji[user_class].emoji_id}>"
        else:
            class_emoji = ""
        statuses[status] += f"{class_emoji} {discord.mention_user(user)}\n"

    party_fields = _get_party_fields(event_name, event_id)

    signup_fields = []
    for state in AvailabilityEmoji:
        signup_fields.append(
            {
                "name": f"{state} {state.name}",
                "value": f"{statuses[state.name] if statuses[state.name] else BLANK}",
                "inline": True,
            }
        )

    if is_full:
        # red
        color = 0xAA4A44
    else:
        # base on event status
        color = 0xFFFF00 if event_status == EventStatus.TENTATIVE else 0x00FF00

    return {
        "type": "rich",
        "title": f"Scheduling for {event_name}{'- full ' if is_full else ''}",
        "description": f"Timezone-adjusted: {start_time_pretty}",
        "color": color,
        "fields": [
            *party_fields,
            *signup_fields,
        ],
        "timestamp": start_time_iso,
        "footer": {
            "text": f"{event_status} | created by {discord.get_user_nickname_by_id(server_id, creator)}"
        },
    }


def get_all_user_commitments(info):
    user_id = info[USER_COLUMN]
    user_events = dynamodb.query_index(
        SCHEDULE_TABLE,
        USER_INDEX,
        {USER_COLUMN: user_id},
        filterExpression=f"{STATUS_COLUMN} = :{STATUS_COLUMN}",
        expressionAttributeValues={
            f":{STATUS_COLUMN}": AvailabilityEmoji.COMING.name,
        },
    )

    relevant_rows = []
    for row in user_events:
        if MESSAGE_COLUMN in row and CHANNEL_COLUMN in row:
            message_link = f"https://discord.com/channels/{info['server_id']}/{row[CHANNEL_COLUMN]}/{row[MESSAGE_COLUMN]}"
        else:
            message_link = ""

        time_string = row.get(TIME_COLUMN, "unknown")
        event_type = row.get(EVENT_TYPE_COLUMN)
        event_id = row.get(EVENT_ID_COLUMN)

        try:
            start_time = parser.parse(time_string).replace(tzinfo=PacificTime())
            if start_time >= datetime.now().replace(tzinfo=PacificTime()):
                relevant_rows.append(
                    {
                        EVENT_TYPE_COLUMN: event_type,
                        TIME_COLUMN: start_time.ctime(),
                        "message_link": message_link,
                        EVENT_ID_COLUMN: event_id,
                    }
                )

        except:
            continue

    if not relevant_rows:
        fields = ["Not currently signed up for any events!"]
    else:
        relevant_rows.sort(key=lambda item: item[TIME_COLUMN], reverse=False)
        fields = []
        for row in relevant_rows:
            if row["message_link"]:
                details_link = f"[Details]({row['message_link']})"
            else:
                details_link = f"Original message lost 4ever"
            fields.append(
                {
                    "name": row[EVENT_TYPE_COLUMN],
                    "value": f"{row[TIME_COLUMN]}\n{details_link}",
                    "inline": False,
                }
            )

    return {
        "type": "rich",
        "title": f"My events",
        "color": 0x6495ED,
        "fields": [*fields],
    }


def _tally_classes(event_id):
    all_rows = dynamodb.query_index(
        SCHEDULE_TABLE,
        EVENT_ID_INDEX,
        {EVENT_ID_COLUMN: event_id},
        filterExpression=f"{STATUS_COLUMN} = :{STATUS_COLUMN}",
        expressionAttributeValues={
            f":{STATUS_COLUMN}": AvailabilityEmoji.COMING.name,
        },
    )

    dps = 0
    supp = 0
    flex = 0

    for row in all_rows:
        user_class = row.get(CLASS_COLUMN)
        if not user_class or ClassEmoji[user_class] == ClassEmoji.CLEAR_SELECTION:
            flex += 1
        elif ClassEmoji[user_class] in DPS_CLASSES:
            dps += 1
        elif ClassEmoji[user_class] in SUPPORT_CLASSES:
            supp += 1
        else:
            raise ValueError(f"? Unrecognized class {user_class}")

    return dps, supp, flex


def _get_party_fields(event_name, event_id):
    if re.match(EIGHT_PPL_RAIDS, event_name, flags=re.IGNORECASE):
        n_dps = 6
        n_supp = 2
    elif re.match(FOUR_PPL_RAIDS, event_name, flags=re.IGNORECASE):
        n_dps = 3
        n_supp = 1
    else:
        return []

    dps, supp, flex = _tally_classes(event_id)

    flex_row = (
        {"name": "Flex", "value": f"{flex}/?", "inline": True}
        if flex
        else {"name": BLANK, "value": BLANK, "inline": True}
    )
    return [
        {"name": "DPS", "value": f"{dps}/{n_dps}", "inline": True},
        {"name": "Supports", "value": f"{supp}/{n_supp}", "inline": True},
        flex_row,
    ]


def _update_schedule(event_type, user, event_id, **kwargs):
    cols = {EVENT_TYPE_COLUMN: event_type, EVENT_ID_COLUMN: event_id, USER_COLUMN: user}

    dynamodb.set_rows(
        SCHEDULE_TABLE,
        COMMITMENT_PKEY.format(event_id, user),
        {
            **cols,
            **kwargs,
        },
    )


def _create_event(
    event_type, event_id, start_time, user_id, message_id, channeL_id, thread_id
):
    dynamodb.set_rows(
        SCHEDULE_TABLE,
        EVENT_INFO_PKEY.format(event_id),
        {
            EVENT_TYPE_COLUMN: event_type,
            EVENT_ID_COLUMN: event_id,
            TIME_COLUMN: start_time,
            STATUS_COLUMN: EventStatus.TENTATIVE.value,
            USER_COLUMN: user_id,
            MESSAGE_COLUMN: message_id,
            CHANNEL_COLUMN: channeL_id,
            THREAD_COLUMN: thread_id,
        },
    )


def _clear_schedule(event_id, user):
    for entry in dynamodb.get_rows(
        SCHEDULE_TABLE,
        pkey_value=COMMITMENT_PKEY.format(event_id, user),
        filterExpression=f"{EVENT_TYPE_COLUMN} = {event_id}",
    ):
        dynamodb.delete_item(SCHEDULE_TABLE, entry)


def _add_event_to_calendar(event_id: str, server_id: str):
    # create an `external` event
    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_name = event_info[EVENT_TYPE_COLUMN]
    start_time = parser.parse(event_info[TIME_COLUMN]).replace(tzinfo=PacificTime())
    event_status = event_info[STATUS_COLUMN]
    creator = event_info[USER_COLUMN]

    if MESSAGE_COLUMN in event_info and CHANNEL_COLUMN in event_info:
        message_link = f"Details: https://discord.com/channels/{server_id}/{event_info[CHANNEL_COLUMN]}/{event_info[MESSAGE_COLUMN]}"
    else:
        message_link = ""

    VC1_ID = "951040587266662405"

    event_details = {
        "channel_id": VC1_ID,
        "name": event_name,
        "description": f"Created by {discord.get_user_nickname_by_id(server_id, creator)}\n{message_link}",  # @mentions don't use server nicknames properly
        "privacy_level": 2,  # https://discord.com/developers/docs/resources/guild-scheduled-event#guild-scheduled-event-object-guild-scheduled-event-privacy-level
        "scheduled_start_time": start_time.isoformat(),
        "entity_type": 2,  # https://discord.com/developers/docs/resources/guild-scheduled-event#guild-scheduled-event-object-guild-scheduled-event-entity-types; external requires end time, soooo
    }

    resp = discord.create_server_event(server_id, event_details)
    if resp.ok:
        dynamodb.set_rows(
            SCHEDULE_TABLE,
            EVENT_INFO_PKEY.format(event_id),
            {
                STATUS_COLUMN: EventStatus.CONFIRMED.value,
            },
        )

    return resp.reason


def _set_class(event_id, user, char_class):
    dynamodb.set_rows(
        SCHEDULE_TABLE,
        COMMITMENT_PKEY.format(event_id, user),
        {USER_COLUMN: user, CLASS_COLUMN: char_class},
    )


# public
def display(info: dict) -> dict:
    cmd = info["command"]
    cmd_input = info["options"]
    server_id = info["server_id"]
    channel_id = info["channel_id"]
    if cmd == "make_raid":
        time_string = cmd_input["start_time"]
        event_type = cmd_input.get("raid_name")
        user_id = info["user_id"]
        if not event_type:
            event_type = discord.get_channel_by_id(info["channel_id"])["name"].title()
        event_id = info["interaction_id"]

        try:
            start_time = parser.parse(time_string, ignoretz=True)
            pretty_time = start_time.strftime("%A %B %d, %-I.%M %p")
        except parser.ParserError:
            raise parser.ParserError(
                f"Couldn't parse this start time: `{time_string}`. Try a different format? Some examples: `saturday 8 pm`, `2022 07 30 20:00:00`"
            )

        message_id = discord.get_interaction_message_id(
            info["application_id"], info["interaction_token"]
        )["id"]

        thread_info = discord.create_thread(
            channel_id,
            f"{event_type} | {pretty_time} PT",
            message_id,
            duration=3 * 24 * 60,
        )
        thread_id = thread_info["id"]

        _create_event(
            event_type,
            event_id,
            start_time.isoformat(),
            user_id,
            message_id,
            channel_id,
            thread_id,
        )

        time.sleep(2)

        return {
            "embeds": [schedule_embed(event_id, server_id)],
            "components": scheduler_view.SchedulerView().components,
        }
    else:
        raise ValueError(f"Unrecognized command: {cmd}")


def is_schedule_button(component_id):
    return (
        component_id in AvailabilityEmoji._member_names_
        or component_id in scheduler_view.ScheduleButtons.values()
    )


def is_schedule_selector(component_id):
    return component_id == scheduler_view.CLASS_SELECTOR_ID


def handle_button(info):
    event_id = info["base_interaction_id"]
    base_channel_id = info["base_channel_id"]
    message_id = info["base_msg_id"]
    server_id = info["server_id"]
    user_id = info["user_id"]
    button = info["data"]["id"]

    if button in AvailabilityEmoji._member_names_:
        event_info = dynamodb.get_rows(
            SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
        )[0]

        event_type = event_info[EVENT_TYPE_COLUMN]
        start_time = event_info[TIME_COLUMN]
        thread_id = event_info[THREAD_COLUMN]

        # use the base message id as a unique event identifier
        _update_schedule(
            event_type,
            user_id,
            event_id,
            **{
                STATUS_COLUMN: button,
                TIME_COLUMN: start_time,
                MESSAGE_COLUMN: message_id,
                CHANNEL_COLUMN: base_channel_id,
            },
        )

        is_full = _is_event_full(event_id, event_type)

        new_msg = {
            "embeds": [schedule_embed(event_id, server_id, is_full=is_full)],
            "components": scheduler_view.SchedulerView(is_full=is_full).components,
        }

        if button == AvailabilityEmoji.NOT_COMING.name:
            discord.remove_thread_member(thread_id, user_id)
        else:
            discord.add_thread_member(thread_id, user_id)
        return new_msg

    elif button == scheduler_view.ScheduleButtons.ADD_TO_CALENDAR:
        resp = _add_event_to_calendar(event_id, server_id)
        discord.send_followup(
            info["application_id"],
            info["interaction_token"],
            f"Event creation request sent: {resp}",
            ephemeral=True,
        )

        event_info = dynamodb.get_rows(
            SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
        )[0]

        event_type = event_info[EVENT_TYPE_COLUMN]

        # refresh original message status
        is_full = _is_event_full(event_id, event_type)
        new_msg = {"embeds": [schedule_embed(event_id, server_id, is_full=is_full)]}
        return new_msg
    elif button == scheduler_view.ScheduleButtons.CHANGE_TIME:
        pass
    elif button == scheduler_view.ScheduleButtons.SEE_COMMITMENTS:
        output = {"embeds": [get_all_user_commitments(info)]}

        discord.send_followup(
            info["application_id"], info["interaction_token"], output, ephemeral=True
        )


def handle_selector(info):
    data = info["data"]
    event_id = info["base_interaction_id"]
    server_id = info["server_id"]

    _set_class(event_id, info["user_id"], data["values"][0])

    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_type = event_info[EVENT_TYPE_COLUMN]

    is_full = _is_event_full(event_id, event_type)
    new_msg = {"embeds": [schedule_embed(event_id, server_id, is_full=is_full)]}
    return new_msg
