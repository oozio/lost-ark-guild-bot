from typing import List

from views.button import Button


class PunchView:
    JOIN_ID = "join"

    def get_buttons(self):
        return [
            {
                "type": 1,
                "components": [
                    {"type": 2, "label": "Join", "style": 1, "custom_id": self.JOIN_ID}
                ],
            }
        ]
