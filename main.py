from utils import discord
from handlers import roles

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
        return f"Code lives at https://github.com/oozio/lost-ark-guild-bot; feel free to add pull requests!!"


    elif "role" in command:
        return roles.handle(command, options, user_id, server_id)


    raise ValueError(f"Unrecognized command {command}, sad")
        

def lambda_handler(event, context):
    # get interaction metadata
    body = event["body-json"]
    channel_id = body["channel_id"]
    application_id = body["application_id"]
    interaction_token = body["token"]
    
    user_id = body["member"]["user"]["id"]
    command = body["data"]["name"]
    
    output = None

    try:
        output = handle_command(body)
    except Exception as e:
        discord.delete_response(application_id, interaction_token)
        discord.send_followup(application_id, interaction_token, f"Error: {e}", ephemeral=True)
#         discord_utils.send_response(channel_id, None, {"title": f"/{command}", "description": f"Error: {e}"}, ephemeral=True)
        raise e
  
    if not output:
        discord.delete_response(application_id, interaction_token)
    else:
        discord.update_response(application_id, interaction_token, output)
#         discord_utils.send_followup(application_id, interaction_token, output)
#         discord_utils.send_response(channel_id, f"<@{user_id}>", {"title": f"/{command}", "description": output})

   
