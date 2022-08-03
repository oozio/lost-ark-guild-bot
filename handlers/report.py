import re
from utils import discord, dynamodb

SPAM_CHANNEL = "951409442593865748"

REPORT_TABLE = "lost_ark_generic"
PAIR_PKEY = "reporter:{}victim:{}"
VICTIM_PKEY = "victim:{}"
REPORTER_PKEY = "reporter:{}"

TALLY_COLUMN = "tally"

EMOTE_REGEX = r"(.*)\\(<.*:\d*>)(.*)"


def _update_table(reporter, victim):
    dynamodb.increment_counter(
        REPORT_TABLE, PAIR_PKEY.format(reporter, victim), TALLY_COLUMN
    )

    dynamodb.increment_counter(
        REPORT_TABLE, REPORTER_PKEY.format(reporter), TALLY_COLUMN
    )

    dynamodb.increment_counter(REPORT_TABLE, VICTIM_PKEY.format(victim), TALLY_COLUMN)


def _get_victim_count(victim):
    return dynamodb.get_rows(REPORT_TABLE, pkey_value=VICTIM_PKEY.format(victim))[0][
        TALLY_COLUMN
    ]


def _format_emotes(text: str) -> str:
    while re.match(EMOTE_REGEX, text, flags=re.IGNORECASE):
        text = re.sub(EMOTE_REGEX, r"\1\2\3", text)
    return text


def report(command, cmd_input, user_id):
    victim = cmd_input["who"]
    reason = cmd_input.get("why", "")
    reason_str = f" for: {_format_emotes(reason)}" if reason else ""

    _update_table(user_id, victim)
    victim_count = _get_victim_count(victim)

    message = f"{discord.mention_user(user_id)} reported {discord.mention_user(victim)}{'.' if not reason_str else ''}{reason_str}\n{discord.mention_user(victim)} has been reported {victim_count} {'time' if victim_count == 1 else 'times'}."

    discord.post_message_in_channel(SPAM_CHANNEL, message)
