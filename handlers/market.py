

from utils import discord
from utils.lost_ark import market_prices, items

ITEM_NAMES_TO_IDS = {
    "greater honor leapstone": "great-honor-leapstone-2",
    "honor leapstone": "honor-leapstone-2",
    "honor shard pouch l": "honor-shard-pouch-l-3"
}

def handle(command, cmd_input):
    # Returns a tuple of (output: str, hide_output: bool)
    if command == "price":
        # dunno how to put in unlimited # of autocompletable options
        items = [cmd_input["item"]]
        item_ids = [ITEM_NAMES_TO_IDS[item_name.lower()] for item_name in items]
        
        price_data = market_prices.get_price_data(item_ids)
        data = price_data.values()
        item = items.Item(data)
        result = {
            'content': "",
            "embed": item.format_for_embed()
        }
        return result

    else:
        return f"UNKNOWN COMMAND: {command}"
