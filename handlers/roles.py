import enum
import re

from utils import discord


def _pretty_role(role_id):
    return f"<@&{role_id}>"
    
def _pretty_roles(role_ids):
    return " ".join([_pretty_role(role_id) for role_id in role_ids])

def handle(command, cmd_input, user_id, server_id):
    # Returns a tuple of (output: str, hide_output: bool)
    if command == "add_role":
        roles_to_add = cmd_input["roles"]
        for role in roles_to_add:
            discord.add_role(user_id, role, server_id)
        
        output = f"Roles {_pretty_roles(roles_to_add)} have been added.\nAll current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user_id))}"

    elif command == "remove_role":
        roles_to_remove = cmd_input["roles"]
        for role in roles_to_remove:
            discord.add_role(user_id, role, server_id)
        output = f"Roles {_pretty_roles(roles_to_remove)} have been removed.\n All current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user_id))}"

    else:
        output = f"UNKNOWN COMMAND: {command}"


    return output