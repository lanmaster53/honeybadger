import json
import urllib2

from honeybadger import log

GOOGLE_API_KEY = ''
GOOGLE_API_URL = "https://www.googleapis.com/geolocation/v1/geolocate?key={}".format(GOOGLE_API_KEY)

def google_api(data):
    """Make a request to the google maps api for given data

    :arg data: dictionary containing data to send to google
    """
    data_json = json.dumps(data)
    data_length = len(data_json)
    req_headers = {
        'Content-Type': 'application/json',
        'Contnet-Length': data_length
    }
    request = urllib2.Request(GOOGLE_API_URL, data_json, req_headers)
    transmission = urllib2.urlopen(request)
    response = transmission.read()
    transmission.close()
    log.message("Google API Response: {}".format(response))
    try:
        return json.loads(response)

    except Exception as e:
        log.message("Could not parse json response: {}".format(e.message))

    return None