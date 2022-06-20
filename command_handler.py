from handlers import roles, market
from utils import discord

ROLE_COMMANDS = ["add_roles", "remove_roles"]
MARKET_COMMANDS = ["price", "mari"]
HONING_COMMANDS = ["hone"]


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
        raise NotImplementedError('Zethorix')
    raise ValueError(f"Unrecognized command {command}, sad")


def lambda_handler(event, context):
    # get interaction metadata
    body = event["body-json"]
    server_id = body["guild_id"]
    channel_id = body["channel_id"]
    application_id = body["application_id"]
    interaction_token = body["token"]

    user_id = body["member"]["user"]["id"]
    command = body["data"]["name"]

    output = None

    try:
        output = handle_command(body)
    except NotImplementedError as nie:
        output = f"This function is not yet implemented. Contact the owner. ({nie})"
    except Exception as e:
        discord.delete_response(application_id, interaction_token)
        discord.send_followup(
            application_id, interaction_token, f"Error: {e}", ephemeral=True)
        raise e

    if not output:
        discord.delete_response(application_id, interaction_token)
    else:
        discord.update_response(application_id, interaction_token, output)
