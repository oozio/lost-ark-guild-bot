import requests
from bs4 import BeautifulSoup
from utils import aws_lambda, discord

SERVER = 'Bergstrom'

# Looks through all server statuses, looking for the SERVER keyword, then goes up
# a level and looks for MAINTENANCE_CLASS, which is the class assigned to the
# maintenance status icon.
#
# Would need to observe the CSS class of other statuses to handle them, but we
# don't actually care since all we want to know is if maintenance is over.
def is_maintenance():
    MAINTENANCE_CLASS = 'ags-ServerStatus-content-responses-response-server-status--maintenance'

    response = requests.get('https://www.playlostark.com/en-us/support/server-status', timeout=15)
    html = BeautifulSoup(response.text, 'html.parser')

    statuses = html.select('.ags-ServerStatus-content-responses > div.ags-ServerStatus-content-responses-response')

    server = None
    for region_statuses in statuses:
        servers = region_statuses.select('.ags-ServerStatus-content-responses-response-server-name')
        for s in servers:
            if s.text.strip() == SERVER:
                server = s
                break
        if server:
            break

    if server:
        status = server.parent.select('.ags-ServerStatus-content-responses-response-server-status')[0]
        if MAINTENANCE_CLASS in status.attrs['class']:
            return True
        else:
            return False
    else:
        return False

# Just do an immediate response for now
def handle(command, user_id, channel_id):
    if command == "server_status":
        if is_maintenance():
            return "Server is under maintenance!"
        else:
            return "Server is up!"
    elif command == "maintenance_watch":
        if is_maintenance():
            aws_lambda.enable_rule('Timer')
            return "Watching until server is up..."
        else:
            aws_lambda.disable_rule('Timer')
            return "Server is up!"
    else:
        return f"UNKNOWN COMMAND: {command}"


# We got poked by the timer
def handle_timer():
    if is_maintenance():
        return
    else:
        aws_lambda.disable_rule('Timer')
        # Post in bot-testing for now
        discord.post_message_in_channel('985659954532847646', 'Server maintenance is over!')
