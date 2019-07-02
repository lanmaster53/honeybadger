from honeybadger import db, logger
from honeybadger.models import Beacon
from honeybadger.parsers import parse_airport, parse_netsh, parse_iwlist, parse_google
from honeybadger.plugins import get_coords_from_google, get_coords_from_ipstack, get_coords_from_ipinfo
from base64 import b64decode as b64d
import re

def add_beacon(*args, **kwargs):
    b = Beacon(**kwargs)
    db.session.add(b)
    db.session.commit()
    logger.info('Target location identified as Lat: {}, Lng: {}'.format(kwargs['lat'], kwargs['lng']))

def process_json(data, jsondata):
    logger.info('Processing JSON data.')
    logger.info('Data received:\n{}'.format(jsondata))
    # process Google device data
    if jsondata.get('scan_results'):
        aps = parse_google(jsondata['scan_results'])
        if aps:
            logger.info('Parsed access points: {}'.format(aps))
            coords = get_coords_from_google(aps)
            if all([x for x in coords.values()]):
                add_beacon(
                    target_guid=data['target'],
                    agent=data['agent'],
                    ip=data['ip'],
                    port=data['port'],
                    useragent=data['useragent'],
                    comment=data['comment'],
                    lat=coords['lat'],
                    lng=coords['lng'],
                    acc=coords['acc'],
                )
                return True
            else:
                logger.error('Invalid coordinates data.')
        else:
            # handle empty data
            logger.info('No AP data received.')
    else:
        # handle unrecognized data
        logger.info('Unrecognized data received from the agent.')

def process_known_coords(data):
    logger.info('Processing known coordinates.')
    add_beacon(
        target_guid=data['target'],
        agent=data['agent'],
        ip=data['ip'],
        port=data['port'],
        useragent=data['useragent'],
        comment=data['comment'],
        lat=data['lat'],
        lng=data['lng'],
        acc=data['acc'],
    )
    return True

def process_wlan_survey(data):
    logger.info('Processing wireless survey data.')
    os = data['os']
    _data = data['data']
    #content = _data.decode('base64')
    content = b64d(_data).decode()
    logger.info('Data received:\n{}'.format(_data))
    logger.info('Decoded Data:\n{}'.format(content))
    if _data:
        aps = []
        if re.search('^mac os x', os.lower()):
            aps = parse_airport(content)
        elif re.search('^windows', os.lower()):
            aps = parse_netsh(content)
        elif re.search('^linux', os.lower()):
            aps = parse_iwlist(content)
        # handle recognized data
        if aps:
            logger.info('Parsed access points: {}'.format(aps))
            coords = get_coords_from_google(aps)
            if all([x for x in coords.values()]):
                add_beacon(
                    target_guid=data['target'],
                    agent=data['agent'],
                    ip=data['ip'],
                    port=data['port'],
                    useragent=data['useragent'],
                    comment=data['comment'],
                    lat=coords['lat'],
                    lng=coords['lng'],
                    acc=coords['acc'],
                )
                return True
            else:
                logger.error('Invalid coordinates data.')
        else:
            # handle unrecognized data
            logger.info('No parsable WLAN data received.')
    else:
        # handle blank data
        logger.info('No data received from the agent.')
    return False

def process_ip(data):
    logger.info('Processing IP address.')
    coords = get_coords_from_ipstack(data['ip'])
    if not coords:
        logger.info('Using fallback API.')
        coords = get_coords_from_ipinfo(data['ip'])

    if all([x for x in coords.values()]):
        add_beacon(
            target_guid=data['target'],
            agent=data['agent'],
            ip=data['ip'],  # Replace with get_external_ip(data['ip'])?
            port=data['port'],
            useragent=data['useragent'],
            comment=data['comment'],
            lat=coords['lat'],
            lng=coords['lng'],
            acc='Unknown',
        )
        return True
    else:
        logger.error('Invalid coordinates data.')
    return False
