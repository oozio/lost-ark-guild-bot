from enum import Enum


class EmojiEnum(Enum):
    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, emoji_name: str, emoji_id: str = None):
        # Expects <name>: <emoji_name>, <emoji_id>
        self.emoji_name = emoji_name
        self.emoji_id = emoji_id
        
    def __repr__(self):
        return f"<:{self.emoji_name}:{self.emoji_id}>"
        

class AvailabilityEmoji(EmojiEnum):
    COMING = "mokoko_lets_play", "984283567859331086"
    NOT_COMING = "mokoko_puddle", "984284429671338014"
    MAYBE = "mokoko_huh", "984283548095750195" 
 

class ClassEmoji(EmojiEnum):
    ARCANIST = "arcanist", "999209761285361774"
    ARTILLERIST = "artillerist", "999209777504727071"
    ARTIST = "artist", "999209793958973551"
    BARD = "bard", "999209811176607744"
    BERSERKER = "berserker", "999209825797943356"
    DEADEYE = "deadeye", "999209841438498876"
    DEATHBLADE = "deathblade", "999209861348864020"
    DESTROYER = "destroyer", "999209878650376192"
    GLAIVIER = "glaivier", "999209894731321434"
    GUNLANCER = "gunlancer", "999209910845845534"
    GUNSLINGER = "gunslinger", "999209929745371237"
    MACHINIST = "machinist", "999209962003763260"
    PALADIN = "paladin", "999209977531072552"
    REAPER = "reaper", "999209992802537472"
    SCRAPPER = "scrapper", "999210007721680906"
    SHADOWHUNTER = "shadowhunter", "999210021973938207"
    SHARPSHOOTER = "sharpshooter", "999210036406521856"
    SORCERESS = "sorceress", "999210051191451658"
    SOULFIST = "soulfist", "999210065221390466"
    STRIKER = "striker", "999210080002134016"
    SUMMONER = "summoner", "999210094921269258"
    WARDANCER = "wardancer", "999210110389866546"


EMOJI_IDS = {
    'gold':
    '<:gold:991944972804829185>',
    'silver':
    '<:silver:991945407473143929>',
    'honor-shard':
    '<:honorshard:991942576020140052>',
    'crystallized-guardian-stone-0':
    '<:guardianstonecrystal0:991945647492178000>',
    'crystallized-destruction-stone-0':
    '<:destructionstonecrystal0:991945773237416048>',
    'honor-leapstone-2':
    '<:honorleapstone2:991946666204741682>',
    'great-honor-leapstone-2':
    '<:greathonorleapstone2:991946650010533918>',
    'simple-oreha-fusion-material-1':
    '<:simpleorehafusionmaterial1:991946707480891473>',
    'basic-oreha-fusion-material-2':
    '<:basicorehafusionmaterial2:991946731128356916>',
    'solar-grace-1':
    '<:solargrace1:991942897861677108>',
    'solar-blessing-2':
    '<:solarblessing2:991942770510024704>',
    'solar-protection-3':
    '<:solarprotection3:991943070767644742>',
    'tailoring-basic-mending-3':
    '<:tailoringbasicmending3:991946764590526464>',
    'metallurgy-basic-welding-3':
    '<:metallurgybasicwelding3:991946786392514710>',
    'tailoring-applied-mending-4':
    '<:tailoringappliedmending4:991943401484320778>',
    'metallurgy-applied-welding-4':
    '<:metallurgyappliedwelding4:991943536096321546>',
}
