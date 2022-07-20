from views import scheduler_view
from utils import discord


def _parse_schedule(pretty_schedule):
    # TODO: parse bullet-point content into json schedule
    pass

def _prettify_schedule(json_schedule):
    # TODO: generate bullet-point content from json schedule
    pass

def _update_schedule(old_schedule, changes):
    # TODO: apply changes specified by button-click or whatever to existing schedule
    pass

def _generate_header(channel_id):
    # TODO: generate a nicer msg title 
    channel = discord.get_channel_by_id(channel_id)
    return f"Scheduling for {channel['name']}"

def display(info):
    return {
        "content": f"{_generate_header(info['channel_id'])}",
        "components": scheduler_view.SchedulerView.COMPONENTS
    }


def handle(info):
    original_msg = discord.get_message_by_id(info["channel_id"], info["base_msg_id"])["content"]
    
    # TODO

    # old_schedule = _parse_schedule(original_msg)
    # new_schedule = _update_schedule()
    # new_msg      = _prettify_schedule(new_schedule)
    
    user_id = info["user_id"]
    new_msg = original_msg.strip() + f"; <@{user_id}> clicked!"
    
    return new_msg

        


