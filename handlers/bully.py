import hashlib
import random
import re

from utils import discord, dynamodb

SPAM_CHANNEL = "951409442593865748"

TOXIC_INTERACTION_TABLE = "lost_ark_generic"

# reports
PAIR_PKEY = "reporter:{}victim:{}"
VICTIM_PKEY = "victim:{}"
REPORTER_PKEY = "reporter:{}"
TALLY_COLUMN = "tally"

# punch
PHRASES_PKEY = "phrases"
CHAR_PKEY = "user_stats:{}"
HEALTH_COLUMN = "hp"
DEATHS_COLUMN = "deaths"
KILLS_COLUMN = "kills"
CRIT_FAILS = "crit_fails"
MAX_HP = 10

# generic
EMOTE_REGEX = r"(.*)\\(<.*:\d*>)(.*)"
PUNCH_EMOTE = "<a:PUNCH:1010342592338202767>"


class CommandHandler:
    FIELDS = {}

    def __init__(self, command, **kwargs) -> None:
        # mandatory fields
        self.command = command

        # add fields from kwargs if in FIELDS
        for name_to_keep, name_to_look_for in self.FIELDS.items():
            self.__dict__[name_to_keep] = kwargs.get(name_to_look_for, "??")

    def _format_emotes(self, text: str) -> str:
        while re.match(EMOTE_REGEX, text, flags=re.IGNORECASE):
            text = re.sub(EMOTE_REGEX, r"\1\2\3", text)
        return text


class ReportHandler(CommandHandler):
    FIELDS = {"reporter": "user_id", "victim": "who", "reason": "why"}

    def _update_table(self):
        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE,
            PAIR_PKEY.format(self.reporter, self.victim),
            TALLY_COLUMN,
        )

        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE, REPORTER_PKEY.format(self.reporter), TALLY_COLUMN
        )

        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE, VICTIM_PKEY.format(self.victim), TALLY_COLUMN
        )

    def _get_victim_count(self):
        return dynamodb.get_rows(
            TOXIC_INTERACTION_TABLE, pkey_value=VICTIM_PKEY.format(self.victim)
        )[0][TALLY_COLUMN]

    def handle(self):
        reason_str = f" for: {self._format_emotes(self.reason)}" if self.reason else ""

        self._update_table()
        victim_count = self._get_victim_count()

        message = f"{discord.mention_user(self.reporter)} reported {discord.mention_user(self.victim)}{'.' if not reason_str else ''}{reason_str}\n{discord.mention_user(self.victim)} has been reported {victim_count} {'time' if victim_count == 1 else 'times'}."

        discord.post_message_in_channel(SPAM_CHANNEL, message)


class PunchHandler(CommandHandler):
    FIELDS = {"puncher": "user_id", "victim": "who", "channel_id": "channel_id"}

    def _update_hp(self, dmg):
        dynamodb.decrement_counter(
            TOXIC_INTERACTION_TABLE,
            CHAR_PKEY.format(self.victim),
            HEALTH_COLUMN,
            default_start=MAX_HP,
            decrement=int(dmg),
        )

    def _update_crit_fails(self):
        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE,
            CHAR_PKEY.format(self.puncher),
            CRIT_FAILS,
        )

    def _update_kda(self):
        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE,
            CHAR_PKEY.format(self.puncher),
            KILLS_COLUMN,
        )

        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE, CHAR_PKEY.format(self.victim), DEATHS_COLUMN
        )

        dynamodb.set_rows(
            TOXIC_INTERACTION_TABLE,
            CHAR_PKEY.format(self.victim),
            {HEALTH_COLUMN: MAX_HP},
        )

    def _get_victim_health(self):
        return dynamodb.get_rows(
            TOXIC_INTERACTION_TABLE, pkey_value=CHAR_PKEY.format(self.victim)
        )[0][HEALTH_COLUMN]

    def _get_victim_deaths(self):
        try:
            return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE, pkey_value=CHAR_PKEY.format(self.victim)
            )[0][DEATHS_COLUMN]
        except:
            return 0

    def _get_kill_count(self):
        try:
            return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE, pkey_value=CHAR_PKEY.format(self.puncher)
            )[0][KILLS_COLUMN]
        except:
            return 0

    def _get_crit_fails(self):
        try:
            return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE, pkey_value=CHAR_PKEY.format(self.puncher)
            )[0][CRIT_FAILS]
        except:
            return 0

    def _get_phrases(self):
        phrases = dynamodb.get_rows(TOXIC_INTERACTION_TABLE, pkey_value=PHRASES_PKEY)[0]

        phrases.pop("pk")
        return list(phrases.values())

    def handle(self):
        puncher_mention = discord.mention_user(self.puncher)
        victim_mention = discord.mention_user(self.victim)

        dmg = random.randrange(MAX_HP)
        self._update_hp(dmg)

        # format message
        phrase = random.choice(self._get_phrases())

        hp = self._get_victim_health()
        death_msg = ""

        if "knguyen" in puncher_mention:
            self._update_hp(10)
            hp = self._get_victim_health()
            dmg = 10000
            phrase = "teaches what a real joke is to"
            puncher_mention = "@REAL TWISTYFLOOF, GREEN=IMPOSTER"

        if hp <= 0:
            self._update_kda()

            death_count = self._get_victim_deaths()
            kill_count = self._get_kill_count()

            death_msg = f"""
            {victim_mention} has died {death_count} time{'s' if death_count != 1 else ''}.
            {puncher_mention} has killed someone {kill_count} time{'s' if kill_count != 1 else ''}."""

        if not dmg:
            self._update_crit_fails()
            crit_fails = self._get_crit_fails()

            message = f"""{puncher_mention} {phrase} {victim_mention} {PUNCH_EMOTE} for {dmg} damage.
            LOL
            {puncher_mention} has crit failed {crit_fails} time{'s' if crit_fails != 1 else ''}.
            """
        else:
            message = f"""{puncher_mention} {phrase} {victim_mention} {PUNCH_EMOTE} for {dmg} damage.
            {victim_mention} has {hp if hp > 0 else 0} HP left. 
            {death_msg}"""

        embedded_message = {
            "embeds": [
                {
                    "type": "rich",
                    "title": "Violence",
                    "description": message,
                }
            ]
        }

        discord.post_message_in_channel(self.channel_id, embedded_message)


class PhraseHandler(CommandHandler):
    FIELDS = {"phrase": "description"}

    def handle(self):
        phrase_hash = hashlib.md5(self.phrase.encode()).hexdigest()
        dynamodb.set_rows(
            TOXIC_INTERACTION_TABLE, PHRASES_PKEY, {f"hash_{phrase_hash}": self.phrase}
        )
        return f"'{self.phrase}' has been added to the wordbank."


handler_map = {
    "report": ReportHandler,
    "punch": PunchHandler,
    "add_punch_message": PhraseHandler,
}


def handle(command, info):
    handler = handler_map[command](**info, **info["options"])
    return handler.handle()
