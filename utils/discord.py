import boto3
import re
import requests

from functools import lru_cache
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from constants.interactions import InteractionsCallbackType

PING_PONG = {"type": 1}

MAX_RESPONSE_LENGTH = 2000

RESPONSE_TYPES = {
    "PONG": 1,
    "ACK_NO_SOURCE": 2,
    "MESSAGE_NO_SOURCE": 3,
    "MESSAGE_WITH_SOURCE": 4,
    "ACK_WITH_SOURCE": 5,
    "DEFERRED_UPDATE_MESSAGE": 6,
    "MODAL": 9,
}


BASE_URL = "https://discord.com/api/v9"

ssm = boto3.client("ssm", region_name="us-east-2")

PUBLIC_KEY = ssm.get_parameter(
    Name="/discord/public_key/lost-ark-guild-bot", WithDecryption=True
)["Parameter"]["Value"]
BOT_TOKEN = ssm.get_parameter(
    Name="/discord/bot_token/lost-ark-guild-bot", WithDecryption=True
)["Parameter"]["Value"]
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

SIZE_ROLE_NAME_PATTERN = re.compile(r"Size (?P<size>\d+)")

_PERMISSIONS = {
    "VIEW_AND_USE_SLASH_COMMANDS": 0x0080000400,
    "ADD_REACTIONS": 0x0000000040,
    "USE_EXTERNAL_EMOJIS": 0x0000040000,
    "SEND_MESSAGES": 0x0000000800,
}

# Verification related


def _verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event["params"]["header"].get("x-signature-ed25519")
    auth_ts = event["params"]["header"].get("x-signature-timestamp")
    message = auth_ts.encode() + raw_body.encode()

    try:
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        verify_key.verify(message, bytes.fromhex(auth_sig))
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")


def _ping_pong(body):
    if body.get("type") == 1:
        return True
    return False


def check_input(event):
    _verify_signature(event)
    body = event.get("body-json")
    if _ping_pong(body):
        return PING_PONG


def get_input(data, target):
    for option in data.get("options", []):
        if option["name"] == target:
            return option["value"]


# Channel-related
@lru_cache(maxsize=128)
def get_channel_by_id(channel_id):
    """Returns a channel object.

    returns channel object (dict).
    Params found at https://discord.com/developers/docs/resources/channel
    """
    url = f"{BASE_URL}/channels/{channel_id}"
    return requests.get(url, headers=HEADERS).json()


def create_thread(
    channel_id: str, thread_name: str, message_id=None, duration=1 * 24 * 60
) -> dict:
    if not message_id:
        url = f"{BASE_URL}/channels/{channel_id}/threads"
    else:
        url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}/threads"
    return requests.post(
        url,
        json={"name": thread_name, "auto_archive_duration": duration},
        headers=HEADERS,
    ).json()


def get_thread_members(channel_id):
    url = f"{BASE_URL}/channels/{channel_id}/thread-members"
    return requests.get(url, headers=HEADERS).json()


def add_thread_member(thread_id, user_id):
    url = f"{BASE_URL}/channels/{thread_id}/thread-members/{user_id}"
    return requests.put(url, headers=HEADERS).text


def remove_thread_member(thread_id, user_id):
    url = f"{BASE_URL}/channels/{thread_id}/thread-members/{user_id}"
    return requests.delete(url, headers=HEADERS).text


# Role-related
_ROLES_CACHE = {}


def _get_all_roles(server_id, force_refresh=False):
    if server_id in _ROLES_CACHE and not force_refresh:
        return _ROLES_CACHE[server_id]
    url = f"{BASE_URL}/guilds/{server_id}/roles"
    roles = requests.get(url, headers=HEADERS).json()
    _ROLES_CACHE[server_id] = roles
    return roles


def get_roles_by_ids(server_id, role_ids):
    roles = _get_all_roles(server_id)
    return [role for role in roles if role["id"] in role_ids]


def get_roles_by_names(server_id, role_names):
    roles = _get_all_roles(server_id)
    return [role for role in roles if role["name"] in role_names]


def _get_role_ids_by_name(server_id, role_names):
    results = {key: None for key in role_names}
    for role in _get_all_roles(server_id):
        if role["name"] in role_names:
            results[role["name"]] = role["id"]
        if None not in results.values():
            return results


def _get_role_names_by_id(server_id, role_ids):
    results = {key: None for key in role_ids}
    for role in _get_all_roles(server_id):
        if role["id"] in role_ids:
            results[role["id"]] = role["name"]
        if None not in results.values():
            return results


