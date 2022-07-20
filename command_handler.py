from handlers import honing, market, render_display, role_selector, roles, scheduler
from constants import interactions
from utils import discord

# TODO: move this section to /constants
ROLE_COMMANDS = ["add_roles", "remove_roles"]
MARKET_COMMANDS = ["price", "mari"]
HONING_COMMANDS = ["hone"]
BUTTON_COMMANDS = ["role_selector", "scheduler"]

# TODO: pull roles from api instead
ROLE_BUTTONS = ["vykas"]
SCHEDULING_BUTTONS = ["toggle_event_interest"]

def handle_command(info):
    channel_id = info["channel_id"]
    server_id = info["server_id"]
    user_id = info["user_id"]
    role_ids = info["role_ids"]

    command = info["command"]
    options = info["options"]
    if command == "git":
        return f"Code lives at https://github.com/oozio/lost-ark-guild-bot; feel free to contribute!!"
    elif command in ROLE_COMMANDS:
        return roles.handle(command, options, user_id, server_id)
    elif command in MARKET_COMMANDS:
        return market.handle(command, options)
    elif command in HONING_COMMANDS:
        return honing.handle(command, options)
    elif command in BUTTON_COMMANDS:
        return render_display.display(command)(info)
    raise ValueError(f"Unrecognized command {command}, sad")
        

def handle_component_interaction(info):
    base_interaction = info["base_interaction_msg"]
    if base_interaction in BUTTON_COMMANDS:
        # TODO: is each interaction at most one button?
        for button in info["buttons"]:
            button_id = button["id"]
            button_label = button["label"]
            if button_id in SCHEDULING_BUTTONS:
                return scheduler.handle(info)
            elif button_id in ROLE_BUTTONS: 
                return role_selector.respond(info)
            raise ValueError(f"Unrecognized button: `{button_label}` with ID `{button_id}`")
    
    raise ValueError(f"No followup interactions defined for {base_interaction}")
    
def lambda_handler(event, context):
    # get interaction metadata
    body = event["body-json"]
    application_id = body["application_id"]
    interaction_type = body["type"]

    interaction_id = body["id"]
    interaction_token = body["token"]

    output = None

    try:
        info = interactions.INPUT_PARSERS[interaction_type](body)   

        if interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
            output = handle_command(info)
        elif interaction_type == interactions.InteractionsType.MESSAGE_COMPONENT:
            output = handle_component_interaction(info)
 
    except NotImplementedError as nie:
        output = f"This function is not yet implemented. Contact the owner. ({nie})"
    except Exception as e:
        discord.delete_response(application_id, interaction_token)
        discord.send_followup(application_id,
                              interaction_token,
                              f"Error: {e}",
                              ephemeral=True)
        raise e

    if not output:
        discord.delete_response(application_id, interaction_token)
    else:
        if interaction_type == interactions.InteractionsType.MESSAGE_COMPONENT:
            discord.edit_message(info["channel_id"], info["base_msg_id"],
                                            output)
        else:
            discord.update_response(application_id, interaction_token, output)
