from typing import List

from views.button import Button
from constants import roles
from utils import discord


ADD_TEMPLATE = "___add_role__{}"
RM_TEMPLATE  = "___rm_role__{}"

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


    def _wrap_in_action_rows(self, items: List[dict]):
        # max 5 things per row
        MAX_ITEMS_PER_ROW = 5
        chunked_items = [items[i:i + MAX_ITEMS_PER_ROW] for i in range(0, len(items), MAX_ITEMS_PER_ROW)]

        action_rows = []

        for chunk in chunked_items:
            action_rows.append({
                "type": 1,
                "components": chunk
            })

        return action_rows


    def _get_add_id(self, role_name: str):
        return ADD_TEMPLATE.format(role_name)


    def _get_rm_id(self, role_name: str):
        return RM_TEMPLATE.format(role_name)


    def get_buttons(self, role_type: roles.RoleTypes):
        add_buttons = []
        rm_buttons = []
        for role in self.all_roles:
            role_name = role["name"]
            if role_name in roles.ROLES_BY_TYPE[role_type]:          
                add_button = Button(
                        custom_id=self._get_add_id(role_name),
                        label=role_name
                    )
                rm_button = Button(
                        custom_id=self._get_rm_id(role_name),
                        label=role_name,
                        style=Button.Styles.red.value
                    )
 
                add_buttons.append(vars(add_button))
                rm_buttons.append(vars(rm_button))

        return self._wrap_in_action_rows([*add_buttons, *rm_buttons])