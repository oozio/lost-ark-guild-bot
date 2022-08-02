from enum import Enum
from typing import List

from constants.emojis import AvailabilityEmoji, ClassEmoji, EmojiEnum
from views.button import Button

CLASS_SELECTOR_ID = "class_selector"


class ScheduleButtons(str, Enum):
    ADD_TO_CALENDAR = "add_event_to_calendar"
    CHANGE_TIME = "change_start_time"
    SEE_COMMITMENTS = "see_signups"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))


# TODO: better typing
def _add_to_calendar_button():
    return Button(
        custom_id=ScheduleButtons.ADD_TO_CALENDAR,
        label="Add to Calendar",
        style=Button.Styles.grey.value,
    )


def _change_time_button():
    return Button(
        custom_id=ScheduleButtons.CHANGE_TIME,
        label="Change Start Time",
        style=Button.Styles.grey.value,
        disabled=True,
    )


def _see_commitments_button():
    return Button(
        custom_id=ScheduleButtons.SEE_COMMITMENTS,
        label="My Events",
        style=Button.Styles.grey.value,
    )


def _generate_emoji_button(emojiEnum: EmojiEnum) -> dict:
    emoji = {"id": emojiEnum.emoji_id, "name": emojiEnum.emoji_name}

    return Button(
        label=f"{emojiEnum.name.replace('_', ' ').title()}",
        custom_id=f"{emojiEnum.name}",
        emoji=emoji,
    )


def _generate_emoji_dropdown(choices: List[EmojiEnum]) -> dict:
    options = []
    for emojiEnum in choices:
        emoji = {"id": emojiEnum.emoji_id, "name": emojiEnum.emoji_name}

        options.append(
            {
                "label": f"{emojiEnum.name.title()}",
                "value": f"{emojiEnum.name}",
                "emoji": emoji,
            }
        )

    return {
        "type": 3,
        "custom_id": CLASS_SELECTOR_ID,
        "placeholder": "Which class are you bringing?",
        "options": options,
    }


class SchedulerView:
    COMPONENTS = [
        {
            "type": 1,
            "components": [
                vars(_generate_emoji_button(availability))
                for availability in AvailabilityEmoji
            ],
        },
        {
            "type": 1,
            "components": [
                _generate_emoji_dropdown([char_class for char_class in ClassEmoji])
            ],
        },
        {
            "type": 1,
            "components": [
                vars(_add_to_calendar_button()),
                vars(_change_time_button()),
                vars(_see_commitments_button()),
            ],
        },
    ]
