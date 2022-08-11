import base64
import hashlib
import io
import requests

from constants import emojis
from PIL import Image
from utils import discord, dynamodb


EMOTE_MULE_SERVERS = ["1007089962228928594"]

EMOTES_TABLE = "lost_ark_emotes"
URL_PKEY = "url:{}"

NAME_COLUMN = "name"
ID_COLUMN = "id"
SERVER_COLUMN = "server"

EMOTE_REGEX = r"(.*)\\(<.*:\d*>)(.*)"
URL_REGEX = r"/(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])/igm"


def _create_emoji(emoji_name, image_url):
    # TODO: check if emoji already exists
    r = requests.get(image_url).content
    dataBytesIO = io.BytesIO(r)
    img = Image.open(dataBytesIO)

    buffered = io.BytesIO()
    params = {"save_all": True, "disposal": 2} if img.format == "GIF" else {}
    img.save(buffered, format=img.format, **params, **img.info)
    img_str = base64.b64encode(buffered.getvalue()).decode()

    for server in EMOTE_MULE_SERVERS:
        resp = discord.create_emoji(server, emoji_name, img.format, img_str)
        if resp.ok:
            return resp.json()

    raise Exception("Emote creation failed")


def handle(command, cmd_input, channel_id):
    if command == "nitro_message":
        msg = cmd_input["message"]
        emote_names = cmd_input.get("emote_names")

    elif command == "nitro_react":
        msg = cmd_input["message_id"]
        image_url = cmd_input["image_url"]
        channel_id = channel_id
        emote_name = cmd_input.get(
            "emote_name", hashlib.md5(image_url.encode()).hexdigest()
        )
        emoji_info = _create_emoji(emote_name, image_url.replace("webp", "png"))

        r = discord.react_to_message(
            channel_id, msg, f"{emote_name}:{emoji_info['id']}"
        )

    elif command == "unreact":
        discord.unreact()

    else:
        raise ValueError(f"Don't know what to do with {command}")
    return "okie"
