import enum
import re

from utils import discord


def handle(command, cmd_input, user_id, server_id):
    if command == "add_roles":
        roles_to_add = cmd_input["roles"]
        for role in roles_to_add:
            discord.add_role(user_id, role["id"], server_id)
        
        return f"Roles {roles_to_add} have been added.\nAll current roles: {discord.get_user_roles(server_id, user_id)}"

    elif command == "remove_roles":
        roles_to_remove = cmd_input["roles"]
        for role in roles_to_remove:
            discord.add_role(user_id, role["id"], server_id)
        return f"Roles {roles_to_remove} have been removed.\n All current roles: {discord.get_user_roles(server_id, user_id)}"

    return f"UNKNOWN COMMAND: {command}"
