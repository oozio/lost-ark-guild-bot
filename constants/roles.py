from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union


class RoleTypes(str, Enum):
    RAID = "raid"
    COLOR = "color"
    MISC = "misc"

ROLES_BY_TYPE = {
    RoleTypes.RAID: ["Vykas", "Valtan", "Argos", "Abyssals", "GVG/GVE"],
    RoleTypes.COLOR: ["Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Gray"],
    RoleTypes.MISC: ["Secret Maps", "Achievement Hunter", "Bot Dev"]
}
