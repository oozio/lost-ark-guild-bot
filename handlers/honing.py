from constants import emojis, honing_data as hd_const
from utils.lost_ark import honing_strategy


def handle(command, cmd_input):
    if command == "hone":
        # dunno how to put in unlimited # of autocompletable options
        equipment_type = hd_const.EquipmentType.WEAPON if cmd_input[
            'is_weapon'] else hd_const.EquipmentType.ARMOR
        equipment_type_str = 'weapon' if cmd_input['is_weapon'] else 'armor'
        ilevel = cmd_input['current_item_level']
        level_id = ilevel, equipment_type
        if level_id not in hd_const.HONES_DICT:
            return ('No data found for level {ilevel} {equipment_type_str}. '
                    'Contact Zethorix if you believe this is an error.')
        honing_level = hd_const.HONES_DICT[level_id]
        if 'base_rate' in cmd_input:
            br_input = cmd_input['base_rate']
            starting_rate = br_input / 100
            starting_rate_str = f'Starting Honing Success Rate: {br_input}'
        else:
            starting_rate = None
            starting_rate_str = ''
        if 'artisans_energy' in cmd_input:
            ae_input = cmd_input['artisans_energy']
            starting_artisans = ae_input / 100
            starting_artisans_str = f'Starting Artisan\'s Energy: {ae_input}'
        else:
            starting_artisans = 0
            starting_artisans_str = ''

        strategy_calculator = honing_strategy.StrategyCalculator()
        num_hones, average_cost, combination_list, state_list = \
            strategy_calculator.get_honing_strategy(
                honing_level,
                starting_rate=starting_rate,
                starting_artisans=starting_artisans)

        hsr_builder = []
        ae_builder = []
        enh_builder = []
        for state, combination in zip(state_list, combination_list):
            enhancement_builder = []
            for enhancement, num in zip(honing_level.enhancements,
                                        combination):
                if num == 0:
                    continue
                enhancement_builder.append(
                    f'{emojis.EMOJI_IDS[enhancement.item_id]}x{num}')
            if honing_level.book_id is not None and combination[-1] == 1:
                enhancement_builder.append(
                    f'{emojis.EMOJI_IDS[honing_level.book_id]}')

            if enhancement_builder:
                enhancement_str = ','.join(enhancement_builder)
            else:
                enhancement_str = '----'
            enh_builder.append(enhancement_str)

            hsr_builder.append(state.pretty_rate())
            ae_builder.append(state.pretty_artisans())

        base_level = honing_level.base_level
        summary_header = ''
        if starting_artisans_str and starting_rate_str:
            summary_header = '\n'.join(
                [starting_rate_str, starting_artisans_str, '\n'])

        material_emojis = []
        quantities = []
        prices = []
        for material in honing_level.cost:
            item_id = material.item_id
            material_emojis.append(emojis.EMOJI_IDS[item_id])
            amount = material.amount * num_hones
            quantities.append(str(round(amount, 2)))
            prices.append(
                str(
                    round(
                        amount *
                        strategy_calculator.market_client.get_unit_price(
                            item_id), 2)))

        output = {
            "content":
            "",
            "embeds": [
                {
                    "author": {
                        "name":
                        f"Hone {equipment_type_str}: +{base_level} ({ilevel}) -> "
                        f"+{base_level + 1} ({honing_level.next_item_level})",
                    },
                    "fields": [
                        {
                            "name":
                            "Summary",
                            "value":
                            f"{summary_header}"
                            f"Avg # of hones: {round(num_hones, 2)}\n"
                            f"Avg gold cost: {round(average_cost, 2)}",
                        },
                        {
                            "name": "Rate",
                            "value": '\n'.join(hsr_builder),
                            "inline": True,
                        },
                        {
                            "name": "Artisan's",
                            "value": '\n'.join(ae_builder),
                            "inline": True,
                        },
                        {
                            "name": "Use",
                            "value": '\n'.join(enh_builder),
                            "inline": True,
                        },
                    ],
                },
                {
                    "author": {
                        "name":
                        "Materials Used (Prices from lostarkmarket.online)",
                        "url":
                        "https://www.lostarkmarket.online/north-america-west/market",
                    },
                    "fields": [
                        {
                            "name": "Material",
                            "value": '\n'.join(material_emojis),
                            "inline": True,
                        },
                        {
                            "name": "Quantity",
                            "value": '\n'.join(quantities),
                            "inline": True,
                        },
                        {
                            "name": "Price",
                            "value": '\n'.join(prices),
                            "inline": True,
                        },
                    ],
                },
            ]
        }
        return output
    else:
        return f"UNKNOWN COMMAND: {command}"
