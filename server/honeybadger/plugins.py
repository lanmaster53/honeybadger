from honeybadger import app, logger
import urllib2
import json

def get_coords_from_google(aps):
    logger.info('Geolocating via Google Geolocation API.')
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(app.config['GOOGLE_API_KEY'])
    data = {"wifiAccessPoints": []}
    for ap in aps:
        data['wifiAccessPoints'].append(ap.serialized_for_google)
    data_json = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    request = urllib2.Request(url, data=data_json, headers=headers)
    response = urllib2.urlopen(request)
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

def get_coords_from_uniapple(ip):
    logger.info('Geolocating via Uniapple API.')
    url = 'http://uniapple.net/geoip/?ip={}'.format(ip)
    content = urllib2.urlopen(url).read()
    logger.info('Uniapple API response:\n{}'.format(content))
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
