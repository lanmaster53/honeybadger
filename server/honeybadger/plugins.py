from honeybadger import app, logger
import urllib
from urllib.request import urlopen
import json

def get_coords_from_google(aps):
    logger.info('Geolocating via Google Geolocation API.')
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(app.config['GOOGLE_API_KEY'])
    data = {"wifiAccessPoints": []}
    for ap in aps:
        data['wifiAccessPoints'].append(ap.serialized_for_google)
    data_json = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    request = urllib.request.Request(url, data="{}".encode(), headers=headers)
    print(data_json)
    response = urlopen(request)
    content = response.read()
    logger.info("Google API response: {}".format(content))
    jsondata = None
    try:
        jsondata = json.loads(content)
    except ValueError as e:
        logger.error('{}.'.format(e))
    data = {'lat':None, 'lng':None, 'acc':None}
    if jsondata:
        data['acc'] = jsondata['accuracy']
        data['lat'] = jsondata['location']['lat']
        data['lng'] = jsondata['location']['lng']
    return data

def get_external_ip(ip):
    logger.info('Resolving external IP via Ipify API.')
    url = "https://api.ipify.org"
    content = urlopen(url).read()
    return content.decode()

def get_coords_from_ipstack(ip):
    logger.info('Geolocating via Ipstack API.')
    url = 'http://api.ipstack.com/{0}?access_key={1}'.format(get_external_ip(ip), app.config['IPSTACK_API_KEY'])
    content = urlopen(url).read()
    logger.info('Ipstack API response:\n{}'.format(content))
    jsondata = None
    try:
        jsondata = json.loads(content)
    except ValueError as e:
        logger.error('{}.'.format(e))
    data = {'lat':None, 'lng':None}
    if jsondata:
        data['lat'] = jsondata['latitude']
        data['lng'] = jsondata['longitude']
    return data
