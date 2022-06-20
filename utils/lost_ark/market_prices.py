from typing import Dict, Optional, Sequence, Union
from constants import market_data
from utils import http

_DataType = Union[str, int, float]
_PriceDict = Dict[str, Dict[str, _DataType]]

def get_price_data(item_ids: Sequence[str],
                   region: str = 'North America West',
                   cache: Optional[_PriceDict] = None) -> _PriceDict:
  '''Returns the raw market data from lostarkmarket.online.

  See https://documenter.getpostman.com/view/20821530/UyxbppKr for more APi
  info.

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

  request_url = 'https://www.lostarkmarket.online/api/export-market-live' \
               f'/{region}'
  raw_json = http.make_request('GET', request_url, params={'items': ','.join(item_ids)})
  cache.update({item['id']: item for item in raw_json})
  return cache

def get_price_data_for_category(category: str,
                   region: str = 'North America West',
                   cache: Optional[_PriceDict] = None) -> _PriceDict:
  if cache is None:
    cache = {}
  request_url = 'https://www.lostarkmarket.online/api/export-market-live' \
               f'/{region}'
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


def get_lowest_prices(item_ids: Sequence[str], 
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
  request_url = 'https://www.lostarkmarket.online/api/export-market-live' \
               f'/{region}'
  raw_json = http.make_request('GET', request_url, params={'items': ','.join(item_ids)})
  return{item['id']: item['lowPrice'] for item in raw_json}


def get_current_blue_crystal_price() -> float:
  '''
  Request_Data wrapper to return only the lowest price for blue crystal
  Args:
    None

  Returns:
   A float value representing the current loweest price for blue crystal
  '''
  blue_crystal_data = get_lowest_prices([market_data.BLUE_CRYSTAL_ID])
  if len(blue_crystal_data) > 0:
    return blue_crystal_data[market_data.BLUE_CRYSTAL_ID]

def convert_mari_store_crystal_to_gold_prices():
  '''
  Converts LostArkMarket Mari shop prices from crystal to gold

  Args:
    None

  Returns:
   A dictionary containing items where each key is the LostArkMarket ID and the
   value will the respective gold cost calculated by using the current blue crystal
   price
  '''
  #Grab all item id's for only the T3 priority items in Mari's cash shop
  mari_item_ids = market_data.MARI_SHOP_CRYSTAL_PRICES_AND_QUANITITIES.keys()
  #print(mari_item_ids)

  #Get current lowest blue crystal price from LostMarketOnline
  blue_crystal_price = get_current_blue_crystal_price()
  #print("Blue crystal price is " + str(blue_crystal_price))

  #Calculate equivalent gold value for each Mari priority item factoring in 
  #current blue crystal price. If the shop sells an item in a bundle of x number
  #of items. Will divide by X to get value of each individual item.
  mari_store_crystal_to_gold_prices = {}
  for x in market_data.MARI_SHOP_CRYSTAL_PRICES_AND_QUANITITIES:
      mari_store_crystal_to_gold_prices[x] =  round((blue_crystal_price
                                              *market_data.MARI_SHOP_CRYSTAL_PRICES_AND_QUANITITIES[x][0]
                                              /market_data.MARI_SHOP_CRYSTAL_PRICES_AND_QUANITITIES[x][1]),2)
 
  #if number of items returned do not match, there was likely an error in sending
  #the correct ID's
  if (len(mari_item_ids) != len(mari_store_crystal_to_gold_prices)):
    raise Exception("Error in retreiving data from Market")
  else:
    #print(mari_store_crystal_to_gold_prices)
    return mari_store_crystal_to_gold_prices

def generate_profitable_mari_purchases_string() -> str:
  '''
  Displays all the profitable purchases available in Mari shop. If an item in mari
  shop has a lower gold than its market counterpart, it will display the item and
  percentage discount

  Args:
    None

  Returns:
   An ugly string dump
  '''
  #Grab all item id's for only the T3 priority items in Mari's cash shop
  mari_item_ids = market_data.MARI_SHOP_CRYSTAL_PRICES_AND_QUANITITIES.keys()

  #Grab lowest prices for each individual item from Mari's cash shop
  mari_market_lowest_prices = get_lowest_prices(mari_item_ids)

  #Calculate equivalent gold value for each Mari priority item factoring in 
  #current blue crystal price. If the shop sells an item in a bundle of x number
  #of items. Will divide by X to get value of each individual item.
  mari_store_crystal_to_gold_prices = convert_mari_store_crystal_to_gold_prices()

  outputString = ""

  mari_market_and_store_difference={}
  mari_market_and_store_percentage_difference={}
  for x in mari_store_crystal_to_gold_prices:
      mari_market_and_store_difference[x] = mari_market_lowest_prices[x] - mari_store_crystal_to_gold_prices[x]
      mari_market_and_store_percentage_difference[x] = mari_market_and_store_difference[x]/mari_market_lowest_prices[x]
      #Will do a pretty format later, want to test to see how this gets displayed on discord first
      if(mari_market_and_store_percentage_difference[x] < 1):
          outputString = (outputString + "\n" + str(x) + ": " 
                          + str(mari_store_crystal_to_gold_prices[x]) + "g (-"
                          + str(round(mari_market_and_store_percentage_difference[x]*100,2)) + "%)")

  # print(mari_market_lowest_prices)
  # print(mari_market_and_store_difference)
  # print(outputString)
  return outputString
