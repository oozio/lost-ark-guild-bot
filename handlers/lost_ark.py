import enum
import re

from utils import discord



def handle(command, cmd_input, discord_user):
    if command == 'roles':
        print(command)
        print(cmd_input)
        print(discord_user)
        mal_username = cmd_input.get('mal_name')
        return 'a'
    return f"UNKNOWN COMMAND: {command}"
