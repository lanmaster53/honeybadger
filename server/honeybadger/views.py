from flask import request, make_response, session, g, redirect, url_for, render_template, jsonify, flash, abort
from honeybadger import app, db
from honeybadger.parsers import parse_airport, parse_netsh, parse_iwlist
from honeybadger.validators import is_valid_email, is_valid_password
from honeybadger.decorators import login_required, roles_required
from honeybadger.constants import ROLES
from honeybadger.utils import get_token
from models import User, Target, Beacon
import json
import re
import urllib2

# request preprocessors

@app.before_request
def load_user():
    g.user = None
    if session.get('user_id'):
        g.user = User.query.filter_by(id=session["user_id"]).first()

# control panel ui views

@app.route('/')
@app.route('/index')
@login_required
def index():
    return redirect(url_for('map'))

@app.route('/map')
@login_required
def map():
    return render_template('map.html')

@app.route('/beacons')
@login_required
def beacons():
    beacons = [b.serialized for t in Target.query.all() for b in t.beacons.all()]
    columns = ['id', 'target', 'agent', 'lat', 'lng', 'acc', 'ip', 'time']
    return render_template('beacons.html', columns=columns, beacons=beacons)

@app.route('/beacon/delete/<int:id>')
@login_required
@roles_required('admin')
def beacon_delete(id):
    beacon = Beacon.query.get(id)
    if beacon:
        db.session.delete(beacon)
        db.session.commit()
        flash('Beacon deleted.')
    else:
        flash('Invalid beacon ID.')
    return redirect(url_for('beacons'))

@app.route('/targets')
@login_required
def targets():
    targets = Target.query.all()
    columns = ['id', 'name', 'guid', 'beacon_count']
    return render_template('targets.html', columns=columns, targets=targets)

@app.route('/target/add', methods=['POST'])
@login_required
@roles_required('admin')
def target_add():
    name = request.form['target']
    if name:
        target = Target(
            name=name,
        )
        db.session.add(target)
        db.session.commit()
        flash('Target added.')
    return redirect(url_for('targets'))

