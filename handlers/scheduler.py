import os
import re
import time
from enum import Enum
from datetime import datetime, tzinfo, timedelta
from dateutil import parser

from views import scheduler_view
from utils import discord, dynamodb

os.putenv("TZ", "America/Los_Angeles")
time.tzset()

# TODO seems like a bad import
from constants.emojis import AvailabilityEmoji, ClassEmoji, DPS_CLASSES, SUPPORT_CLASSES

BLANK = "\u200b"
DOT = "\u2022"
NEWLINE = chr(10)

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
CHANNEL_NAME_COLUMN = "channel_name"
MESSAGE_COLUMN = "message_id"
THREAD_COLUMN = "thread_id"
DESCRIPTION_COLUMN = "description"

EVENT_ID_INDEX = "event_id-index"
USER_INDEX = "user_id-index"

# track calendar posts
CALENDAR_PKEY = "calendar:{}"

# class table schema = "lost_ark_sc
CLASS_PKEY = "user_class"

STANDARD_PER_PARTY_SUPP = 1
STANDARD_PER_PARTY_DPS = 3
NO_SIZE_LIMIT = 999

ADMIN_ROLE_ID = "951412916912013332"
EVENT_EXPIRATION_GRACE_PERIOD = 15  # min


class Raid:
    def __init__(
        self,
        name,
        n_supports=NO_SIZE_LIMIT,
        n_dps=NO_SIZE_LIMIT,
        aliases=[],
        excludes=[],
    ):
        self.name = name
        self.n_supports = n_supports
        self.n_dps = n_dps
        self.aliases = aliases
        self.excludes = excludes

        self.regex = "(?:{})".format(
            "|".join([rf".*{option}.*" for option in [self.name, *self.aliases]])
        )

        self.max_size = self.n_supports + self.n_dps
        self.has_size_limit = (
            self.n_dps != NO_SIZE_LIMIT and self.n_supports != NO_SIZE_LIMIT
        )

    def matches(self, raid_indicator, custom_name=""):
        return re.match(self.regex, raid_indicator, flags=re.IGNORECASE) and not any(
            exclude in custom_name for exclude in self.excludes
        )

    def pretty_name(self):
        return f"=={self.name}=="


ALL_RAIDS = [
    # Raid("test", n_supports=1, n_dps=0),
    Raid(
        "GvG/GvE",
        aliases=["gvg", "gve"],
    ),
    Raid(
        "Abyssals",
        n_supports=STANDARD_PER_PARTY_SUPP,
        n_dps=STANDARD_PER_PARTY_DPS,
        aliases=["Oreha"],
    ),
    Raid(
        "Argos",
        n_supports=STANDARD_PER_PARTY_SUPP * 2,
        n_dps=STANDARD_PER_PARTY_DPS * 2,
        excludes=["bus"],
    ),
    Raid(
        "Valtan",
        n_supports=STANDARD_PER_PARTY_SUPP * 2,
        n_dps=STANDARD_PER_PARTY_DPS * 2,
    ),
    Raid(
        "Vykas",
        n_supports=STANDARD_PER_PARTY_SUPP * 2,
        n_dps=STANDARD_PER_PARTY_DPS * 2,
    ),
    Raid(
        "Kakul Saydon",
        n_supports=STANDARD_PER_PARTY_SUPP,
        n_dps=STANDARD_PER_PARTY_DPS,
        aliases=["kuku", "clown"],
    ),
    Raid(
        "Secret Maps",
        n_supports=STANDARD_PER_PARTY_SUPP,
        n_dps=STANDARD_PER_PARTY_DPS,
        aliases=["secret-maps"],
    ),
    Raid(
        "Achievement Hunters",
        aliases=["achievement-hunters"],
    ),
    Raid(
        "Other Spam",
        aliases=["spam", "main", "pics"],
    ),
]


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


