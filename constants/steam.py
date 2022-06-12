import random

from datetime import datetime
from enum import Enum

from constants.common import TrimmableClass
from constants.common import TYPED_NONES

# internal
class DynamoDBInfo(Enum):
    TABLE = "hippobotas_discord_steam"
    USER_COLUMN = "steam_username"
    PK_TEMPLATE = "discord_user_{}"

# search
STEAM_API = 'http://api.steampowered.com'
STEAM_COMMUNITY_API = 'https://steamcommunity.com/{url_vers}/{username}/?xml=1'

# formatting
FAVICON = "https://imgur.com/vnp9YrT.png"
