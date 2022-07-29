from typing import List

from constants.emojis import AvailabilityEmoji, ClassEmoji, EmojiEnum
from views.button import Button

CLASS_SELECTOR_ID = "class_selector"

# TODO: better typing
def _add_to_calendar_button():
    return Button(
        custom_id="add_event_to_calendar",
        label="Add to Calendar",
        style=Button.Styles.grey.value,
        disabled=True,
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
            ]
            + [vars(_add_to_calendar_button())],
        },
        {
            "type": 1,
            "components": [
                _generate_emoji_dropdown([char_class for char_class in ClassEmoji])
            ],
        },
    ]
