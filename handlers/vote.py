from time import sleep

from utils import discord, dynamodb
from views import vote_view

VOTES_TABLE = "lost_ark_generic"
PKEY = "vote:{}"

Q_COLUMN = "question"
CREATOR_COLUMN = "creator"

CHOICE_SEPARATOR = "|"
VOTE_PREFIX = "vote_"


def _is_vote_column(column_name: str) -> bool:
    return column_name.startswith(VOTE_PREFIX)


def _drop_vote_prefix(column_name: str) -> str:
    return column_name.replace(VOTE_PREFIX, "")


def _create_vote(interaction_id, creator, question, votes):
    dynamodb.set_rows(
        VOTES_TABLE,
        PKEY.format(interaction_id),
        {CREATOR_COLUMN: creator, Q_COLUMN: question, **votes},
    )

    sleep(2)


def _update_votes(interaction_id, choice):
    dynamodb.increment_counter(VOTES_TABLE, PKEY.format(interaction_id), choice)


def _get_votes(interaction_id):
    return dynamodb.get_rows(VOTES_TABLE, PKEY.format(interaction_id))


def _get_vote_embed(interaction_id, info):
    vote_info = _get_votes(interaction_id)

    question = vote_info.pop(Q_COLUMN, "? ur code is buggy")
    vote_fields = {}
    for key, value in vote_info:
        if _is_vote_column(key):
            vote_fields.append(
                {
                    "name": _drop_vote_prefix(key),
                    "value": value,
                    "inline": True,
                }
            )

    return {
        "type": "rich",
        "title": f"Vote on an important topic",
        "description": f"{question}",
        "color": 0x03045E,
        "fields": [*vote_fields],
    }


def display(info: dict) -> dict:
    cmd = info["command"]
    cmd_input = info["options"]

    if cmd == "vote":
        user_id = info["user_id"]
        interaction_id = info["interaction_id"]
        question = cmd_input["question"]
        choices = cmd_input["choices"].split("|")

        _create_vote(
            interaction_id, user_id, question, {choice: 0 for choice in choices}
        )

        return {
            "embeds": [_get_vote_embed(interaction_id, info)],
            "components": vote_view.VoteView(choices).components,
        }
    else:
        raise ValueError(f"Unrecognized command: {cmd}")


def is_vote_button(component_id):
    return _is_vote_column(component_id)


def handle_button(info):
    interaction_id = info["base_interaction_id"]
    base_channel_id = info["base_channel_id"]
    message_id = info["base_msg_id"]
    server_id = info["server_id"]
    user_id = info["user_id"]
    choice = info["data"]["id"]

    _update_votes(interaction_id, choice)

    new_msg = {"embeds": [_get_vote_embed(interaction_id, info)]}

    return new_msg
