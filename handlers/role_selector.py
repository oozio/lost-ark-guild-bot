from views import role_selector_view


#currently testing ability to display a button
def display():
    output = {
        "content": "",
        "components": role_selector_view.RoleSelectorView.COMPONENTS
    }
    return output

def respond(data):
    output = {
        "tts": False,
        "content": str(data), #printing out interaction data for now
        "embeds": [],
        "allowed_mentions": { "parse": [] }
    }
    return output
