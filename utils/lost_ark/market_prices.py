import json
import requests
from typing import Dict, Sequence, Union

_DataType = Union[str, int, float]

def GetPriceData(item_ids: Sequence[str],
                 region: str = 'North America West') -> Dict[str, _DataType]:
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
  params = ','.join(item_ids)
  request_url = 'https://www.lostarkmarket.online/api/export-market-live' \
               f'/{region}?items={params}'
  response = requests.get(request_url)
  if response.status_code != 200:
    response.raise_for_status()
  raw_json = json.loads(response.text)
  return {item['id']: item for item in raw_json}
