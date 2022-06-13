

from utils import discord
from utils.lost_ark import market_prices

ITEM_NAMES_TO_IDS = {
    "greater honor leapstone": "great-honor-leapstone-2",
    "honor leapstone": "honor-leapstone-2",
    "honor shard pouch l": "honor-shard-pouch-l-3"
}

def handle(command, cmd_input, user_id, server_id):
    # Returns a tuple of (output: str, hide_output: bool)
    if command == "price":
        # dunno how to put in unlimited # of autocompletable options
        items = [cmd_input["item"]]
        item_ids = [ITEM_NAMES_TO_IDS[item_name.lower()] for item_name in items]
        
        return market_prices.get_price_data(item_ids)

    else:
        return f"UNKNOWN COMMAND: {command}"
