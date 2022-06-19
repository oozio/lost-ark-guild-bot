from dataclasses import dataclass
import enum
from typing import Optional, Tuple

class EquipmentType(enum.Enum):
  ARMOR = 0
  WEAPON = 1

@dataclass(frozen=True)
class Material:
  id: str
  amount: int

@dataclass(frozen=True)
class Enhancement:
  id: str
  rate_increase_permyria: int
  max_amount: int

@dataclass(frozen=True)
class HoningLevel:
  base_item_level: int
  next_item_level: int
  tier: int
  base_level: int
  equipment_type: EquipmentType
  base_rate_permyria: int
  cost: Tuple[Material]
  enhancements: Tuple[Enhancement] = ()
  max_enhancement_rate_permyria: int = 0
  book_id: Optional[str] = None

HONES = (
    HoningLevel(
        base_item_level=1302,
        next_item_level=1304,
        tier=3,
        base_level=0,
        equipment_type=EquipmentType.ARMOR,
        base_rate_permyria=10000,
        cost=(
            Material(id='guardian-stone-crystal-0', amount=82),
            Material(id='honor-shard', amount=22),
            Material(id='honor-leapstone-2', amount=2),
            Material(id='silver', amount=11100),
        ),
    ),
    HoningLevel(
        base_item_level=1304,
        next_item_level=1307,
        tier=3,
        base_level=1,
        equipment_type=EquipmentType.ARMOR,
        base_rate_permyria=10000,
        cost=(
            Material(id='guardian-stone-crystal-0', amount=82),
            Material(id='honor-shard', amount=22),
            Material(id='honor-leapstone', amount=2),
            Material(id='silver', amount=11380),
        ),
    ),
    HoningLevel(
        base_item_level=1307,
        next_item_level=1310,
        tier=3,
        base_level=2,
        equipment_type=EquipmentType.ARMOR,
        base_rate_permyria=10000,
        cost=(
            Material(id='guardian-stone-crystal-0', amount=82),
            Material(id='honor-shard', amount=22),
            Material(id='honor-leapstone-2', amount=2),
            Material(id='silver', amount=11660),
        ),
    ),
    HoningLevel(
        base_item_level=1310,
        next_item_level=1315,
        tier=3,
        base_level=3,
        equipment_type=EquipmentType.ARMOR,
        base_rate_permyria=10000,
        cost=(
            Material(id='guardian-stone-crystal-0', amount=120),
            Material(id='honor-shard', amount=32),
            Material(id='honor-leapstone-2', amount=4),
            Material(id='simple-oreha-fusion-material-1', amount=2),
            Material(id='silver', amount=11960),
        ),
    ),
    HoningLevel(
        base_item_level=1325,
        next_item_level=1330,
        tier=3,
        base_level=6,
        equipment_type=EquipmentType.ARMOR,
        base_rate_permyria=6000,
        cost=(
            Material(id='guardian-stone-crystal-0', amount=156),
            Material(id='honor-shard', amount=42),
            Material(id='honor-leapstone-2', amount=4),
            Material(id='simple-oreha-fusion-material-1', amount=4),
            Material(id='silver', amount=12840),
            Material(id='gold', amount=70),
        ),
        enhancements=(
            Enhancement(id='solar-grace-1',
                        rate_increase_permyria=125,
                        max_amount=24),
            Enhancement(id='solar-blessing-2',
                        rate_increase_permyria=250,
                        max_amount=12),
            Enhancement(id='solar-protection-3',
                        rate_increase_permyria=750,
                        max_amount=4),
        ),
        max_enhancement_rate_permyria=4000,
        book_id='tailoring-basic-mending-3',
    ),
)

HONES_DICT = {(h.base_item_level, h.equipment_type): h for h in HONES}