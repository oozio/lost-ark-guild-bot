import requests
from bs4 import BeautifulSoup

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
    if is_maintenance():
        return "Server is under maintenance!"
    else:
        return "Server is up!"
