import boto3
import re
import requests

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

PING_PONG = {"type": 1}

MAX_RESPONSE_LENGTH = 2000

RESPONSE_TYPES =  {
                    "PONG": 1,
                    "ACK_NO_SOURCE": 2,
                    "MESSAGE_NO_SOURCE": 3,
                    "MESSAGE_WITH_SOURCE": 4,
                    "ACK_WITH_SOURCE": 5
                  }

BASE_URL = "https://discord.com/api/v9"

ssm = boto3.client('ssm', region_name='us-east-2')

PUBLIC_KEY = ssm.get_parameter(Name="/discord/public_key/lost-ark-guild-bot", WithDecryption=True)['Parameter']['Value']
BOT_TOKEN = ssm.get_parameter(Name="/discord/bot_token/lost-ark-guild-bot", WithDecryption=True)['Parameter']['Value']
HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

SIZE_ROLE_NAME_PATTERN = re.compile(r'Size (?P<size>\d+)')

_PERMISSIONS = {
    "VIEW_AND_USE_SLASH_COMMANDS": 0x0080000400,
    "ADD_REACTIONS": 0x0000000040,
    "USE_EXTERNAL_EMOJIS": 0x0000040000,
    "SEND_MESSAGES": 0x0000000800
}

# Verification related

def _verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')
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
    body = event.get('body-json')
    if _ping_pong(body):
        return PING_PONG


def get_input(data, target):
    for option in data.get('options', []):
        if option['name'] == target:
            return option['value']



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
    return [role for role in roles if role['id'] in role_ids]


def get_roles_by_names(server_id, role_names):
    roles = _get_all_roles(server_id)
    return [role for role in roles if role['name'] in role_names]


def _get_role_ids_by_name(server_id, role_names):
    results = {key: None for key in role_names}
    for role in _get_all_roles(server_id):
        if role['name'] in role_names:
            results[ role['name'] ] = role['id']
        if None not in results.values():
            return results


def _get_role_names_by_id(server_id, role_ids):
    results = {key: None for key in role_ids}
    for role in _get_all_roles(server_id):
        if role['id'] in role_ids:
            results[ role['id'] ] = role['name']
        if None not in results.values():
            return results


def remove_role(user_id, role_id, server_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    requests.delete(url, headers=HEADERS)


def add_role(user_id, role_id, server_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    requests.put(url, headers=HEADERS)


def get_user_role_ids(server_id, user_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url,  headers=HEADERS).json()
    return user['roles']


def get_user_role_names(server_id, user_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url,  headers=HEADERS).json()
    return get_roles_by_ids(server_id, user['roles'])


def get_all_users(server_id):
    # return all user_ids in a server
    url = f"{BASE_URL}/guilds/{server_id}/members?limit=1000"
    response = requests.get(url,  headers=HEADERS)
    return response.json()


def change_role(server_id, user_id, old_role_name, new_role_name):
    role_ids_by_name = _get_role_ids_by_name(server_id, [new_role_name, old_role_name])
    remove_role(user_id, role_ids_by_name[old_role_name], server_id)
    add_role(user_id, role_ids_by_name[new_role_name], server_id)


def get_user_nickname_by_id(server_id, user_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    user = requests.get(url,  headers=HEADERS).json()
    return user["nick"]


# Message related

def post_message_in_channel(channel_id, content, ephemeral=True):
    url = f'{BASE_URL}/channels/{channel_id}/messages'
    body = {'content': content, "flags": 64}
    requests.post(url, json=body, headers=HEADERS)


def get_messages(channel_id, limit, specified_message):
    # gets the last <limit> messages from the specified channel, and appends any message specified by id
    # doesn't check if <specified_message> is duplicated
    url = f"https://discord.com/api/v8/channels/{channel_id}/messages?limit={limit}"
    ind_url = f"https://discord.com/api/v8/channels/{channel_id}/messages/{specified_message}"
    messages = requests.get(url, headers=HEADERS).json()
    if specified_message:
        messages.append(requests.get(ind_url, headers=HEADERS).json())

    return messages


def format_response(body, ephemeral):
    if isinstance(body, str):
        response = {
            "content": body,
            "flags": 64 if ephemeral else 128
        }
    else:        
        content = body.get('content')
        embed = body.get('embed')
        response = {
                "content": content,
                "embeds": [embed],
                "allowed_mentions": [],
                "flags": 64 if ephemeral else None
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
    remaining = ''
    # TODO FIX FOR DICT CONTENT
    if len(content) > MAX_RESPONSE_LENGTH:
        content, remaining = content[:MAX_RESPONSE_LENGTH], content[MAX_RESPONSE_LENGTH:]

    body = format_response(content, ephemeral=ephemeral)
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    requests.patch(url, json=body, headers=HEADERS)

    if remaining:
        send_followup(application_id, interaction_token, remaining)


def delete_response(application_id, interaction_token):
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    requests.delete(url, headers=HEADERS)


def send_response(channel_id, content, embed=None, ephemeral=False):
    body = format_response({"content": content, "embed": embed}, ephemeral=ephemeral)
    url = f"{BASE_URL}/channels/{channel_id}/messages"
    response = requests.post(url, json=body, headers=HEADERS)
    
    return response


def edit_message(channel_id, message_id, content, embed={}):
    response = {
        "content": content
    }
    if embed:
        response['embed'] = {
            "title": f"{embed.get('title')}",
            "description": f"{embed.get('description')}"
         }
    url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}"
    response = requests.patch(url, json=response, headers=HEADERS)



# Misc

def initial_response(response_type, content=None, ephemeral=False):
    response = {
        "type": RESPONSE_TYPES[response_type] if response_type in RESPONSE_TYPES else RESPONSE_TYPES['MESSAGE_WITH_SOURCE'],
        }
    if response_type != 'PONG':# and "ACK" not in response_type:
        response["data"] = {
            "content": content,
            "embeds": [],
            "allowed_mentions": [],
            "flags": 64 if ephemeral else None
            }
    return response


def _form_permission():
    result = 0
    for permission in _PERMISSIONS.values():
        result = result | permission
    return result
