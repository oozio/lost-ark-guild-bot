from typing import List

from views.button import Button
from constants import roles
from utils import discord


ADD_TEMPLATE = "___add_role__{}"
RM_TEMPLATE = "___rm_role__{}"


class RoleSelectorView:
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

    def __init__(self, server_id: str) -> None:
        self.all_roles = discord._get_all_roles(server_id)
        # generate buttons for all channel-related roles

    def _wrap_in_action_rows(self, items: List[dict], max_per_row):
        # max 5 things per row
        chunked_items = [
            items[i : i + max_per_row] for i in range(0, len(items), max_per_row)
        ]

        action_rows = []

        for chunk in chunked_items:
            action_rows.append({"type": 1, "components": chunk})

        return action_rows

    def _get_id(self, role_name: str, operation: roles.RoleOperations):
        return (
            RM_TEMPLATE.format(role_name)
            if operation == roles.RoleOperations.RM
            else ADD_TEMPLATE.format(role_name)
        )

    def get_buttons(
        self,
        role_type: roles.RoleTypes,
        operation: roles.RoleOperations,
        color: Button.Styles,
        emoji,
        max_per_row=5,
    ):
        buttons = []
        for role in self.all_roles:
            role_name = role["name"]
            if role_name in roles.ROLES_BY_TYPE[role_type]:
                button = Button(
                    custom_id=self._get_id(role_name, operation),
                    label=f"{role_name}",
                    style=color.value,
                    emoji=emoji,
                )

                buttons.append(vars(button))

        buttons.sort(
            key=lambda item: roles.ROLES_BY_TYPE[role_type].index(item["label"])
        )

        return self._wrap_in_action_rows(buttons, max_per_row)
