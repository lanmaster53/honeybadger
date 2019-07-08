from honeybadger import app, logger
import requests
import json

def get_coords_from_google(aps):
    logger.info('Geolocating via Google Geolocation API.')
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(app.config['GOOGLE_API_KEY'])
    data = {"wifiAccessPoints": []}
    for ap in aps:
        data['wifiAccessPoints'].append(ap.serialized_for_google)
    data_json = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    request = requests.post(url=url, data=data_json, headers=headers)
    logger.info("Google API response: {}".format(request.content))
    jsondata = None
    try:
        jsondata = request.json()
    except ValueError as e:
        logger.error('{}.'.format(e))
    data = {'lat':None, 'lng':None, 'acc':None}
    if jsondata:
        data['acc'] = jsondata['accuracy']
        data['lat'] = jsondata['location']['lat']
        data['lng'] = jsondata['location']['lng']
    return data

def get_coords_from_ipstack(ip):
    logger.info('Geolocating via Ipstack API.')
    url = 'http://api.ipstack.com/{0}?access_key={1}'.format(ip, app.config['IPSTACK_API_KEY'])
    request = requests.get(url)
    logger.info('Ipstack API response:\n{}'.format(request.content))
    jsondata = None
    try:
        jsondata = request.json()
    except ValueError as e:
        logger.error('{}.'.format(e))

    data = {'lat':None, 'lng':None}

    # Avoid the KeyError. For some reason, a successful API call to Ipstack doesn't include
    #   the 'success' key in the json result, but a failed call does, and the value is False
    if 'success' in jsondata and not jsondata['success']:
        logger.info('Ipstack API call failed: {}'.format(jsondata['error']['type']))
        # Return with empty data so the caller knows to default to the fallback API
        return data

    if jsondata:
        data['lat'] = jsondata['latitude']
        data['lng'] = jsondata['longitude']
    return data

def get_coords_from_ipinfo(ip):
    # New fallback, ipinfo doesn't require an API key for a certain number of API calls
    logger.info('Geolocating via Ipinfo.io API.')
    url = 'https://ipinfo.io/{}'.format(ip)
    request = requests.get(url)
    logger.info('Ipinfo.io API response:\n{}'.format(request.content))
    jsondata = None
    try:
        jsondata = request.json()
    except ValueError as e:
        logger.error('{}.'.format(e))
    data = {'lat':None, 'lng':None}
    if jsondata and 'loc' in jsondata:
        data['lat'] = jsondata['loc'].split(',')[0]
        data['lng'] = jsondata['loc'].split(',')[1]
    if 'bogon' in jsondata and jsondata['bogon']:
        logger.info('Ipinfo.io cannot geolocate IP {}'.format(ip))
    return data
