import cmd
from constants import emojis
from utils import discord, dynamodb


EMOTE_MULE_SERVERS = ["1007089962228928594"]

EMOTES_TABLE = "lost_ark_emotes"
URL_PKEY = "url:{}"

NAME_COLUMN = "name"
ID_COLUMN = "id"
SERVER_COLUMN = "server"

EMOTE_REGEX = r"(.*)\\(<.*:\d*>)(.*)"
URL_REGEX = r"/(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])/igm"


def _create_emoji(emoji_name, emoji_image):
    # TODO: check if emoji already exists
    for server in EMOTE_MULE_SERVERS:
        resp = discord.create_emoji(server, emoji_name, emoji_image)
        print(resp.json())
        if resp.ok:
            return

    raise Exception("Emote creation failed")


def handle(command, cmd_input, channel_id):
    if command == "nitro_message":
        msg = cmd_input["message"]
        emote_names = cmd_input.get("emote_names")

    elif command == "nitro_react":
        msg = cmd_input["message_id"]
        image_url = cmd_input["image_url"]
        channel_id = channel_id
        emote_name = cmd_input.get("emote_name")
        _create_emoji(emote_name, image_url)
        discord.react_to_message(
            channel_id, msg, "<:mokoko_vibrate:984283879324147732>"
        )
    return "whee"
