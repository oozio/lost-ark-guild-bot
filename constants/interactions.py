from enum import Enum

# TODO: move this file into utils

class InteractionsType(int, Enum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5

class InteractionsCallbackType(int, Enum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9
    

def parse_basic_input(body):
    return {
        "channel_id": body["channel_id"],
        "server_id": body["guild_id"],
        "user_id": body["member"]["user"]["id"],
        "role_ids": body["member"]["roles"]
    }

def parse_button_input(action_rows):
    buttons = []
    
    for action_row in action_rows:
        for component in action_row["components"]:
            # TODO: is there only ever one button per interaction?
            button_info = {
                "id": component["custom_id"].lower(),
                "label": component["label"]
            }
            
            buttons.append(button_info)
            
    return buttons
            
            
def parse_component_input(body):
    info = parse_basic_input(body)
    
    message = body["message"]
    
    action_rows = message["components"]
    
    info["base_interaction_msg"] = message["interaction"]["name"].lower()
    info["base_msg_id"] = message["id"]
    info["base_interaction_id"] = message["interaction"]["id"]
    info["buttons"] = parse_button_input(action_rows)
    
    return info


def parse_slash_command_input(body):
    data = body["data"]

    info = parse_basic_input(body)
    info["command"] = data["name"].lower()

    info["options"] = {}
    if "options" in data:
        for option in data.get("options"):
            option_key = option["name"]
            option_value = option["value"]
            info["options"][option_key] = option_value    
    
    return info
    
    
INPUT_PARSERS = {
    InteractionsType.APPLICATION_COMMAND: parse_slash_command_input, 
    InteractionsType.MESSAGE_COMPONENT: parse_component_input
}