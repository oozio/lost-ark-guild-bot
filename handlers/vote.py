from cProfile import label
import re

from time import sleep

from utils import discord, dynamodb
from views import vote_view

VOTES_TABLE = "lost_ark_generic"
PKEY = "vote:{}"

Q_COLUMN = "question"
CREATOR_COLUMN = "creator"
LABEL_MAP_COLUMN = "map"

CHOICE_SEPARATOR = "|"
VOTE_PREFIX = "vote_"


def _sanitize(input: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", input)


def _is_vote_column(column_name: str) -> bool:
    return column_name.startswith(VOTE_PREFIX)


def _drop_vote_prefix(column_name: str) -> str:
    return column_name.replace(VOTE_PREFIX, "")


def _create_vote(interaction_id, creator, question, votes, choice_label_map):
    dynamodb.set_rows(
        VOTES_TABLE,
        PKEY.format(interaction_id),
        {
            CREATOR_COLUMN: creator,
            Q_COLUMN: question,
            LABEL_MAP_COLUMN: choice_label_map,
            **votes,
        },
    )

    sleep(2)


def _update_votes(interaction_id, choice):
    dynamodb.increment_counter(VOTES_TABLE, PKEY.format(interaction_id), choice)


def _get_votes(interaction_id):
    return dynamodb.get_rows(VOTES_TABLE, PKEY.format(interaction_id))[0]


def _get_vote_embed(interaction_id):
    vote_info = _get_votes(interaction_id)

    question = vote_info.pop(Q_COLUMN, "? ur code is buggy")
    label_map = vote_info.pop(LABEL_MAP_COLUMN, {})
    vote_fields = []

    for key, value in vote_info.items():
        if _is_vote_column(key):
            pretty_label = label_map.get(key)
            vote_fields.append(
                {
                    "name": pretty_label,
                    "value": int(value),
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

        sanitized_choices = []
        choice_label_map = {}
        for choice in choices:
            sanitized_choice = f"{VOTE_PREFIX}{_sanitize(choice)}"
            sanitized_choices.append(sanitized_choice)
            choice_label_map[sanitized_choice] = choice

        _create_vote(
            interaction_id,
            user_id,
            question,
            {choice: 0 for choice in sanitized_choices},
            choice_label_map,
        )

        return {
            "embeds": [_get_vote_embed(interaction_id)],
            "components": vote_view.VoteView(choices).get_buttons(),
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
    choice = _drop_vote_prefix(info["data"]["id"])

    vote_info = _get_votes(interaction_id)

    label_map = vote_info.pop(LABEL_MAP_COLUMN, {})
    for sanitized, pretty in label_map.items():
        if pretty == choice:
            _update_votes(interaction_id, sanitized)

    new_msg = {"embeds": [_get_vote_embed(interaction_id)]}

    return new_msg
