from collections import defaultdict
from views import scheduler_view
from utils import discord, dynamodb


# TODO seems like a bad import
from constants.emojis import AvailabilityEmoji, ClassEmoji, DPS_CLASSES, SUPPORT_CLASSES

SCHEDULE_TEMPLATE = f"""
DPS: {{3}}/6 | Supports: {{4}}/2
{AvailabilityEmoji.COMING}:\n{{0}}
{AvailabilityEmoji.NOT_COMING}:\n{{1}}
{AvailabilityEmoji.MAYBE}:\n{{2}}"""

SCHEDULE_TABLE = "lost_ark_schedule"
PKEY = "pk"
USER_KEY = "user_id"
AVAILABILITY_KEY = "availability"


# event table schema
COMMITMENT_PKEY = "event:{}user:{}"
EVENT_TYPE_COLUMN = "event_type"
EVENT_ID_COLUMN = "event_id"
USER_COLUMN = "user_id"
STATUS_COLUMN = "availability"
CLASS_COLUMN = "char_class"
TIME_COLUMN = "start_time"

EVENT_ID_INDEX = "event_id-index"
USER_INDEX = "user_id-index"

# class table schema
CLASS_PKEY = "user_class"


def _mention_user(user_id):
    return f"<@{user_id}>"


# def _get_all_user_commitments(user_id):
# return dynamodb.query_with_pk(SCHEDULE_TABLE, "event_commitment:", filter_expression=f"user = {user_id}")


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
        user_class = row.get(CLASS_COLUMN)
        if ClassEmoji[user_class] in DPS_CLASSES:
            dps += 1
        elif ClassEmoji[user_class] in SUPPORT_CLASSES:
            supp += 1
        else:
            raise ValueError(f"? Unrecognized class {user_class}")

    return dps, supp


def _get_schedule(event_id, user):

    all_rows = dynamodb.query_index(
        SCHEDULE_TABLE, EVENT_ID_INDEX, {EVENT_ID_COLUMN: event_id}
    )

    statuses = {state.name: "" for state in AvailabilityEmoji}
    for row in all_rows:
        user = row[USER_COLUMN]
        user_class = row.get(CLASS_COLUMN)
        if user_class:
            class_emoji = f"<:{ClassEmoji[user_class].emoji_name}:{ClassEmoji[user_class].emoji_id}>"
        else:
            class_emoji = ""
        statuses[row[AVAILABILITY_KEY]] += f"   {class_emoji} {_mention_user(user)}\n"

    dps, supp = _tally_classes(event_id)
    return SCHEDULE_TEMPLATE.format(*statuses.values(), dps, supp)


def _update_schedule(event_type, user, event_id, changes):
    status = changes["id"]
    dynamodb.set_rows(
        SCHEDULE_TABLE,
        COMMITMENT_PKEY.format(event_id, user),
        {
            EVENT_TYPE_COLUMN: event_type,
            EVENT_ID_COLUMN: event_id,
            USER_COLUMN: user,
            STATUS_COLUMN: status,
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

        event_id = "new event"

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
    channel_name = discord.get_channel_by_id(info["channel_id"])["name"]
    event_type = channel_name
    event_id = info["base_msg_id"]

    # use the base message id as a unique event identifier
    _update_schedule(channel_name, info["user_id"], event_id, info["data"])

    new_msg = (
        f"{_generate_header(event_type)}\n{_get_schedule(event_id, info['user_id'])}"
    )

    return new_msg


def handle_selector(info):
    data = info["data"]
    channel_name = discord.get_channel_by_id(info["channel_id"])["name"]
    event_type = channel_name
    event_id = info["base_msg_id"]

    _set_class(event_id, info["user_id"], data["values"][0])
    new_msg = (
        f"{_generate_header(event_type)}\n{_get_schedule(event_id, info['user_id'])}"
    )
    return new_msg
