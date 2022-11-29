from enum import Enum
import random

from handlers.bully import CommandHandler

from utils import discord, dynamodb
from views import compliment_view
TOXIC_INTERACTION_TABLE = "lost_ark_words"

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
        max_id_info = dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE,
                pkey_value=PPS_MAX_ID_PK.format(pps=self.pps),
            )
        if not max_id_info:
            return 0
        else:
            return max_id_info[0][MAX_ID_COL]

    def _increment_max_id(self):
        dynamodb.increment_counter(TOXIC_INTERACTION_TABLE, PPS_MAX_ID_PK.format(pps=self.pps), MAX_ID_COL)

    def _get_words_by_pps(self, pps: str):
        return dynamodb.get_rows(
            TOXIC_INTERACTION_TABLE,
            filterExpression=f"contains (pk, :pk)",
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

    def _get_message(self):
        try:
            return dynamodb.get_rows(
                TOXIC_INTERACTION_TABLE,
                pkey_value=INTERACTION_PKEY.format(self.interaction_id),
            )[0][MESSAGE_COLUMN]
        except:
            return ""

    def _get_phrase(self, victim_mention):
        verbs = self._get_words_by_pps(PartsOfSpeech.VERB)
        intjs = self._get_words_by_pps(PartsOfSpeech.INTJ)
        nouns = self._get_words_by_pps(PartsOfSpeech.NOUN)
        adjectives = self._get_words_by_pps(PartsOfSpeech.ADJ)
        adverbs = self._get_words_by_pps(PartsOfSpeech.ADV)

        subj_adj = {}
        subj_adj_chance = 0.3
        if random.random() < subj_adj_chance:
            subj_adj = random.choice(adjectives)

        primary_verb = random.choice(verbs)
        do = {}
        do_adj = {}

        intj = {}
        intj_chance = 0.2
        if random.random() < intj_chance:
            intj = random.choice(intjs)

        if primary_verb.get(TRANSITIVITY_COLUMN, False):
            do = random.choice(nouns)

            adj_chance = 0.5
            if random.random() < adj_chance:
                do_adj = random.choice(adjectives)
            
        adv_chance = 0.5
        pv_adv = {}

        if primary_verb.get(WORD_COLUMN, "") == "is":
            pv_adv = random.choice(adjectives)
        else:            
            if random.random() < adv_chance:
                pv_adv = random.choice(adverbs)

        phrase = ""

        phrase += f"{subj_adj[WORD_COLUMN]} " if WORD_COLUMN in subj_adj else ""
        phrase += f"{victim_mention} "

        for part in [primary_verb, do_adj, do, pv_adv]:
            phrase += f"{part[WORD_COLUMN]} " if WORD_COLUMN in part else ""

        phrase = phrase.strip()
        phrase += f". {intj[WORD_COLUMN]}" if WORD_COLUMN in intj else ""

        return phrase.strip()

    def handle(self):
        perp_mention = discord.mention_user(self.perp)
        victim_mention = discord.mention_user(self.victim)

        # format message
        phrase = self._get_phrase(victim_mention)

        message = f"""{perp_mention}: {phrase}."""
        

        if self.command == compliment_view.ComplimentView.JOIN_ID:
            prev_msg = self._get_message().strip()
            if prev_msg:
                prev_msg += f"\n{self.MESSAGE_DIVIDER}\n"
                if perp_mention not in prev_msg:
                    prev_msg += f"{perp_mention} is here.\n"

            message = prev_msg + message
        
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
                    "title": "A Heartfelt Message (`/add_compliment_word` to expand the word pool)",
                    "description": message.strip(),
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
