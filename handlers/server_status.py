import requests
from bs4 import BeautifulSoup
from utils import aws_lambda, discord

SERVER = 'Bergstrom'
BOT_TESTING = '985659954532847646'
MAIN = '951040587266662402'
SPAM = '951409442593865748'

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
        # This indicates the page didn't respond or did not fully load, which
        # happens at certain points of the server maintenance, so we return True
        return True

# Just do an immediate response for now
def handle(command, user_id, channel_id):
    if command == "server_status":
        if is_maintenance():
            return "Server is under maintenance!"
        else:
            return "Server is up!"
    elif command == "maintenance_watch":
        if is_maintenance():
            try:
                aws_lambda.enable_rule('Timer')
            except Exception as error:
                print(error)

            return "Watching until server is up..."
        else:
            try:
                aws_lambda.disable_rule('Timer')
            except Exception as error:
                print(error)

            return "Server is up!"
    else:
        return f"UNKNOWN COMMAND: {command}"


# We got poked by the timer
def handle_timer():
    if is_maintenance():
        print("Still under maintenance!")
        return
    else:
        print("Maintenance is over!")

        try:
            aws_lambda.disable_rule('Timer')
        except Exception as error:
            print(error)

        # Post in other-spam for now
        # TODO: Collect list of interested parties and ping them specifically
        discord.post_message_in_channel(SPAM, '@here Server maintenance is over!', ephemeral=False)
