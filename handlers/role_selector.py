from constants.roles import RoleTypes
from views.role_selector_view import RoleSelectorView
from utils import discord


def _pretty_role(role_id):
    return f"<@&{role_id}>"


def _pretty_roles(role_ids):
    return " ".join([_pretty_role(role_id) for role_id in role_ids])


def is_role_button(component_id):
    return "role" in component_id


def display(info):
    # TODO: add logic for different types of roles
    role_selector = RoleSelectorView(info["server_id"])
    output = {
        "content": "Which content channels do you want to see?",
        "components": role_selector.get_buttons(RoleTypes.RAID)
    }

    return output

def respond(info):
    data = info["data"]
    user = info["user_id"]
    server_id = info["server_id"]
    
    role_requested = data["id"].split("_role__")[-1]

    role_id = list(discord._get_role_ids_by_name(server_id, [role_requested]).values())[0]
    
    output = "Something broke while trying to change roles. Let <@Bot Dev> know"
    if "___add_role__" in data["id"]:
        discord.add_role(user, role_id, server_id) 

        output = f"{_pretty_role(role_id)} has been added! \nAll current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user))}"
    elif "___rm_role__" in data["id"]:
        discord.remove_role(user, role_id, server_id)

        output = f"{_pretty_role(role_id)} has been removed! \nAll current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user))}"

    discord.send_followup(info["application_id"], info["interaction_token"], output, ephemeral=True)   
