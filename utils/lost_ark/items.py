from constants.common import TrimmableClass

FAVICON = "https://www.lostarkmarket.online/assets/icons/favicon.png"

class Item(TrimmableClass):
    FIELDS = {
        "name": {
            "type": str,
            "readable_name": "_name"
            },
        "id": {
            "type": str,
            "readable_name": "_id"
            },
        "image": {
            "type": str,
            "readable_name": "_image_url"
            }, 
        "lowPrice": {
            "type": int,
            "readable_name": "Current Lowest Price"
            },
        "cheapestRemaining": {
            "type": int,
            "readable_name": "Cheapest Remaining"
        },
        "shortHistoric": {
            "type": dict,
            "readable_name": "Historic Prices"
        }
        }

    def __init__(self, kwargs):
        super().__init__(**kwargs)

        
    def format_for_embed(self):    
        embed = {
            "author": {
                "name": self.name,
                "icon_url": self.image
            },
            "fields": [
                {
                    "name": "Current Price",
                    "value": f"{self.lowPrice} gold\n   -{self.cheapestRemaining} remaining",
                    "inline": True
                },
                {
                    "name": "Historic Price",
                    "value": "\n".join([f"{date}: {price}" for date, price in sorted(self.shortHistoric.items())]),
                    "inline": True
                }
            ],
            "footer": {
                "icon_url": FAVICON,
                "text": f"Data from: https://www.lostarkmarket.online/north-america-west/market"
            },
        }

        return embed