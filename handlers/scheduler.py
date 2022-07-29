from dis import disco
import re
import time
from enum import Enum
from datetime import datetime, tzinfo, timedelta
from tracemalloc import start
from dateutil import parser

from views import scheduler_view
from utils import discord, dynamodb


# TODO seems like a bad import
from constants.emojis import AvailabilityEmoji, ClassEmoji, DPS_CLASSES, SUPPORT_CLASSES


IND_CALENDAR_TEMPLATE = f"""
Event: {{event_type}}
Start time: {{start_time}}
Jump to original message: {{message_link}}
"""


class EventStatus(str, Enum):
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"


class PacificTime(tzinfo):
    def tzname(self, **kwargs):
        return "PT"

    def utcoffset(self, dt):
        return timedelta(hours=-7)


BLANK = "\u200b"


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


def schedule_embed(event_id: str, server_id) -> dict:
    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_name = event_info[EVENT_TYPE_COLUMN]
    start_time = parser.parse(event_info[TIME_COLUMN]).replace(tzinfo=PacificTime())
    event_status = event_info[STATUS_COLUMN]
    creator = event_info[USER_COLUMN]

    start_time_iso = start_time.isoformat()
    print(start_time_iso)
    start_time_ctime = start_time.ctime()

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
        statuses[status] += f"{class_emoji} {_mention_user(user)}\n"

    party_fields = _get_party_fields(event_name, event_id)

    signup_fields = []
    for state in AvailabilityEmoji:
        signup_fields.append(
            {
                "name": f"{state} {state.name}",
                "value": f"{statuses[state.name] if statuses[state.name] else BLANK}",
                "inline": False,
            }
        )

    return {
        "type": "rich",
        "title": f"Scheduling for {event_name}",
        "description": f"{event_name} at {start_time_ctime} PT",
        "color": 0xFFFF00 if event_status == EventStatus.TENTATIVE else 0x00FF00,
        "fields": [*party_fields, *signup_fields],
        "timestamp": start_time_iso,
        "footer": {
            "text": f"{event_status} ? created by {discord.get_user_nickname_by_id(server_id, creator)}"
        },
    }


def _mention_user(user_id):
    return f"<@{user_id}>"


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
        if MESSAGE_COLUMN in row:
            message_link = f"https://discord.com/channels/{info['server_id']}/{info['channel_id']}/{row[MESSAGE_COLUMN]}"
        else:
            message_link = "lost 4ever"

        time_string = row.get(TIME_COLUMN, "unknown")
        event_type = row.get(EVENT_TYPE_COLUMN)

        try:
            start_time = parser.parse(time_string).replace(tzinfo=PacificTime())
            if start_time >= datetime.now():
                relevant_rows.append(
                    {
                        EVENT_TYPE_COLUMN: event_type,
                        TIME_COLUMN: start_time.ctime(),
                        "message_link": message_link,
                    }
                )

        except:
            continue

    if not relevant_rows:
        return "Not currently signed up for any events!"

    relevant_rows.sort(key=lambda item: item[TIME_COLUMN], reverse=False)
    output = ""
    for row in relevant_rows:
        output += IND_CALENDAR_TEMPLATE.format(
            event_type=event_type,
            start_time=start_time.ctime(),
            message_link=message_link,
        )

    return output


def _tally_classes(event_id):
    all_rows = dynamodb.query_index(
        SCHEDULE_TABLE,
        EVENT_ID_INDEX,
        {EVENT_ID_COLUMN: event_id},
        filterExpression=f"attribute_exists({CLASS_COLUMN}) AND {STATUS_COLUMN} = :{STATUS_COLUMN}",
        expressionAttributeValues={
            f":{STATUS_COLUMN}": AvailabilityEmoji.COMING.name,
        },
    )

    dps = 0
    supp = 0

    for row in all_rows:
        user_class = row[CLASS_COLUMN]
        if ClassEmoji[user_class] in DPS_CLASSES:
            dps += 1
        elif ClassEmoji[user_class] in SUPPORT_CLASSES:
            supp += 1
        else:
            raise ValueError(f"? Unrecognized class {user_class}")

    return dps, supp


def _get_party_fields(event_name, event_id):
    if re.match(EIGHT_PPL_RAIDS, event_name, flags=re.IGNORECASE):
        n_dps = 6
        n_supp = 2
    elif re.match(FOUR_PPL_RAIDS, event_name, flags=re.IGNORECASE):
        n_dps = 3
        n_supp = 1
    else:
        return []

    dps, supp = _tally_classes(event_id)

    return [
        {"name": "DPS", "value": f"{dps}/{n_dps}", "inline": True},
        {"name": "Supports", "value": f"{supp}/{n_supp}", "inline": True},
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


def _create_event(event_type, event_id, start_time, user_id, message_id, thread_id):
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


def _set_class(event_id, user, char_class):
    dynamodb.set_rows(
        SCHEDULE_TABLE,
        COMMITMENT_PKEY.format(event_id, user),
        {USER_COLUMN: user, CLASS_COLUMN: char_class},
    )


def _generate_header(event_type: str, start_time: str = ""):
    # TODO: generate a nicer msg title \
    header = f"Scheduling for {event_type}: "
    if start_time:
        header += f"starting at {start_time}"
    return header


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
            event_type = discord.get_channel_by_id(info["channel_id"])["name"]
        event_id = info["interaction_id"]

        try:
            start_time = parser.parse(time_string, ignoretz=True)
        except parser.ParserError:
            raise parser.ParserError(
                f"Couldn't parse this start time: `{time_string}`. Try a different format? Some examples: `saturday 8 pm`, `2022 07 30 20:00:00`"
            )

        message_id = discord.get_interaction_message_id(
            info["application_id"], info["interaction_token"]
        )["id"]

        thread_info = discord.create_thread(channel_id, f"{event_type}", message_id)
        thread_id = thread_info["id"]

        _create_event(event_type, event_id, time_string, user_id, message_id, thread_id)

        time.sleep(2)

        return {
            "embeds": [schedule_embed(event_id, server_id)],
            "components": scheduler_view.SchedulerView.COMPONENTS,
        }
    else:
        raise ValueError(f"Unrecognized command: {cmd}")


def is_schedule_button(component_id):
    return component_id in [state.name for state in AvailabilityEmoji]


def is_schedule_selector(component_id):
    return component_id == scheduler_view.CLASS_SELECTOR_ID


def handle_button(info):
    event_id = info["base_interaction_id"]
    message_id = info["base_msg_id"]
    server_id = info["server_id"]
    user_id = info["user_id"]
    button = info["data"]["id"]

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
        },
    )

    if button == AvailabilityEmoji.NOT_COMING.name:
        print(discord.remove_thread_member(thread_id, user_id))
    else:
        print(discord.add_thread_member(thread_id, user_id))

    new_msg = {"embeds": [schedule_embed(event_id, server_id)]}
    return new_msg


def handle_selector(info):
    data = info["data"]
    event_id = info["base_interaction_id"]
    server_id = info["server_id"]

    _set_class(event_id, info["user_id"], data["values"][0])
    new_msg = {"embeds": [schedule_embed(event_id, server_id)]}
    return new_msg
