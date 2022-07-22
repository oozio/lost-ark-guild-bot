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
    

class ComponentType(int, Enum):
    ACTION_ROW = 1
    BUTTON = 2
    SELECT = 3
    TEXT_INPUT = 4


def parse_basic_input(body):
    return {
        "channel_id": body["channel_id"],
        "server_id": body["guild_id"],
        "user_id": body["member"]["user"]["id"],
        "application_id": body["application_id"],
        "interaction_token": body["token"]
    }


def parse_button_input(data, action_rows):
    all_buttons = [component for row in action_rows for component in row["components"] if component["type"] == ComponentType.BUTTON]
    curr_id = data["custom_id"]
    curr_button = next((button for button in all_buttons if button["custom_id"] == curr_id), None)

    assert curr_button, f"Button `{curr_id}` not found in list of all buttons on original message"
    
    button_info = {
        "id": curr_id,
        "label": curr_button["label"]
    }
            
    return button_info


def parse_select_input(data, action_rows):
    selection_info = {
        "id": data["custom_id"],
        "values": data["values"]
    }
            
    return selection_info

            
def parse_component_input(body):
    info = parse_basic_input(body)
    
    message = body["message"]    
    info["base_interaction_msg"] = message["interaction"]["name"]
    info["base_msg_id"] = message["id"]
    info["base_interaction_id"] = message["interaction"]["id"]

    action_rows = message["components"]
    data = body["data"]

    info["data"] = COMPONENT_PARSERS[data["component_type"]](data, action_rows)

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
    

COMPONENT_PARSERS = {
    ComponentType.BUTTON: parse_button_input,
    ComponentType.SELECT: parse_select_input
}

INPUT_PARSERS = {
    InteractionsType.APPLICATION_COMMAND: parse_slash_command_input, 
    InteractionsType.MESSAGE_COMPONENT: parse_component_input
}