class Event:
    def __init__(self, event_id, **kwargs) -> None:
        # mandatory fields
        self.event_id = event_id

        # fields with defaults
        self.event_name = kwargs.pop("event_name")
        self.channel_id = kwargs.pop("channel_id")

        self.start_time = kwargs.pop("start_time")
        self.is_done = True
        self.parsed_time = None
        if self.start_time:
            self.parsed_time = parser.parse(self.start_time).replace(
                tzinfo=PacificTime()
            )

            expiration_time = datetime.now().replace(tzinfo=PacificTime()) - timedelta(
                minutes=EVENT_EXPIRATION_GRACE_PERIOD
            )
            if self.parsed_time > expiration_time:
                self.is_done = False
            # return early since past events aren't useful
            else:
                return

        self.event_type = "Unknown"
        self.channel_name = kwargs.pop("channel_name")
        if not self.channel_name:
            self.channel_name = discord.get_channel_by_id(self.channel_id)["name"]
        for raid in ALL_RAIDS:
            if raid.matches(self.channel_name):
                self.event_type = raid.name
                self.raid = raid
                break

        self.tally = sum(_tally_classes(self.event_id))

        # add other fields if specified
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def __eq__(self, other):
        return self.event_id == other.event_id

    def pretty_print(self):
        ts = self.parsed_time.timestamp()
        start_time_long = discord.format_time(ts)
        start_time_relative = discord.format_time(ts, format="R")

        if self.raid.has_size_limit:
            if self.tally == self.raid.max_size:
                size = "(FULL) "
            else:
                size = f"({self.tally}/{self.raid.max_size}) "
        else:
            size = ""

        return f"[{size}{start_time_long} ({start_time_relative}) | {self.event_name}](https://discord.com/channels/{self.server_id}/{self.channel_id}/{self.message_id})\n"


def _is_event_full(event_id: str, event_name: str) -> bool:
    tally = sum(_tally_classes(event_id))
    for raid in ALL_RAIDS:
        if raid.matches(event_name):
            return tally >= raid.max_size

    return False


def _get_calendar_posts():
    return dynamodb.get_rows(
        SCHEDULE_TABLE,
        filterExpression=f"contains ({PKEY}, :calendar)",
        expressionAttributeValues={":calendar": "calendar"},
    )


def _update_calendars(server_id):
    # update all calendar posts
    new_calendar = {
        "embeds": [calendar_embed(server_id)],
        "components": scheduler_view.CalendarView().components,
    }
    calendar_posts = _get_calendar_posts()
    for post in calendar_posts:
        discord.edit_message(post[CHANNEL_COLUMN], post[MESSAGE_COLUMN], new_calendar)


def calendar_embed(server_id: str) -> dict:
    all_rows = dynamodb.get_rows(
        SCHEDULE_TABLE,
        filterExpression=f"contains ({PKEY}, :info)",
        expressionAttributeValues={":info": "info"},
    )

    events = []
    seen = []

    for row in all_rows:
        event_id = row[EVENT_ID_COLUMN]
        if event_id in seen:
            continue
        else:
            event_name = row[EVENT_TYPE_COLUMN]
            event = Event(
                event_id=event_id,
                event_name=event_name,
                channel_id=row.get(CHANNEL_COLUMN),
                channel_name=row.get(CHANNEL_NAME_COLUMN),
                server_id=server_id,
                message_id=row[MESSAGE_COLUMN],
                thread_id=row[THREAD_COLUMN],
                start_time=row[TIME_COLUMN],
                creator=row[USER_COLUMN],
            )
            if not event.is_done:
                events.append(event)

    events.sort(key=lambda event: event.start_time, reverse=False)

    fields = []
    for raid in ALL_RAIDS:
        relevant_events = "".join(
            [
                f"{event.pretty_print()}"
                for event in events
                if event.event_type == raid.name
            ]
        )

        if relevant_events:
            fields.append(
                {
                    "name": raid.pretty_name(),
                    "value": relevant_events,
                    "inline": False,
                }
            )

    return {
        "type": "rich",
        "title": f"Upcoming Raids",
        "description": f"[Google Calendar](https://calendar.google.com/calendar/u/3?cid=MDRnNmpycnFsYXJyczExc21hNjY1N2RsdHNAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)\n\nAll times are timezone-adjusted; click the link to go to the original message.\nTo make a new raid, type `/make_raid <start time> <raid name>` in the correct channel!\nThis message will be automatically updated as events are created.\n",
        "fields": fields,
    }


def schedule_embed(event_id: str, server_id, is_full=False) -> dict:
    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_name = event_info[EVENT_TYPE_COLUMN]
    start_time = parser.parse(event_info[TIME_COLUMN]).replace(tzinfo=PacificTime())
    event_status = event_info[STATUS_COLUMN]
    creator = event_info[USER_COLUMN]
    channel_name = event_info.get(CHANNEL_NAME_COLUMN, event_name)
    description = event_info.get(DESCRIPTION_COLUMN, "")

    ts = start_time.timestamp()
    start_time_long = discord.format_time(ts)
    start_time_relative = discord.format_time(ts, format="R")

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

    party_fields = _get_party_fields(channel_name, event_name, event_id)

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
        "title": f"Scheduling for {event_name}{'- full' if is_full else ''}",
        "description": f"Timezone-adjusted: {start_time_long} ({start_time_relative}){NEWLINE*2 if description else ''}{description}",
        "color": color,
        "fields": [
            *party_fields,
            *signup_fields,
        ],
    }


