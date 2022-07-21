from handlers import honing, market, render_display, role_selector, roles, scheduler
from constants import interactions
from utils import discord

# TODO: move this entire section to /constants'
# text-only slash commands
ROLE_COMMANDS = ["add_roles", "remove_roles"]
MARKET_COMMANDS = ["price", "mari"]
HONING_COMMANDS = ["hone"]

# slash commands that generate UIs
BUTTON_COMMANDS = ["role_selector", "scheduler"]
SELECTOR_COMMANDS = ["scheduler"]

RENDER_VIEW_COMMANDS = set([*BUTTON_COMMANDS, *SELECTOR_COMMANDS])

# component interactions 
# TODO: pull roles from api instead
COMPONENT_HANDLERS = {
    frozenset(("vykas", )): role_selector.respond,
    frozenset(("COMING", "NOT_COMING", "MAYBE")): scheduler.handle_button,
    frozenset(("class_selector", )): scheduler.handle_selector
}

def handle_command(info):
    server_id = info["server_id"]
    user_id = info["user_id"]

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
    elif command in RENDER_VIEW_COMMANDS:
        return render_display.display(command)(info)
    raise ValueError(f"Unrecognized command {command}, sad")
        

def handle_component_interaction(info):
    base_interaction = info["base_interaction_msg"]
    component_id = info["data"]["id"]

    handler = [f for k, f in COMPONENT_HANDLERS.items() if component_id in k]

    if handler:
        assert len(handler)==1, f"Duplicate handler found for `{component_id}`"
        print(handler)
        return handler[0](info)
        
    raise ValueError(f"Unrecognized component `{component_id}` from `/{base_interaction}`")
    

def lambda_handler(event, context):
    # get interaction metadata
    body = event["body-json"]
    application_id = body["application_id"]
    interaction_type = body["type"]

    interaction_token = body["token"]

    output = None

    # Handling an request can either succeed or fail.
    #   If it succeeds, take any output that came from the handler and 
    #           - if the request was a simple slash command, it'll have generated a loading message; when done, update
    #             that message.
    #           - if the request was a component interaction, edit the body of the original message.
    #           - if no output is necessary, delete the original message to reduce spam. 
    #   
    #   If it failed, 
    #           - for slash commands, delete the original message and show the error to the user who made the request.
    #           - for component interactions, keep the original message so that other people can still interact with 
    #             it; show the error to the user who made the request.

    try:
        info = interactions.INPUT_PARSERS[interaction_type](body)   
    
        if interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
            output = handle_command(info)
        elif interaction_type == interactions.InteractionsType.MESSAGE_COMPONENT:
            output = handle_component_interaction(info)
    except NotImplementedError as nie:
        output = f"This function is not yet implemented. Contact the owner. Any volunteers? ({nie})"
    except Exception as e:
        # only delete the original message if a slash command failed
        if interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
            discord.delete_response(application_id, interaction_token)
        discord.send_followup(application_id,
                              interaction_token,
                              f"Error: {e}",
                              ephemeral=True)
        raise e


    print(f"output: {output}")

    if not output:
        discord.delete_response(application_id, interaction_token)
    else:
        if interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
            discord.update_response(application_id, interaction_token, output)
        elif interaction_type == interactions.InteractionsType.MESSAGE_COMPONENT:
            discord.edit_message(info["channel_id"], info["base_msg_id"],
                                            output)
        else:
            discord.post_message_in_channel(info["channel_id"], f"Don't know how to handle this interaction type: {interaction_type}", ephemeral=True)
