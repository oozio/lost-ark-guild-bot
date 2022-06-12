import enum
import re

from utils import discord, steam

def handle(command, cmd_input, discord_user):
    if command == 'addsteam':
        steam_username = cmd_input.get('steam_name')
        return steam.set_steam_user(discord_user, steam_username)
    if command == 'steam': 
        steam_username = cmd_input.get('steam_name')
        # if not username:
        steam_username = steam.map_user(discord_user)
            # return f"not implemented yet quq"
        result = steam.get_steam_user(steam_username)
        return result
    return f"UNKNOWN COMMAND: {command}"