def remove_role(user_id, role_id, server_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    return requests.delete(url, headers=HEADERS)


def add_role(user_id, role_id, server_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    return requests.put(url, headers=HEADERS)


def get_user_role_ids(server_id, user_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url, headers=HEADERS).json()
    return user["roles"]


def get_user_role_names(server_id, user_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url, headers=HEADERS).json()
    return get_roles_by_ids(server_id, user["roles"])


def get_all_users(server_id):
    # return all user_ids in a server
    url = f"{BASE_URL}/guilds/{server_id}/members?limit=1000"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def mention_user(user_id):
    return f"<@{user_id}>"


def change_role(server_id, user_id, old_role_name, new_role_name):
    role_ids_by_name = _get_role_ids_by_name(server_id, [new_role_name, old_role_name])
    remove_role(user_id, role_ids_by_name[old_role_name], server_id)
    add_role(user_id, role_ids_by_name[new_role_name], server_id)


def get_user_nickname_by_id(server_id, user_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url, headers=HEADERS).json()
    if user["nick"]:
        return user["nick"]
    else:
        return user["user"]["username"]


def is_admin(server_id, user_id, admin_role_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url, headers=HEADERS).json()
    return admin_role_id in user["roles"]


# Message related
def post_message_in_channel(channel_id, message, ephemeral=True):
    url = f"{BASE_URL}/channels/{channel_id}/messages"
    body = format_response(message, ephemeral)
    r = requests.post(url, json=body, headers=HEADERS)


def delete_message(channel_id, message_id):
    url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}"
    requests.delete(url, headers=HEADERS)


def get_messages(channel_id, limit, specified_message):
    # gets the last <limit> messages from the specified channel
    url = f"https://discord.com/api/v8/channels/{channel_id}/messages?limit={limit}"
    return requests.get(url, headers=HEADERS).json()


def get_message_by_id(channel_id, message_id):
    url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}"

    return requests.get(url, headers=HEADERS).json()


def get_interaction_message_id(application_id: str, interaction_token: str) -> str:
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    return requests.get(url, headers=HEADERS).json()


def format_response(body, ephemeral):
    if isinstance(body, str):
        response = {"content": body, "flags": 64 if ephemeral else 128}
    else:
        content = body.get("content")
        embeds = body.get("embeds")
        components = body.get("components")
        response = {
            "content": content,
            "embeds": embeds,
            "allowed_mentions": [],
            "flags": 64 if ephemeral else None,
            "components": components,
        }

    return response


def send_followup(application_id, interaction_token, content, ephemeral=False):
    while len(content) > MAX_RESPONSE_LENGTH:
        send_followup(application_id, interaction_token, content[:MAX_RESPONSE_LENGTH])
        content = content[MAX_RESPONSE_LENGTH:]

    body = format_response(content, ephemeral=ephemeral)
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}"
    requests.post(url, json=body, headers=HEADERS)


def update_response(application_id, interaction_token, content, ephemeral=False):
    remaining = ""
    # TODO FIX FOR DICT CONTENT
    if len(content) > MAX_RESPONSE_LENGTH:
        content, remaining = (
            content[:MAX_RESPONSE_LENGTH],
            content[MAX_RESPONSE_LENGTH:],
        )

    body = format_response(content, ephemeral=ephemeral)
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    requests.patch(url, json=body, headers=HEADERS)

    if remaining:
        send_followup(application_id, interaction_token, remaining)


def delete_response(application_id, interaction_token):
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    requests.delete(url, headers=HEADERS)


def send_response(channel_id, content, embeds=None, ephemeral=False):
    if embeds is None:
        embeds = []
    body = format_response({"content": content, "embeds": embeds}, ephemeral=ephemeral)
    url = f"{BASE_URL}/channels/{channel_id}/messages"
    response = requests.post(url, json=body, headers=HEADERS)

    return response


def edit_message(channel_id, message_id, output):
    response = format_response(output, ephemeral=False)
    url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}"
    response = requests.patch(url, json=response, headers=HEADERS)

    return response


# Component related
def send_component_response(interaction_id, interaction_token, content=None):
    if content is None:
        body = initial_response(InteractionsCallbackType.PONG)
    else:
        body = {"type": InteractionsCallbackType.CHANNEL_MESSAGE_WITH_SOURCE}
        body["data"] = content
    url = f"{BASE_URL}/interactions/{interaction_id}/{interaction_token}/callback"
    requests.post(url, json=body, headers=HEADERS)


# Event related
def create_server_event(server_id: str, event_details: dict) -> None:
    url = f"{BASE_URL}/guilds/{server_id}/scheduled-events"
    return requests.post(url, json=event_details, headers=HEADERS)


# Emote related
def create_emoji(server_id, emoji_name, image_format, image_data):
    emoji = {
        "name": emoji_name,
        "image": f"data:image/{image_format};base64,{image_data}",
        "roles": [],
    }

    url = f"{BASE_URL}/guilds/{server_id}/emojis"
    return requests.post(url, json=emoji, headers=HEADERS)


def react_to_message(channel_id, message_id, emoji):
    url = (
        f"{BASE_URL}/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
    )
    return requests.put(url, headers=HEADERS)


def delete_self_react(channel_id, message_id, emoji):
    url = (
        f"{BASE_URL}/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
    )

    return requests.delete(url, headers=HEADERS)


# Misc
def initial_response(response_type, content=None, ephemeral=False):
    response = {
        "type": RESPONSE_TYPES[response_type]
        if response_type in RESPONSE_TYPES
        else RESPONSE_TYPES["MESSAGE_WITH_SOURCE"],
    }
    if response_type != "PONG":  # and "ACK" not in response_type:
        response["data"] = {
            "content": content,
            "embeds": [],
            "allowed_mentions": [],
            "flags": 64 if ephemeral else None,
        }
    return response


def _form_permission():
    result = 0
    for permission in _PERMISSIONS.values():
        result = result | permission
    return result
