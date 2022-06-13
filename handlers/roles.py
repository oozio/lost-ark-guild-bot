from utils import discord


def _pretty_role(role_id):
    return f"<@&{role_id}>"
    
def _pretty_roles(role_ids):
    return " ".join([_pretty_role(role_id) for role_id in role_ids])

def handle(command, cmd_input, user_id, server_id):
    if command == "add_roles":
        roles_seen = []
        for _, role in cmd_input.items():
            if role not in roles_seen:
                discord.add_role(user_id, role, server_id)
                roles_seen.append(role)

        return f"Roles {_pretty_roles(roles_seen)} have been added.\nAll current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user_id))}"

    elif command == "remove_roles":
        roles_seen = []
        for _, role in cmd_input.items():
            if role not in roles_seen:
                discord.remove_role(user_id, role, server_id)
                roles_seen.append(role)
                
        return f"Roles {_pretty_roles(cmd_input.values())} have been removed.\n All current roles: {_pretty_roles(discord.get_user_role_ids(server_id, user_id))}"

    else:
        return f"UNKNOWN COMMAND: {command}"