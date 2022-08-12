from typing import List

from views.button import Button


class VoteView:
    # self.COMPONENTS = [
    #     {
    #         "type": 1,
    #         "components": [
    #             {
    #                 "type": 2,
    #                 "label": "Vykas",
    #                 "style": 1,
    #                 "custom_id": "vykas"
    #             }
    #         ]

    #     }
    # ]

    def __init__(self, choices: list) -> None:
        self.choices = choices
        # generate buttons for all channel-related roles

    def _wrap_in_action_rows(self, items: List[dict]):
        # max 5 things per row
        MAX_ITEMS_PER_ROW = 5
        chunked_items = [
            items[i : i + MAX_ITEMS_PER_ROW]
            for i in range(0, len(items), MAX_ITEMS_PER_ROW)
        ]

        action_rows = []

        for chunk in chunked_items:
            action_rows.append({"type": 1, "components": chunk})

        return action_rows

    def get_buttons(self):
        buttons = []
        for choice in self.choices:
            buttons.append(vars(Button(custom_id=f"vote_{choice}", label=choice)))
        return self._wrap_in_action_rows(buttons)
