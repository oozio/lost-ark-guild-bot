from views import role_selector_view


#currently testing ability to display a button
def display(info):
    output = {
        "content": "<under construction>",
        "components": role_selector_view.RoleSelectorView.COMPONENTS
    }

    return output

def respond(data):
    output = {
        "content": "Congrats! we pressed a button"
    }

    return output
