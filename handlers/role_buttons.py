from views import role_button_view


#currently testing ability to display a button
def handle():
    output = {
            "content": "",
            "components": role_button_view.RoleButtonView.COMPONENTS
    }
    return output

