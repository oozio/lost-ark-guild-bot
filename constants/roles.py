from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union

from views.button import Button


class RoleTypes(str, Enum):
    RAID = "raid"
    MISC = "misc"
    COLOR = "color"


class RoleOperations(str, Enum):
    ADD = "add"
    RM = "remove"


ROLES_BY_TYPE = {
    RoleTypes.RAID: [
        "Abyssals",
        "Argos",
        "Valtan",
        "Vykas",
    ],
    RoleTypes.COLOR: ["Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Gray"],
    RoleTypes.MISC: ["GVG/GVE", "Secret Maps", "Achievement Hunter", "Bot Dev"],
}

ROLETYPE_COLORS = {
    RoleTypes.RAID: {
        RoleOperations.ADD: Button.Styles.grey,
        RoleOperations.RM: Button.Styles.grey,
    },
    RoleTypes.COLOR: {
        RoleOperations.ADD: Button.Styles.grey,
        RoleOperations.RM: Button.Styles.grey,
    },
    RoleTypes.MISC: {
        RoleOperations.ADD: Button.Styles.grey,
        RoleOperations.RM: Button.Styles.grey,
    },
}
