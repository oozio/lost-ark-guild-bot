from constants import honing_data as hd_const
from utils.lost_ark import honing_strategy


def handle(command, cmd_input):
    if command == "hone":
        # dunno how to put in unlimited # of autocompletable options
        equipment_type = hd_const.EquipmentType.WEAPON if cmd_input[
            'is_weapon'] else hd_const.EquipmentType.ARMOR
        ilevel = cmd_input['current_item_level']
        level_id = ilevel, equipment_type
        if level_id not in hd_const.HONES_DICT:
            raise NotImplementedError('Zethorix')
        honing_level = hd_const.HONES_DICT[level_id]
        starting_rate = cmd_input['base_rate'] / \
            100 if 'base_rate' in cmd_input else None
        starting_artisans = cmd_input['artisans_energy'] / \
            100 if 'artisans_energy' in cmd_input else 0

        num_hones, average_cost, combination_list, state_list = \
            honing_strategy.get_honing_strategy(
                honing_level,
                starting_rate=starting_rate,
                starting_artisans=starting_artisans
            )

        output = [
            f'Average number of hones: {round(num_hones, 2)}',
            f'Average gold cost: {round(average_cost, 2)}\n'
        ]
        for state, combination in zip(state_list, combination_list):
            enhancement_builder = []
            for enhancement, num in zip(honing_level.enhancements,
                                        combination):
                if num == 0:
                    continue
                enhancement_builder.append(
                    f'Use {enhancement.item_id} (x{num})')
            if honing_level.book_id is not None and combination[-1] == 1:
                enhancement_builder.append(f'Use {honing_level.book_id}')

            if enhancement_builder:
                enhancement_str = ', '.join(enhancement_builder)
            else:
                enhancement_str = 'No Enhancement Materials'
            output.append(f'({state.prettify()}) -> ({enhancement_str})')
        return '\n'.join(output)
    else:
        return f"UNKNOWN COMMAND: {command}"
