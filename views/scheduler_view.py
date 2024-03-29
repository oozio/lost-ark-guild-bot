from enum import Enum
from typing import List

from constants.emojis import AvailabilityEmoji, ClassEmoji, EmojiEnum
from views.button import Button
from views.modal import Modal

CLASS_SELECTOR_ID = "class_selector"


class ScheduleButtons(str, Enum):
    ADD_TO_CALENDAR = "add_event_to_calendar"
    CHANGE_TIME = "change_start_time"
    SEE_COMMITMENTS = "see_signups"
    DELETE = "delete"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))


class CalendarButtons(str, Enum):
    SEE_COMMITMENTS = "see_signups"
    REFRESH = "refresh"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))


# TODO: better typing
def _add_to_calendar_button():
    return Button(
        custom_id=ScheduleButtons.ADD_TO_CALENDAR,
        label="Add to Server Events",
        style=Button.Styles.grey.value,
    )


def _change_time_modal():
    return Modal(
        custom_id=ScheduleButtons.CHANGE_TIME,
        label="Change Start Time"
    )


def _change_time_button():
    return Button(
        custom_id=ScheduleButtons.CHANGE_TIME,
        label="Change Start Time",
        style=Button.Styles.grey.value,
        disabled=False,
    )


def _delete_button():
    return Button(
        custom_id=ScheduleButtons.DELETE,
        label="Delete Event",
        style=Button.Styles.red.value,
    )


def _see_commitments_button():
    return Button(
        custom_id=ScheduleButtons.SEE_COMMITMENTS,
        label="My Events",
        style=Button.Styles.grey.value,
    )


def _refresh_calendar_button():
    return Button(
        custom_id=CalendarButtons.REFRESH,
        label="Refresh",
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
                "label": f"{emojiEnum.name.title().replace('_', ' ')}",
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
    def __init__(self, is_full=False):
        availability_buttons = {
            availability: vars(_generate_emoji_button(availability))
            for availability in AvailabilityEmoji
        }

        if is_full:
            availability_buttons[AvailabilityEmoji.COMING]["label"] = "FULL"
            availability_buttons[AvailabilityEmoji.COMING]["disabled"] = True
            availability_buttons[AvailabilityEmoji.COMING]["emoji"] = {
                "id": "984283879324147732",
                "name": "mokoko_vibrate",
            }

        self.components = [
            {
                "type": 1,
                "components": list(availability_buttons.values()),
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
                    vars(_delete_button()),
                ],
            },
        ]


class CalendarView:
    def __init__(self):
        self.components = [
            {
                "type": 1,
                "components": [
                    vars(_see_commitments_button()),
                    vars(_refresh_calendar_button()),
                ],
            },
        ]
