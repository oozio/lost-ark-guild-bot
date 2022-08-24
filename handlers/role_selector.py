from constants.emojis import EmojiEnum
from constants.roles import RoleOperations, RoleTypes, ROLETYPE_COLORS
from views import button
from views.role_selector_view import RoleSelectorView
from utils import discord


class AddRmEmoji(EmojiEnum):
    ADD = "add", "1011832352365875230"
    RM = "remove", "1011832493097373786"


def _pretty_role(role_id):
    return f"<@&{role_id}>"


def _pretty_roles(role_ids):
    return " ".join([_pretty_role(role_id) for role_id in role_ids])


def is_role_button(component_id):
    return "role" in component_id


def display(info):
    # TODO: add logic for different types of roles
    role_selector = RoleSelectorView(info["server_id"])

    for role_operation in RoleOperations:
        emoji = (
            AddRmEmoji.ADD if role_operation == RoleOperations.ADD else AddRmEmoji.RM
        )

        thumbnail_url = (
            "https://cdn.discordapp.com/emojis/1011832352365875230.png"
            if role_operation == RoleOperations.ADD
            else "https://cdn.discordapp.com/emojis/1011832493097373786.png"
        )

        embed_msg = {
            "type": "rich",
            "title": f"{role_operation.capitalize()} Roles",
            "description": f"Click the button to {role_operation.lower()} the role!\n\nFor content-related roles, the corresponding channel should {'appear' if role_operation == RoleOperations.ADD else 'disappear'} in the left bar \n\nFor color roles, set a role to change the color of your name",
            "thumbnail": {"url": thumbnail_url, "height": 256, "width": 256},
        }

        buttons = []
        for role_type in RoleTypes:
            role_buttons = role_selector.get_buttons(
                role_type,
                role_operation,
                ROLETYPE_COLORS[role_type][role_operation],
                {"id": emoji.emoji_id, "name": emoji.emoji_name},
                max_per_row=4 if role_type == RoleTypes.COLOR else 5,
            )

            buttons = [*buttons, *role_buttons]

        output = {
            "embeds": [embed_msg],
            "components": buttons,
        }

        discord.post_message_in_channel(info["channel_id"], output)


def respond(info):
    data = info["data"]
    user = info["user_id"]
    server_id = info["server_id"]

    role_requested = data["id"].split("_role__")[-1]

    role_id = list(discord._get_role_ids_by_name(server_id, [role_requested]).values())[
        0
    ]

    output = "Something broke while trying to change roles. Let <@Bot Dev> know"
    if "___add_role__" in data["id"]:
        r = discord.add_role(user, role_id, server_id)

        if r.ok:
            output = f"{_pretty_role(role_id)} has been added! \nAll current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user))}"
        else:
            output = f"Adding role failed: let {discord.mention_user('143257008706027521')} know.\n{r.status_code}- {r.text}"

    elif "___rm_role__" in data["id"]:
        r = discord.remove_role(user, role_id, server_id)

        if r.ok:
            output = f"{_pretty_role(role_id)} has been removed! \nAll current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user))}"
        else:
            output = f"Removing role failed: let {discord.mention_user('143257008706027521')} know.\n{r.status_code}- {r.text}"

    discord.send_followup(
        info["application_id"], info["interaction_token"], output, ephemeral=True
    )