def get_all_user_commitments(info):
    user_id = info[USER_COLUMN]
    user_events = {}
    user_events[AvailabilityEmoji.COMING.name] = dynamodb.query_index(
        SCHEDULE_TABLE,
        USER_INDEX,
        {USER_COLUMN: user_id},
        filterExpression=f"{STATUS_COLUMN} = :{STATUS_COLUMN}",
        expressionAttributeValues={
            f":{STATUS_COLUMN}": AvailabilityEmoji.COMING.name,
        },
    )

    user_events[AvailabilityEmoji.MAYBE.name] = dynamodb.query_index(
        SCHEDULE_TABLE,
        USER_INDEX,
        {USER_COLUMN: user_id},
        filterExpression=f"{STATUS_COLUMN} = :{STATUS_COLUMN}",
        expressionAttributeValues={
            f":{STATUS_COLUMN}": AvailabilityEmoji.MAYBE.name,
        },
    )

    fields = []
    for response, events in user_events.items():
        relevant_rows = []
        for row in events:
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
                            TIME_COLUMN: start_time.timestamp(),
                            "message_link": message_link,
                            EVENT_ID_COLUMN: event_id,
                        }
                    )

            except:
                continue

        field_value = ""
        if relevant_rows:
            relevant_rows.sort(key=lambda item: item[TIME_COLUMN], reverse=False)
            for row in relevant_rows:
                if row["message_link"]:
                    details_link = f"[Details]({row['message_link']})"
                else:
                    details_link = f"Original message lost 4ever"

                ts = row[TIME_COLUMN]
                start_time_long = discord.format_time(ts)
                start_time_relative = discord.format_time(ts, format="R")
                field_value += f"**{row[EVENT_TYPE_COLUMN]}**: {start_time_long} ({start_time_relative})- {details_link}\n"
        else:
            field_value = "Not currently signed up for any events!"

        fields.append(
            {
                "name": response.capitalize(),
                "value": field_value,
                "inline": False,
            }
        )

    return {
        "type": "rich",
        "title": f"My events",
        "color": 0x6495ED,
        "fields": fields,
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


def _get_party_fields(channel_name, event_name, event_id):
    for raid in ALL_RAIDS:
        if raid.matches(channel_name, custom_name=event_name):
            if not raid.has_size_limit:
                return []
            n_dps = raid.n_dps
            n_supp = raid.n_supports
            break
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


def change_time_prompt(event_id, event_type, new_time=None):
    if new_time:
        msg = f"""Time for `{event_type}` changed to `{new_time}`!"""
    else:
        msg = f"""Send this command in any channel to quietly change the time for `{event_type}`:\n\n`/change_time {event_id} <new time>`"""

    return {
        "type": "rich",
        "title": f"Change Time",
        "description": msg
    }


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
    event_type,
    event_id,
    start_time,
    user_id,
    message_id,
    channel_id,
    thread_id,
    description,
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
            CHANNEL_COLUMN: channel_id,
            CHANNEL_NAME_COLUMN: discord.get_channel_by_id(channel_id)["name"],
            THREAD_COLUMN: thread_id,
            DESCRIPTION_COLUMN: description,
        },
    )


def _log_calendar_post(interaction_id, channel_id, message_id):
    dynamodb.set_rows(
        SCHEDULE_TABLE,
        CALENDAR_PKEY.format(interaction_id),
        {
            MESSAGE_COLUMN: message_id,
            CHANNEL_COLUMN: channel_id,
        },
    )


def _delete_event(event_id, user_id, server_id):
    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]
    creator = event_info[USER_COLUMN]
    thread_id = event_info[THREAD_COLUMN]

    if user_id == creator or discord.is_admin(
        server_id, user_id, admin_role_id=ADMIN_ROLE_ID
    ):
        dynamodb.delete_item(
            SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
        )
        discord.archive_thread(thread_id)
    else:
        raise PermissionError(
            f"Only the creator of this event can delete it; message {discord.mention_user(creator)} or an admin (<@&{ADMIN_ROLE_ID}>)"
        )


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
        description = cmd_input.get("description", BLANK)
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

        # create thread
        channel_info = discord.get_channel_by_id(channel_id)
        if "thread_metadata" in channel_info:
            thread_id = "-1"
        else:
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
            description,
        )

        _update_calendars(server_id)

        # render message
        time.sleep(1)

        return {
            "embeds": [schedule_embed(event_id, server_id)],
            "components": scheduler_view.SchedulerView().components,
        }
    elif cmd == "calendar":
        interaction_id = info["interaction_id"]

        message_id = discord.get_interaction_message_id(
            info["application_id"], info["interaction_token"]
        )["id"]

        _log_calendar_post(interaction_id, channel_id, message_id)
        return {
            "embeds": [calendar_embed(server_id)],
            "components": scheduler_view.CalendarView().components,
        }
    else:
        raise ValueError(f"Unrecognized command: {cmd}")


