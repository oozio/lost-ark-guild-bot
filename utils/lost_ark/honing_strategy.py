from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Set, Sequence, Tuple, Union

from constants import honing_data
from utils import multi_range
from utils.lost_ark import market_prices

_BOOK_PERMYRIA = 1000
_MAX_ARTISANS_POINTS = 21500
_MYRIA = 10000


@dataclass(frozen=True)
class _HoningState:
    rate_permyria: int
    artisans_points: int = 0


_Combination = Tuple[int, ...]


class StrategyCalculator(object):
    def __init__(self):
        self.market_client = market_prices.MarketClient()

    def _rate_and_cost(self,
                       combination: _Combination) -> Tuple[int, float]:
        permyria = 0
        cost = 0
        use_book = False
        for i, num in enumerate(combination):
            if self.honing_level.book_id is not None and i == len(self.honing_level.enhancements):
                use_book = (num == 1)
                break
            permyria += num * \
                self.honing_level.enhancements[i].rate_increase_permyria
            cost += num * \
                self.market_client.get_unit_price(
                    self.honing_level.enhancements[i].item_id)
        permyria = min(
            permyria, self.honing_level.max_enhancement_rate_permyria)
        if use_book:
            permyria += _BOOK_PERMYRIA
            cost += self.market_client.get_unit_price(
                self.honing_level.book_id)
        return permyria, cost

    def _get_enhancement_combination_list(self) -> List[Tuple[int, float, _Combination]]:
        enhancements = self.honing_level.enhancements
        num_enhancements = len(enhancements)
        stops = [e.max_amount + 1 for e in enhancements]
        if self.honing_level.book_id is not None:
            stops.append(2)
        counts = [c for c in multi_range.MultipleRange(stops)]

        to_sort = [(self._rate_and_cost(c), c)
                   for c in counts]

        combinations = []
        rates_seen = set()
        for (rate, cost), counts in sorted(to_sort):
            if rate in rates_seen:
                continue
            rates_seen.add(rate)
            combinations.append((rate, cost, counts))

        filtered = []
        min_cost = float('inf')
        for rate, cost, counts in reversed(combinations):
            if cost >= min_cost:
                continue
            min_cost = cost
            filtered.append((rate, cost, counts))
        return filtered

    def _apply_combination(self,
                           honing_state: _HoningState,
                           combination: _Combination) -> Tuple[int, _HoningState]:
        new_base_rate = min(2 * self.honing_level.base_rate_permyria,
                            honing_state.rate_permyria + self.honing_level.base_rate_permyria // 10)

        enhancement_rate, _ = self._rate_and_cost(combination)
        enhanced_rate = min(
            _MYRIA, honing_state.rate_permyria + enhancement_rate)
        new_points = min(_MAX_ARTISANS_POINTS,
                         honing_state.artisans_points + enhanced_rate)
        return (enhanced_rate,
                _HoningState(rate_permyria=new_base_rate, artisans_points=new_points))

    _EdgeDict = Dict[_HoningState, Dict[_HoningState, _Combination]]

    def _construct_graph(self,
                         combinations: Sequence[_Combination],
                         starting_state: Optional[_HoningState] = None
                         ) -> Tuple[Set[_HoningState], _EdgeDict, _EdgeDict]:
        if starting_state is None:
            starting_state = _HoningState(
                rate_permyria=self.honing_level.base_rate_permyria)

        states = set()
        in_edges = {starting_state: {}}
        out_edges = {}
        stack = [starting_state]
        while stack:
            state = stack.pop()
            if state in states:
                continue
            states.add(state)
            out_edges[state] = {}
            if state.artisans_points == _MAX_ARTISANS_POINTS:
                continue
            for combination in combinations:
                success, out_state = self._apply_combination(state,
                                                             combination)
                if success == _MYRIA:
                    continue
                stack.append(out_state)
                out_edges[state][out_state] = combination
                if out_state not in in_edges:
                    in_edges[out_state] = {}
                in_edges[out_state][state] = combination
        return states, in_edges, out_edges

    def get_honing_strategy(self, honing_level: honing_data.HoningLevel, starting_rate: Optional[float] = None,
                            starting_artisans: float = 0):
        self.market_client.get_price_data_for_category('Enhancement Material')
        self.honing_level = honing_level

        artisans_points = int(
            math.ceil(starting_artisans * _MAX_ARTISANS_POINTS))
        rate = (self.honing_level.base_rate_permyria
                if starting_rate is None
                else int(starting_rate * _MYRIA))
        starting_state = _HoningState(rate_permyria=rate,
                                      artisans_points=artisans_points)

        enhancement_combination_list = self._get_enhancement_combination_list()
        enhancement_combinations = {combination: (rate, cost)
                                    for rate, cost, combination
                                    in enhancement_combination_list}
        states, in_edges, out_edges = self._construct_graph(enhancement_combinations,
                                                            starting_state=starting_state)

        out_edges_set = {k: set(v.keys()) for k, v in out_edges.items()}
        terminal_states = [state for state, edges
                           in out_edges_set.items() if not edges]

        base_cost = sum(self.market_client.get_unit_price(m.item_id) * m.amount
                        for m in self.honing_level.cost)
        costs = {}
        best_out_edge = {}
        while terminal_states:
            state = terminal_states.pop()
            min_cost = float('inf')
            min_edge = None
            for out_state, combination in out_edges[state].items():
                rate, cost = self._rate_and_cost(combination)
                enhanced_rate = min(_MYRIA, state.rate_permyria + rate)
                ev = (base_cost +
                      cost +
                      costs[out_state] * (_MYRIA - enhanced_rate) / _MYRIA)
                if ev < min_cost:
                    min_cost = ev
                    min_edge = out_state, combination

            if min_edge is None:
                costs[state] = base_cost
            else:
                costs[state] = min_cost
                best_out_edge[state] = min_edge

            for in_state, combination in in_edges[state].items():
                out_edges_set[in_state].remove(state)
                if not out_edges_set[in_state]:
                    terminal_states.append(in_state)

        best_path = []
        best_states = [starting_state]
        while best_states[-1] in best_out_edge:
            next_state, combination = best_out_edge[best_states[-1]]
            best_path.append(combination)
            best_states.append(next_state)

        del self.honing_level

        return costs[starting_state], best_path, best_states
