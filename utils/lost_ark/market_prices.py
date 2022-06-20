from constants import market_data as md_const
from typing import Dict, Optional, Sequence, Union
from utils import http

_DataType = Union[str, int, float]
_PriceDict = Dict[str, Dict[str, _DataType]]


def get_price_data(item_ids: Sequence[str],
                   region: str = 'North America West',
                   cache: Optional[_PriceDict] = None) -> _PriceDict:
  '''Returns the raw market data from lostarkmarket.online.

  See https://documenter.getpostman.com/view/20821530/UyxbppKr
  for more API info.

  Args:
    item_ids: sequence of item ids to fetch.
    region: The market's region. Default is 'North America West'.

  Returns:
    A dictionary containing the raw data from lostarkmarket.online for each
    item id specified. If an item does not exist, the dictionary will omit that
    item. For example, if item_ids is ['basic-oreha-fusion-material-2'], the
    output may be:

    {
      'basic-oreha-fusion-material-2': {
        'amount': 1,
        'avgPrice': 8.9,
        'category': 'Enhancement Material',
        'cheapestRemaining': 356969,
        'gameCode': '6861008',
        'id': 'basic-oreha-fusion-material-2',
        'image': 'https://www.lostarkmarket.online/assets/item_icons/basic-oreha-fusion-material.webp',
        'lowPrice': 9,
        'name': 'Basic Oreha Fusion Material',
        'rarity': 2,
        'recentPrice': 9,
        'shortHistoric': {
          '2022-06-06': 9,
          '2022-06-07': 9,
          '2022-06-08': 9,
          '2022-06-09': 9,
          '2022-06-10': 9,
          '2022-06-11': 8.96,
          '2022-06-12': 8
        },
        'subcategory': 'Honing Materials',
        'updatedAt': '2022-06-12T19:58:29.631Z'
      }
    }

  Raises:
    requests.HTTPError: An error occurred retrieving data from the API.
  '''
  if cache is not None:
    item_ids = [item_id for item_id in item_ids if item_id not in cache]
  else:
    cache = {}

  if not item_ids:
    return {}

  request_url = f'{md_const.MARKET_API}/export-market-live/{region}'
  raw_json = http.make_request('GET', request_url, params={'items': ','.join(item_ids)})
  cache.update({item['id']: item for item in raw_json})
  return cache


def get_price_data_for_category(category: str,
                   region: str = 'North America West',
                   cache: Optional[_PriceDict] = None) -> _PriceDict:
  if cache is None:
    cache = {}
  request_url = f'{md_const.MARKET_API}/export-market-live/{region}'
  raw_json = http.make_request('GET', request_url, params={'category': category})
  cache.update({item['id']: item for item in raw_json})
  return cache


_HARDCODED_PRICES = {
  'gold': 1.,
  'silver': 0.,
}
def get_unit_price(item_id: str, cache: Optional[_PriceDict] = None):
  if item_id in _HARDCODED_PRICES:
    return _HARDCODED_PRICES[item_id]

  if cache is None:
    cache = {}

  if item_id in cache:
    price_json = cache[item_id]
    return price_json['lowPrice'] / price_json['amount']

  if item_id.endswith('-shard'):
    low_unit_price = float('inf')
    for suffix, amount in (('-pouch-s-1', 500),
                           ('-pouch-m-2', 1000),
                           ('-pouch-l-3', 1500)):
      pouch_id = item_id + suffix
      price_json = get_price_data([pouch_id], cache=cache)[pouch_id]
      unit_price = price_json['lowPrice'] / price_json['amount'] / amount
      if unit_price < low_unit_price:
        low_unit_price = unit_price
        low_price = price_json['lowPrice']
        low_amount = price_json['amount'] * amount
        low_id = pouch_id
    cache[item_id] = {'id': low_id, 'lowPrice': low_price, 'amount': low_amount}
  else:
    get_price_data([item_id], cache=cache)

  price_json = cache[item_id]
  return price_json['lowPrice'] / price_json['amount']


def item_gold_prices(item_ids: Sequence[str], 
                     region: str = 'North America West') -> Dict[str, _DataType]:
  '''
  Args:
    item_ids: sequence of item ids to fetch.
    region: The market's region. Default is 'North America West'.

  Returns:
    A dictionary containing the current lowest market price from lostarkmarket.online 
    for each item id specified. If an item does not exist, the dictionary will omit that
    item.
  '''
  request_url = f'{md_const.MARKET_API}/export-market-live/{region}'
  raw_json = http.make_request('GET', request_url, params={'items': ','.join(item_ids)})
  return {item['id']: item['lowPrice'] for item in raw_json}


def gold_of_crystal() -> float:
  '''
  Request_Data wrapper to return only the lowest price for blue crystal
  Args:
    None

  Returns:
    A float representing the current lowest price for blue crystals
  '''
  return item_gold_prices([md_const.BLUE_CRYSTAL_ID])


def item_mari_prices():
  '''
  Converts LostArkMarket Mari shop prices from crystal to gold

  Args:
    None

  Returns:
   A dictionary containing items where each key is the LostArkMarket ID and the
   value will the respective gold cost calculated by using the current blue crystal
   price
  '''

  # Individual gold cost of each item in Mari's
  mari_gold_costs = {}
  for (item, (bc_price, bundle_no)) in md_const.MARI_ITEM_INFO.items():
      mari_gold_costs[item] = round((gold_of_crystal() * bc_price / bundle_no), 2)

  return mari_gold_costs


def profitable_mari_items() -> str:
  '''
  Displays all the profitable purchases available in Mari shop. If an item in mari
  shop has a lower gold than its market counterpart, it will display the item and
  percentage discount

  Args:
    None

  Returns:
    An ugly string dump
  '''
  mari_prices = item_mari_prices()
  output = ""
  for (item, gold_price) in item_gold_prices():
      price_diff = mari_prices[item] - gold_price
      #Will do a pretty format later, want to test to see how this gets displayed on discord first
      if price_diff < 0:
        percent_diff = round(price_diff / gold_price * 100, 2)
        output += f"\n {item}: {mari_prices[item]}g (-{percent_diff}%)"

  return output
