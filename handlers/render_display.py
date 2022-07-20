from . import role_selector, scheduler

# TODO: bad that commands are defined in multiple places

CMD_DISPLAYS = {
    "role_selector": role_selector.display,
    "scheduler": scheduler.display
}
    

def display(command):
    return CMD_DISPLAYS[command]
