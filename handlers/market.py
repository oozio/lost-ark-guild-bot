from constants import market_data as md_const
from utils import discord
from utils.lost_ark import market_prices, items


def handle(command, cmd_input):
    if command == "price":
        # dunno how to put in unlimited # of autocompletable options
        item_id = md_const.ITEM_NAMES_TO_IDS[cmd_input["item"].lower()]
        
        price_data = market_prices.get_price_data([item_id])
        data = price_data[item_id]
        item = items.Item(data)
        result = {
            'content': "",
            "embed": item.format_for_embed()
        }
        return result
    elif command == "mari":
        return market_prices.profitable_mari_items()
    else:
        return f"UNKNOWN COMMAND: {command}"
