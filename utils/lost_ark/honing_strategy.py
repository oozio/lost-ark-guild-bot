import dataclasses
import math
from typing import List, Optional, Sequence, Tuple, Union

from constants import honing_data
from cpp_modules import honing_cpp  # pytype: disable=import-error
from utils.lost_ark import market_prices

_BOOK_PERMYRIA = 1000
_MAX_ARTISANS_POINTS = 21506
_ARTISANS_CONVERSION_NUMERATOR = 465
_ARTISANS_CONVERSION_DENOMINATOR = 100000
_MYRIA = 10000


@dataclasses.dataclass
class _HoningState:
    rate: int
    artisans: int

    def prettify(self) -> str:
        pretty_rate = self.rate * 100 / _MYRIA
        pretty_artisans = round(
            int(
                min(self.artisans, _MAX_ARTISANS_POINTS) *
                _ARTISANS_CONVERSION_NUMERATOR) /
            _ARTISANS_CONVERSION_DENOMINATOR, 2)
        return (f'Unenhanced Rate: {pretty_rate}%, '
                f'Artisan\'s Energy: {pretty_artisans}%')


_Combination = Tuple[int, ...]

_GUARANTEED_SUCCESS = (-1, -1)


def _rate(honing_level: honing_data.HoningLevel,
          combination: _Combination) -> int:
    permyria = 0
    num_books = 0
    for i, num in enumerate(combination):
        if i == len(honing_level.enhancements):
            num_books = num
            break
        permyria += num * honing_level.enhancements[i].rate_increase_permyria
    permyria = min(permyria, honing_level.max_enhancement_rate_permyria)
    permyria += num_books * _BOOK_PERMYRIA
    return permyria


def _cost(combination: _Combination, prices: Sequence[float]) -> float:
    return sum((num * price for num, price in zip(combination, prices)))


def get_honing_strategy(
    honing_level: honing_data.HoningLevel,
    starting_rate: Optional[float] = None,
    starting_artisans: float = 0
) -> Tuple[float, float, List[_Combination], List[_HoningState]]:
    market_client = market_prices.MarketClient()
    market_client.get_price_data_for_category('Enhancement Material')
    base_cost = sum(
        market_client.get_unit_price(m.item_id) * m.amount
        for m in honing_level.cost)

    enhancement_price_list = [
        market_client.get_unit_price(e.item_id)
        for e in honing_level.enhancements
    ]
    if honing_level.book_id is not None:
        enhancement_price_list.append(
            market_client.get_unit_price(honing_level.book_id))

    rate = (honing_level.base_rate_permyria
            if starting_rate is None else int(starting_rate * _MYRIA))
    artisans_points = int(math.ceil(starting_artisans * _MAX_ARTISANS_POINTS))

    best_actions, best_states_tuples = honing_cpp.get_strategy(
        honing_level, base_cost, enhancement_price_list, rate, artisans_points)
    best_states = [
        _HoningState(rate=t[0], artisans=t[1]) for t in best_states_tuples
    ]

    num_hones = 0.
    cost = 0.
    p = 1.
    for state, action in zip(best_states, best_actions):
        num_hones += p
        cost += p * (base_cost + _cost(action, enhancement_price_list))
        success = _rate(honing_level, action) + state.rate
        if success >= _MYRIA:
            break
        p *= (_MYRIA - success) / _MYRIA

    return num_hones, cost, best_actions, best_states
