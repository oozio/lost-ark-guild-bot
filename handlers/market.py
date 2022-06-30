from constants import market_data as md_const
from utils import discord
from utils.lost_ark import market_prices, items


def handle(command, cmd_input):
    if command == "price":
        # dunno how to put in unlimited # of autocompletable options
        item_id = md_const.ITEM_NAMES_TO_IDS[cmd_input["item"].lower()]

        market_client = market_prices.MarketClient()
        price_data = market_client.get_price_data([item_id])
        data = price_data[item_id]
        item = items.item_from_market(data)
        result = {'content': "", "embeds": [item.format_for_embed()]}
        return result
    elif command == "mari":
        market_client = market_prices.MarketClient()
        return market_client.profitable_mari_items()
    else:
        return f"UNKNOWN COMMAND: {command}"
