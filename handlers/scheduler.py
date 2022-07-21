from collections import defaultdict
from views import scheduler_view
from utils import discord, dynamodb


# TODO seems like a bad import
from constants.emojis import AvailabilityEmoji, ClassEmoji

SCHEDULE_TEMPLATE = f"""<:{AvailabilityEmoji.COMING.emoji_name}:{AvailabilityEmoji.COMING.emoji_id}> : {{0}}
<:{AvailabilityEmoji.MAYBE.emoji_name}:{AvailabilityEmoji.MAYBE.emoji_id}> : {{1}}
<:{AvailabilityEmoji.NOT_COMING.emoji_name}:{AvailabilityEmoji.NOT_COMING.emoji_id}> : {{2}}"""

SCHEDULE_TABLE = "lost_ark_schedule"
PKEY = "pk"
USER_KEY = "user_id"
AVAILABILITY_KEY = "availability"


# TODO(table schema): change table structure to have multiple independent partition keys
COMMITMENT_PKEY = "event_commitment:{}user:{}"
CLASS_PKEY = "class_for_user"




def _mention_user(user_id):
    return f"<@{user_id}>"

def _get_user_class(user_id):
    return dynamodb.get_rows(SCHEDULE_TABLE, CLASS_PKEY, f'user_id = {user_id}')

# def _get_all_user_commitments(user_id):
    # return dynamodb.query_with_pk(SCHEDULE_TABLE, "event_commitment:", filter_expression=f"user = {user_id}")


def _get_schedule(event_type):
    # TODO(table schema): after separating the pkeys, stop scanning

    all_rows = dynamodb.get_rows(SCHEDULE_TABLE)

    statuses = {state.name: "" for state in AvailabilityEmoji}

    for row in all_rows:
        if event_type in row[PKEY]:
            # statuses[row[AVAILABILITY_KEY]].append(row[PKEY].split("user:")[1]) 
            user = row[PKEY].split("user:")[1]
            # user_class = _get_user_class(user)
            # class_emoji = f"<:{ClassEmoji[user_class].emoji_name}:{ClassEmoji[user_class].emoji_id}>"
            # statuses[row[AVAILABILITY_KEY]].append(f"{class_emoji} {_mention_user(user)}")
            statuses[row[AVAILABILITY_KEY]] += f" {_mention_user(user)}"
 
    return SCHEDULE_TEMPLATE.format(*statuses.values())


def _update_user_class():
    pass

def _update_schedule(schedule_type, user, changes):
    status = changes["id"]
    dynamodb.set_rows(SCHEDULE_TABLE, COMMITMENT_PKEY.format(schedule_type, user), {"availability": status})


def _clear_schedule(schedule_type):
    for entry in dynamodb.get_rows(SCHEDULE_TABLE, pkey_value=COMMITMENT_PKEY.format(schedule_type)):
        dynamodb.delete_item(SCHEDULE_TABLE, entry)


def _generate_header(event_type):
    # TODO: generate a nicer msg title \
    return f"Scheduling for {event_type}"


def display(info):
    event_type = discord.get_channel_by_id(info["channel_id"])["name"]
    return {
        "content": f"{_generate_header(event_type)}\n{_get_schedule(event_type)}",
        "components": scheduler_view.SchedulerView.COMPONENTS
    }


def handle_button(info):
    channel_name = discord.get_channel_by_id(info["channel_id"])["name"]
    event_type = channel_name

    _update_schedule(channel_name, info["user_id"], info["data"])

    new_msg = f"{_generate_header(event_type)}\n{_get_schedule(event_type)}"

    # TODO: track different instances of the same event type

    return new_msg


def handle_selector(info):
    original_msg = discord.get_message_by_id(info["channel_id"], info["base_msg_id"])["content"]
    
    user_id = info["user_id"]
    data = info["data"]
    
    new_msg = original_msg.strip() + f"\n {_mention_user(user_id)} picked {data['values']}!"
    return new_msg       


