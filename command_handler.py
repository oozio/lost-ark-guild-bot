from handlers import (
    honing,
    market,
    report,
    render_display,
    role_selector,
    roles,
    scheduler,
    server_status,
)
from constants import interactions
from utils import discord


# TODO: move this entire section to /constants'
# text-only slash commands
ROLE_COMMANDS = ["add_roles", "remove_roles"]
MARKET_COMMANDS = ["price", "mari"]
HONING_COMMANDS = ["hone"]

# slash commands that generate UIs
BUTTON_COMMANDS = ["role_selector", "scheduler"]
SELECTOR_COMMANDS = ["make_raid"]

SERVER_STATUS_COMMANDS = ["server_status", "maintenance_watch"]

RENDER_VIEW_COMMANDS = set([*BUTTON_COMMANDS, *SELECTOR_COMMANDS])

# component interactions
COMPONENT_HANDLERS = {
    role_selector.is_role_button: role_selector.respond,
    scheduler.is_schedule_button: scheduler.handle_button,
    scheduler.is_schedule_selector: scheduler.handle_selector,
}


def handle_command(info):
    server_id = info["server_id"]
    user_id = info["user_id"]
    channel_id = info["channel_id"]

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
    elif command == "see_signups":
        return {"embeds": [scheduler.get_all_user_commitments(info)]}
    elif command == "report":
        return report.report(command, options, user_id)
    elif command in SERVER_STATUS_COMMANDS:
        return server_status.handle(command, user_id, channel_id)
    raise ValueError(f"Unrecognized command {command}, sad")


def handle_component_interaction(info):
    base_interaction = info["base_interaction_msg"]
    component_id = info["data"]["id"]

    handler = [
        func for is_match, func in COMPONENT_HANDLERS.items() if is_match(component_id)
    ]

    if handler:
        assert len(handler) == 1, f"Duplicate handler found for `{component_id}`"
        return handler[0](info)

    raise ValueError(
        f"Unrecognized component `{component_id}` from `/{base_interaction}`"
    )

def handle_event(event):
    resources = event["resources"]
    if "arn:aws:events:us-east-2:391107963258:rule/Timer" in resources:
        server_status.handle_timer()
    else:
        print(f"Unknown event(s): {resources}")


def lambda_handler(event, context):
    # Handle timer-triggered special cases
    if event.get("source") == "aws.events":
        handle_event(event)
        return

    # get interaction metadata
    body = event["body-json"]
    application_id = body["application_id"]
    interaction_type = body["type"]

    interaction_token = body["token"]

    output = None

    # Handling an request can either succeed or fail.
    #   If it succeeds, take any output that came from the handler and
    #           - if the request was a simple slash command, it'll have generated a loading
    #             message; when done, update that message.
    #               - if no output is necessary, delete the original message to reduce spam.
    #           - if the request was a component interaction, edit the body of the original
    #             message.
    #               - if no output is necessary, do nothing
    #
    #   If it failed,
    #           - for slash commands, delete the original message and show the error to the user
    #             who made the request.
    #           - for component interactions, keep the original message so that other people can
    #             still interact with it; show the error to the user who made the request.

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
        discord.send_followup(
            application_id, interaction_token, f"Error: {e}", ephemeral=True
        )
        raise e

    if not output:
        if interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
            discord.delete_response(application_id, interaction_token)
    else:
        if interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
            discord.update_response(application_id, interaction_token, output)
        elif interaction_type == interactions.InteractionsType.MESSAGE_COMPONENT:
            response = discord.edit_message(
                info["channel_id"], info["base_msg_id"], output
            )
            if response.status_code == 429:
                reset_time = response.json()["retry_after"]
                discord.send_followup(
                    application_id,
                    interaction_token,
                    f"A lot of people are clicking this button rn- try again in {reset_time} seconds",
                    ephemeral=True,
                )
        else:
            discord.post_message_in_channel(
                info["channel_id"],
                f"Don't know how to handle this interaction type: {interaction_type}",
                ephemeral=True,
            )
