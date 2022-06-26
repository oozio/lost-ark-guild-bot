import dataclasses
from typing import Any, Dict

FAVICON = "https://www.lostarkmarket.online/assets/icons/favicon.png"


@dataclasses.dataclass
class Item:
    name: str
    item_id: str
    image: str
    low_price: float
    cheapest_remaining: int
    short_historic: Dict[str, float]

    def format_for_embed(self):
        embed = {
            "author": {
                "name": self.name,
                "icon_url": self.image
            },
            "fields": [{
                "name": "Current Price",
                "value":
                f"{self.low_price} gold:\n{self.cheapest_remaining} remaining",
                "inline": True
            }, {
                "name":
                "Historic Price",
                "value":
                "\n".join([
                    f"{date}: {price}"
                    for date, price in sorted(self.short_historic.items())
                ]),
                "inline":
                True
            }],
            "footer": {
                "icon_url":
                FAVICON,
                "text":
                f"Data from: https://www.lostarkmarket.online/north-america-west/market"
            },
        }

        return embed


def item_from_market(d: Dict[str, Any]) -> 'Item':
    name = d['name']
    item_id = d['id']
    image = d['image']
    low_price = d['lowPrice']
    cheapest_remaining = d['cheapestRemaining']
    short_historic = d['shortHistoric']
    return Item(name=name,
                item_id=item_id,
                image=image,
                low_price=low_price,
                cheapest_remaining=cheapest_remaining,
                short_historic=short_historic)  # pytype: disable
