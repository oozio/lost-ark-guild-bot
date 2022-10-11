from . import bully, compliment, role_selector, scheduler, vote

# TODO: bad that commands are defined in multiple places

CMD_DISPLAYS = {
    "role_selector": role_selector.display,
    "make_raid": scheduler.display,
    "calendar": scheduler.display,
    "vote": vote.display,
    "punch": bully.display,
    "compliment": compliment.display
}


def display(command):
    return CMD_DISPLAYS[command]
