from enum import Enum
import random

from handlers.bully import CommandHandler

from utils import discord, dynamodb
from views import compliment_view
TOXIC_INTERACTION_TABLE = "lost_ark_generic"

#
PK = "word:{word}_pps:{pps}_id:{id}"
WORD_COLUMN = "word" 
PART_COLUMN = "part_of_speech"
ID_COLUMN = "word_id"


class PartsOfSpeech(str, Enum):
    VERB = "verb"
    ADV = "adverb"
    ADJ = "adjective"
    NOUN = "noun"
    INTJ = "interjection"

#
PPS_MAX_ID_PK = "max_id:{pps}"
MAX_ID_COL = "max_id"

#
INTERACTION_PKEY = "interaction:{}"
CHAR_PKEY = "user_stats:{}"
MESSAGE_COLUMN = "message"
VICTIM_COLUMN = "victim"
PERP_COUNT_COLUMN = "perp_count"
TRANSITIVITY_COLUMN = "is_transitive"


class BaseComplimentsHandler(CommandHandler):
    def _get_max_id(self):
        return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE,
                pkey_value=PPS_MAX_ID_PK.format(pps=self.pps),
            )[0][MAX_ID_COL]

    def _increment_max_id(self):
        dynamodb.increment_counter(TOXIC_INTERACTION_TABLE, PPS_MAX_ID_PK.format(pps=self.pps), MAX_ID_COL)

    def _get_words_by_pps(self, pps: str):
        return dynamodb.get_rows(
            TOXIC_INTERACTION_TABLE,
            filterExpression=f"contains ({PK}, :pk)",
            expressionAttributeValues={":pk": f"pps:{pps}"},
        )


class ComplimentHandler(BaseComplimentsHandler):
    FIELDS = {
        "perp": "user_id",
        "victim": "who",
        "channel_id": "channel_id",
        "allow_group_violence": "allow_group_violence",
        "interaction_id": "base_interaction_id",
    }

    MESSAGE_DIVIDER = "-------------------------"

    def __init__(self, command, **kwargs) -> None:
        super().__init__(command, **kwargs)
        if not self.victim:
            self.victim = self._get_interaction_victim()

    def _get_interaction_victim(self):
        return dynamodb.get_rows(
            TOXIC_INTERACTION_TABLE,
            pkey_value=INTERACTION_PKEY.format(self.interaction_id),
        )[0][VICTIM_COLUMN]

    def _record_compliment(self, message):
        dynamodb.set_rows(
            TOXIC_INTERACTION_TABLE,
            INTERACTION_PKEY.format(self.interaction_id),
            {MESSAGE_COLUMN: message, VICTIM_COLUMN: self.victim},
        )

        dynamodb.increment_counter(
            TOXIC_INTERACTION_TABLE,
            CHAR_PKEY.format(self.perp),
            PERP_COUNT_COLUMN,
        )

    def _get_compliment_count(self):
        try:
            return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE, pkey_value=CHAR_PKEY.format(self.perp)
            )[0][PERP_COUNT_COLUMN]
        except:
            return 0

    def _get_message(self):
        try:
            return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE,
                pkey_value=INTERACTION_PKEY.format(self.interaction_id),
            )[0][MESSAGE_COLUMN]
        except:
            return ""

    def _get_phrase(self):
        verbs = self._get_words_by_pps(PartsOfSpeech.VERB)
        primary_verb = random.choice(verbs)
        do = {}
        do_adj = {}

        intj = {}
        intj_chance = 0.2
        if random.random() < intj_chance:
            intjs = self._get_words_by_pps(PartsOfSpeech.NOUN)
            intj = random.choice(intjs)

        if primary_verb.get(TRANSITIVITY_COLUMN, False):
            nouns = self._get_words_by_pps(PartsOfSpeech.NOUN)
            do = random.choice(nouns)

            adj_chance = 0.5
            if random.random() < adj_chance:
                adjectives = self._get_words_by_pps(PartsOfSpeech.ADJ)
                do_adj = random.choice(adjectives)

        adv_chance = 0.5
        pv_adv = {}
        if random.random() < adv_chance:
            adverbs = self._get_words_by_pps(PartsOfSpeech.ADV)
            pv_adv = random.choice(adverbs)

        phrase = ""
        phrase += f"{intj[WORD_COLUMN]}! " if WORD_COLUMN in intj else ""

        for part in [primary_verb, do_adj, do, pv_adv]:
            phrase += f"{part[WORD_COLUMN]} " if WORD_COLUMN in part else ""


        return phrase

    def handle(self):
        perp_mention = discord.mention_user(self.perp)
        victim_mention = discord.mention_user(self.victim)

        # format message
        phrase = self._get_phrase()

        message = f"""{perp_mention}: {victim_mention} {phrase}."""
        
        self._record_compliment(message)

        dots = ""
        # there's a max length; remove previous messages
        while len(message) > discord.MAX_EMBED_DESCRIPTION_LENGTH - (len(dots)):
            dots = f"*there's been too much kindness to fit into a single embed*\n..."
            message = message.split(self.MESSAGE_DIVIDER, 1)[1]
        else:
            message = dots + message

        embedded_message = {
            "embeds": [
                {
                    "type": "rich",
                    "title": "Violence",
                    "description": message,
                }
            ],
        }

        if True:  # self.allow_group_violence:
            embedded_message["components"] = compliment_view.ComplimentView().get_buttons()

        return embedded_message


class WordHandler(BaseComplimentsHandler):
    FIELDS = {"word": "word", "pps": "pps", "is_transitive": "is_transitive"}

    def handle(self):
        next_id = self._get_max_id() + 1
        self._increment_max_id()

        dynamodb.set_rows(
            TOXIC_INTERACTION_TABLE, PK.format(word=self.word, pps=self.pps, id=next_id), {ID_COLUMN: next_id, PART_COLUMN: self.pps, WORD_COLUMN: self.word, TRANSITIVITY_COLUMN: self.is_transitive}
        )
        return f"The {self.pps} '{self.word}' has been added to the wordbank."



handler_map = {
    "compliment": ComplimentHandler,
    "join_compliment": ComplimentHandler,
    "add_compliment_word": WordHandler,
}


def handle(command, info):
    handler = handler_map[command](**info, **info["options"])
    return handler.handle()


# todo: this is bad
def display(info):
    command = info["command"]
    handler = handler_map[command](
        base_interaction_id=info["interaction_id"], **info, **info["options"]
    )
    return handler.handle()


# todo: this is bad
def handle_button(info):
    button = info["data"]["id"]
    print(button)
    if button == compliment_view.ComplimentView.JOIN_ID:
        handler = handler_map["compliment"](command=button, **info)
        return handler.handle()


def is_button(component_id):
    return component_id in [compliment_view.ComplimentView.JOIN_ID]