@app.route('/target/delete/<string:guid>')
@login_required
@roles_required('admin')
def target_delete(guid):
    target = Target.query.filter_by(guid=guid).first()
    if target:
        db.session.delete(target)
        db.session.commit()
        flash('Target deleted.')
    else:
        flash('Invalid target GUID.')
    return redirect(url_for('targets'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if g.user.check_password(request.form['current_password']):
            new_password = request.form['new_password']
            if new_password == request.form['confirm_password']:
                if is_valid_password(new_password):
                    g.user.password = new_password
                    db.session.add(g.user)
                    db.session.commit()
                    flash('Profile updated.')
                else:
                    flash('Password does not meet complexity requirements.')
            else:
                flash('Passwords do not match.')
        else:
            flash('Incorrect current password.')
    return render_template('profile.html', user=g.user)

# use an alternate route for reset as long as the logic is similar to init
@app.route('/password/reset/<string:token>', methods=['GET', 'POST'], endpoint='password_reset')
@app.route('/profile/activate/<string:token>', methods=['GET', 'POST'])
def profile_activate(token):
    user = User.query.filter_by(token=token).first()
    if user and user.status in (0, 3):
        if request.method == 'POST':
            new_password = request.form['new_password']
            if new_password == request.form['confirm_password']:
                if is_valid_password(new_password):
                    user.password = new_password
                    user.status = 1
                    user.token = None
                    db.session.add(user)
                    db.session.commit()
                    flash('Profile activated.')
                    return redirect(url_for('login'))
                else:
                    flash('Password does not meet complexity requirements.')
            else:
                flash('Passwords do not match.')
        return render_template('profile_activate.html', user=user)
    # abort to 404 for obscurity
    abort(404)

@app.route('/admin')
@login_required
@roles_required('admin')
def admin():
    users = User.query.all()
    columns = ['email', 'role_as_string', 'status_as_string']
    return render_template('admin.html', columns=columns, users=users, roles=ROLES)

@app.route('/admin/user/init', methods=['POST'])
@login_required
@roles_required('admin')
def admin_user_init():
    email = request.form['email']
    if is_valid_email(email):
        if not User.query.filter_by(email=email).first():
            user = User(
                email=email,
                token=get_token(),
            )
            db.session.add(user)
            db.session.commit()
            flash('User initialized.')
        else:
            flash('Username already exists.')
    else:
        flash('Invalid email address.')
    # send notification to user
    return redirect(url_for('admin'))

@app.route('/admin/user/<string:action>/<int:id>')
@login_required
@roles_required('admin')
def admin_user(action, id):
    user = User.query.get(id)
    if user:
        if user != g.user:
            if action == 'activate' and user.status == 2:
                user.status = 1
                db.session.add(user)
                db.session.commit()
                flash('User activated.')
            elif action == 'deactivate' and user.status == 1:
                user.status = 2
                db.session.add(user)
                db.session.commit()
                flash('User deactivated.')
            elif action == 'reset' and user.status == 1:
                user.status = 3
                user.token = get_token()
                db.session.add(user)
                db.session.commit()
                flash('User reset.')
            elif action == 'delete':
                db.session.delete(user)
                db.session.commit()
                flash('User deleted.')
            else:
                flash('Invalid user action.')
        else:
            flash('Self-modification denied.')
    else:
        flash('Invalid user ID.')
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # redirect to home if already logged in
    if session.get('user_id'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])
        if user and user.status == 1 and user.check_password(request.form['password']):
            session['user_id'] = user.id
            flash('You have successfully logged in.')
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/demo/<string:guid>', methods=['GET', 'POST'])
def demo(guid):
    text = request.values.get('text')
    key = request.values.get('key') or ''
    if g.user.check_password(key):
        if text and 'alert(' in text:
            text = 'Congrats! You entered: {}'.format(text)
        else:
            text = 'Nope. Try again.'
    else:
        text = 'Incorrect password.'
    nonce = generate_nonce(24)
    response = make_response(render_template('demo.html', target=guid, text=text, nonce=nonce))
    response.headers['X-XSS-Protection'] = '0'#'1; report=https://hb.lanmaster53.com/api/beacon/{}/X-XSS-Protection'.format(guid)
    uri = url_for('api_beacon', target=guid, agent='Content-Security-Policy')
    response.headers['Content-Security-Policy-Report-Only'] = 'script-src \'nonce-{}\'; report-uri {}'.format(nonce, uri)
    return response

# control panel api views

@app.route('/api/beacons')
@login_required
def api_beacons():
    beacons = [b.serialized for t in Target.query.all() for b in t.beacons.all()]
    return jsonify(beacons=beacons)

# agent api views

@app.route('/api/beacon/<target>/<agent>', methods=['GET', 'POST'])
def api_beacon(target, agent):
    app.logger.info('{}'.format('='*50))
    app.logger.info('Target: {}'.format(target))
    app.logger.info('Agent: {}'.format(agent))
    # check if target is valid
    if target not in [x.guid for x in Target.query.all()]:
        app.logger.error('Invalid target GUID.')
        abort(404)
    # extract universal parameters
    comment = None
    if 'comment' in request.values:
        comment = request.values['comment'].decode('base64')
    ip = request.environ['REMOTE_ADDR']
    port = request.environ['REMOTE_PORT']
    useragent = request.environ['HTTP_USER_AGENT']
    app.logger.info('Connection from {} @ {}:{} via {}'.format(target, ip, port, agent))
    app.logger.info('Parameters: {}'.format(request.values.to_dict()))
    app.logger.info('User-Agent: {}'.format(useragent))
    app.logger.info('Comment: {}'.format(comment))
    # process known coordinates
    if all(k in request.values for k in ('lat', 'lng', 'acc')):
        lat = request.values['lat']
        lng = request.values['lng']
        acc = request.values['acc']
        add_beacon(target_guid=target, agent=agent, ip=ip, port=port, useragent=useragent, comment=comment, lat=lat, lng=lng, acc=acc)
        abort(404)
    # process wireless survey
    elif all(k in request.values for k in ('os', 'data')):
        os = request.values['os']
        data = request.values['data']
        content = data.decode('base64')
        app.logger.info('Data received:\n{}'.format(data))
        app.logger.info('Decoded Data:\n{}'.format(content))
        if data:
            aps = None
            if re.search('^mac os x', os.lower()):
                aps = parse_airport(content)
            elif re.search('^windows', os.lower()):
                aps = parse_netsh(content)
            elif re.search('^linux', os.lower()):
                aps = parse_iwlist(content)
            # handle recognized data
            if aps:
                url = 'https://maps.googleapis.com/maps/api/browserlocation/json?browser=firefox&sensor=true'
                query = '&wifi=mac:{}|ssid:{}|ss:{}'
                for ap in aps:
                    url += query.format(ap[1], ap[0], ap[2])
                jsondata = get_json(url[:1900])
                if jsondata:
                    if jsondata['status'] != 'ZERO_RESULTS':
                        acc = jsondata['accuracy']
                        lat = jsondata['location']['lat']
                        lng = jsondata['location']['lng']
                        add_beacon(target_guid=target, agent=agent, ip=ip, port=port, useragent=useragent, comment=comment, lat=lat, lng=lng, acc=acc)
                        abort(404)
                    else:
                        # handle zero results returned from the api
                        app.logger.info('No results.')
                else:
                    # handle invalid data returned from the api
                    app.logger.error('Invalid JSON object.')
            else:
                # handle unrecognized data
                app.logger.info('No parsable WLAN data received from the agent. Unrecognized target or wireless is disabled.')
        else:
            # handle blank data
            app.logger.info('No data received from the agent.')
    # process ip geolocation (fallback)
    lat, lng = get_coords_by_ip(ip)
    if all((lat, lng)):
        add_beacon(target_guid=target, agent=agent, ip=ip, port=port, useragent=useragent, comment=comment, lat=lat, lng=lng, acc='Unknown')
        abort(404)
    # default abort to 404 for obscurity
    abort(404)

# support functions

def add_beacon(*args, **kwargs):
    b = Beacon(**kwargs)
    db.session.add(b)
    db.session.commit()
    #subscriptions[g.user.guid].put({'beacons': [(b.serialized)]})
    app.logger.info('Target location identified as Lat: {}, Lng: {}'.format(kwargs['lat'], kwargs['lng']))

def get_json(url):
    content = urllib2.urlopen(url).read()
    try:
        jsondata = json.loads(content)
        app.logger.info('API URL used: {}'.format(url))
        app.logger.info('JSON object retrived:\n{}'.format(jsondata))
    except ValueError as e:
        app.logger.error('Error retrieving JSON object: {}'.format(e))
        app.logger.error('Failed URL: {}'.format(url))
        return None
    return jsondata

def get_coords_by_ip(ip):
    app.logger.info('Attempting to geolocate by IP.')
    url = 'http://uniapple.net/geoip/?ip={}'.format(ip)
    jsondata = get_json(url)
    if jsondata:
        lat = jsondata['latitude']
        lng = jsondata['longitude']
        return lat, lng
    else:
        # handle invalid json object
        app.logger.error('Invalid JSON object. Giving up on host.')
        return None, None

import base64
import os

def generate_nonce(n):
    nonce = os.urandom(n)
    return base64.b64encode(nonce).decode()
