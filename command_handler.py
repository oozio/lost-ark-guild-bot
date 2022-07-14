from handlers import honing, market, role_selector, roles
from constants import interactions
from utils import discord

ROLE_COMMANDS = ["add_roles", "remove_roles"]
MARKET_COMMANDS = ["price", "mari"]
HONING_COMMANDS = ["hone"]
BUTTON_COMMANDS = ["role_buttons"]

def handle_command(body):
    # dummy return
    channel_id = body["channel_id"]
    server_id = body["guild_id"]
    user_id = body["member"]["user"]["id"]
    role_ids = body["member"]["roles"]

    data = body["data"]
    command = data["name"].lower()

    options = {}
    if "options" in data:
        for option in data.get("options"):
            option_key = option["name"]
            option_value = option["value"]
            options[option_key] = option_value

    if command == "git":
        return f"Code lives at https://github.com/oozio/lost-ark-guild-bot; feel free to contribute!!"
    elif command in ROLE_COMMANDS:
        return roles.handle(command, options, user_id, server_id)
    elif command in MARKET_COMMANDS:
        return market.handle(command, options)
    elif command in HONING_COMMANDS:
        return honing.handle(command, options)
    elif command in BUTTON_COMMANDS:
        return role_selector.display()
    raise ValueError(f"Unrecognized command {command}, sad")

def handle_component_interaction(body):
    #Handles user interactions with buttons 
    #(for right now, currently only have 1 button for role selector)
    data = body["data"]
    return role_selector.respond(data)

def lambda_handler(event, context):
    # get interaction metadata
    body = event["body-json"]
    interaction_id = body["id"]
    type = body["type"]
    application_id = body["application_id"]
    interaction_token = body["token"]

    output = None


    try:
        if type == interactions.InteractionsType.MESSAGE_COMPONENT:
            output = handle_component_interaction(body)
        else:
            output = handle_command(body)
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
        if type == interactions.InteractionsType.MESSAGE_COMPONENT:
            discord.send_component_response(interaction_id, interaction_token,
                                            output)
        else:
            discord.update_response(application_id, interaction_token, output)