def is_schedule_button(component_id):
    return (
        component_id in AvailabilityEmoji._member_names_
        or component_id in scheduler_view.ScheduleButtons.values()
        or component_id in scheduler_view.CalendarButtons.values()
    )


def is_schedule_selector(component_id):
    return component_id == scheduler_view.CLASS_SELECTOR_ID


def change_time(info, options):
    server_id = info["server_id"]
    event_id = options[EVENT_ID_COLUMN]
    new_time = options[TIME_COLUMN]
    new_time = parser.parse(new_time).replace(tzinfo=PacificTime())

    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_type = event_info[EVENT_TYPE_COLUMN]

    dynamodb.set_rows(
        SCHEDULE_TABLE,
        EVENT_INFO_PKEY.format(event_id), 
        {
            TIME_COLUMN: new_time.isoformat()
        },
    )
    # refresh original message status
    is_full = _is_event_full(event_id, event_info[CHANNEL_NAME_COLUMN])
    new_msg = {
        "embeds": [schedule_embed(event_id, server_id, is_full=is_full)],
        "components": scheduler_view.SchedulerView(is_full=is_full).components,
    }
    _update_calendars(server_id)
    response = discord.edit_message(
                event_info[CHANNEL_COLUMN], event_info[MESSAGE_COLUMN], new_msg
            )

    if response.ok:
        return {"embeds": [change_time_prompt(event_id, event_type, new_time=new_time.isoformat())]}

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

        is_full = _is_event_full(event_id, event_info[CHANNEL_NAME_COLUMN])

        new_msg = {
            "embeds": [schedule_embed(event_id, server_id, is_full=is_full)],
            "components": scheduler_view.SchedulerView(is_full=is_full).components,
        }

        if button == AvailabilityEmoji.NOT_COMING.name:
            discord.remove_thread_member(thread_id, user_id)
        else:
            discord.add_thread_member(thread_id, user_id)

        _update_calendars(server_id)
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
        is_full = _is_event_full(event_id, event_info[CHANNEL_NAME_COLUMN])
        new_msg = {
            "embeds": [schedule_embed(event_id, server_id, is_full=is_full)],
            "components": scheduler_view.SchedulerView(is_full=is_full).components,
        }
        return new_msg
    elif button == scheduler_view.ScheduleButtons.CHANGE_TIME:
        event_info = dynamodb.get_rows(
            SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
        )[0]

        event_type = event_info[EVENT_TYPE_COLUMN]
        output = {"embeds": [change_time_prompt(event_id, event_type)]}

        discord.send_followup(
            info["application_id"], info["interaction_token"], output, ephemeral=True
        )
    elif button == scheduler_view.ScheduleButtons.DELETE:
        try:
            _delete_event(event_id, user_id, server_id)
            _update_calendars(server_id)
            discord.delete_message(base_channel_id, message_id)
        except PermissionError as e:
            discord.send_followup(
                info["application_id"],
                info["interaction_token"],
                str(e),
                ephemeral=True,
            )
    elif button == scheduler_view.ScheduleButtons.SEE_COMMITMENTS:
        output = {"embeds": [get_all_user_commitments(info)]}

        discord.send_followup(
            info["application_id"], info["interaction_token"], output, ephemeral=True
        )
    elif button == scheduler_view.CalendarButtons.REFRESH:
        new_msg = {
            "embeds": [calendar_embed(server_id)],
            "components": scheduler_view.CalendarView().components,
        }
        return new_msg


def handle_selector(info):
    data = info["data"]
    event_id = info["base_interaction_id"]
    server_id = info["server_id"]

    _set_class(event_id, info["user_id"], data["values"][0])

    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_type = event_info[EVENT_TYPE_COLUMN]

    is_full = _is_event_full(event_id, event_info[CHANNEL_NAME_COLUMN])
    new_msg = {
        "embeds": [schedule_embed(event_id, server_id, is_full=is_full)],
        "components": scheduler_view.SchedulerView(is_full=is_full).components,
    }
    return new_msg
