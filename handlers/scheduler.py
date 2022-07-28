from collections import defaultdict
from tracemalloc import start
from views import scheduler_view
from utils import discord, dynamodb


# TODO seems like a bad import
from constants.emojis import AvailabilityEmoji, ClassEmoji, DPS_CLASSES, SUPPORT_CLASSES

SCHEDULE_TEMPLATE = f"""
DPS: {{3}}/6 | Supports: {{4}}/2
{AvailabilityEmoji.COMING}:\n{{0}}
{AvailabilityEmoji.NOT_COMING}:\n{{1}}
{AvailabilityEmoji.MAYBE}:\n{{2}}"""

IND_CALENDAR_TEMPLATE = f"""
Event: {{event_type}}
Start time: {{start_time}}
Jump to original message: {{message_link}}
"""

SCHEDULE_TABLE = "lost_ark_schedule"
PKEY = "pk"


# event table schema
COMMITMENT_PKEY = "event:{}user:{}"
EVENT_INFO_PKEY = "event:{}info"
EVENT_TYPE_COLUMN = "event_type"
EVENT_ID_COLUMN = "event_id"
USER_COLUMN = "user_id"
STATUS_COLUMN = "availability"
CLASS_COLUMN = "char_class"
TIME_COLUMN = "start_time"
MESSAGE_COLUMN = "message_id"


EVENT_ID_INDEX = "event_id-index"
USER_INDEX = "user_id-index"

# class table schema
CLASS_PKEY = "user_class"


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

    user_events.sort(key=lambda item: item.get(TIME_COLUMN, "99999"), reverse=False)

    if not user_events:
        return "Not currently signed up for any events!"

    output = ""
    for row in user_events:
        if MESSAGE_COLUMN in row:
            message_link = f"https://discord.com/channels/{info['server_id']}/{info['channel_id']}/{row[MESSAGE_COLUMN]}"
        else:
            message_link = "lost 4ever"

        start_time = row.get(TIME_COLUMN, "unknown")

        event_type = row.get(EVENT_TYPE_COLUMN)

        output += IND_CALENDAR_TEMPLATE.format(
            event_type=event_type, start_time=start_time, message_link=message_link
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


def _get_schedule(event_id, user):
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
        statuses[status] += f"   {class_emoji} {_mention_user(user)}\n"

    dps, supp = _tally_classes(event_id)
    return SCHEDULE_TEMPLATE.format(*statuses.values(), dps, supp)


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


def _create_event(event_type, event_id, start_time):
    dynamodb.set_rows(
        SCHEDULE_TABLE,
        EVENT_INFO_PKEY.format(event_id),
        {
            EVENT_TYPE_COLUMN: event_type,
            EVENT_ID_COLUMN: event_id,
            TIME_COLUMN: start_time,
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

    if cmd == "make_raid":
        start_time = cmd_input["start_time"]
        event_type = cmd_input.get("raid_name")
        if not event_type:
            event_type = discord.get_channel_by_id(info["channel_id"])["name"]

        event_id = info["interaction_id"]

        _create_event(event_type, event_id, start_time)

        return {
            "content": f"{_generate_header(event_type, start_time=start_time)}\n{_get_schedule(event_id, info['user_id'])}",
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

    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_type = event_info[EVENT_TYPE_COLUMN]
    start_time = event_info[TIME_COLUMN]

    # use the base message id as a unique event identifier
    _update_schedule(
        event_type,
        info["user_id"],
        event_id,
        **{
            STATUS_COLUMN: info["data"]["id"],
            TIME_COLUMN: start_time,
            MESSAGE_COLUMN: message_id,
        },
    )

    new_msg = f"{_generate_header(event_type, start_time)}\n{_get_schedule(event_id, info['user_id'])}"

    return new_msg


def handle_selector(info):
    data = info["data"]
    event_id = info["base_interaction_id"]
    event_info = dynamodb.get_rows(
        SCHEDULE_TABLE, pkey_value=EVENT_INFO_PKEY.format(event_id)
    )[0]

    event_type = event_info[EVENT_TYPE_COLUMN]
    start_time = event_info[TIME_COLUMN]

    _set_class(event_id, info["user_id"], data["values"][0])
    new_msg = f"{_generate_header(event_type, start_time)}\n{_get_schedule(event_id, info['user_id'])}"
    return new_msg
