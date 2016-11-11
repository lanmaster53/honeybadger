from flask import request, Response, session, g, redirect, url_for, render_template, jsonify, flash, abort
from honeybadger import app, db, log
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
    beacons = [b.serialized for t in g.user.targets for b in t.beacons.all()]
    #columns = beacons[0].keys()
    columns = ['id', 'target', 'agent', 'time']
    return render_template('beacons.html', columns=columns, beacons=beacons)

@app.route('/beacons/delete/<int:id>')
@login_required
def beacons_delete(id):
    beacon = Beacon.query.get(id)
    if beacon:
        db.session.delete(beacon)
        db.session.commit()
        flash('Beacon deleted.')
    else:
        flash('Invalid beacon ID.')
    return redirect(url_for('beacons'))

@app.route('/targets', methods=['GET', 'POST'])
@login_required
def targets():
    if request.method == 'POST':
        target = request.form['target']
        if target:
            t = Target(
                name=target,
                user=g.user,
            )
            db.session.add(t)
            db.session.commit()
    targets = g.user.targets.all()
    columns = ['id', 'name', 'guid', 'beacon_count']
    return render_template('targets.html', columns=columns, targets=targets)

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

@app.route('/profile/activate/<string:token>', methods=['GET', 'POST'])
def profile_activate(token):
    user = User.query.filter_by(token=token).first()
    if user and user.status == 0:
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
    users = User.query.filter(User.id != g.user.id).all()
    columns = ['email', 'role_as_string', 'status_as_string']
    return render_template('admin.html', columns=columns, users=users, roles=ROLES)

@app.route('/admin/users/init', methods=['POST'])
@login_required
@roles_required('admin')
def admin_users_init():
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

@app.route('/admin/users/<string:action>/<int:id>')
@login_required
@roles_required('admin')
def admin_users(action, id):
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

@app.route('/demo/<string:guid>')
def demo(guid):
    return render_template('demo.html', target=guid)

# control panel api views

@app.route('/api/beacons')
@login_required
def api_beacons():
    beacons = [b.serialized for t in g.user.targets for b in t.beacons.all()]
    return jsonify(beacons=beacons)

# agent api views

@app.route('/api/beacon/<target>/<agent>')
def api_beacon(target, agent):
    log.message('{}'.format('='*50))
    log.message('Target: {}'.format(target))
    log.message('Agent: {}'.format(agent))
    # check if target is valid
    if target not in [x.guid for x in g.user.targets]:
        log.error('Invalid target GUID.')
        return 'ok'
    # extract universal variables
    comment = None
    if 'comment' in request.values:
        comment = request.values['comment'].decode('base64')
    ip = request.environ['REMOTE_ADDR']
    port = request.environ['REMOTE_PORT']
    useragent = request.environ['HTTP_USER_AGENT']
    log.message('Connection from {} @ {}:{} via {}'.format(target, ip, port, agent))
    log.message('Parameters: {}'.format(request.values.to_dict()))
    log.message('User-Agent: {}'.format(useragent))
    log.message('Comment: {}'.format(comment))
    # handle tracking data
    if all (k in request.values for k in ('lat', 'lng', 'acc')):
        lat = request.values['lat']
        lng = request.values['lng']
        acc = request.values['acc']
        add_beacon(target_guid=target, agent=agent, ip=ip, port=port, useragent=useragent, comment=comment, lat=lat, lng=lng, acc=acc)
        return 'ok'
    elif all (k in request.values for k in ('os', 'data')):
        os = request.values['os']
        data = request.values['data']
        content = data.decode('base64')
        log.message('Data received:\n{}'.format(data))
        log.message('Decoded Data:\n{}'.format(content))
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
                        return 'ok'
                    else:
                        # handle zero results returned from the api
                        log.message('No results.')
                else:
                    # handle invalid data returned from the api
                    log.error('Invalid JSON object.')
            else:
                # handle unrecognized data
                log.message('No parsable WLAN data received from the agent. Unrecognized target or wireless is disabled.')
        else:
            # handle blank data
            log.message('No data received from the agent.')
    # fall back
    if get_coords_by_ip(ip):
        add_beacon(target_guid=target, agent=agent, ip=ip, port=port, useragent=useragent, comment=comment, lat=lat, lng=lng, acc='Unknown')
        return 'ok'
    else:
        # abort to 404 for obscurity
        abort(404)

# support functions

def add_beacon(*args, **kwargs):
    b = Beacon(**kwargs)
    db.session.add(b)
    db.session.commit()
    #subscriptions[g.user.guid].put({'beacons': [(b.serialized)]})
    log.message('Target location identified as Lat: {}, Lng: {}'.format(kwargs['lat'], kwargs['lng']))

def get_json(url):
    content = urllib2.urlopen(url).read()
    try:
        jsondata = json.loads(content)
        log.message('API URL used: {}'.format(url))
        log.message('JSON object retrived:\n{}'.format(jsondata))
    except ValueError as e:
        log.error('Error retrieving JSON object: {}'.format(e))
        log.error('Failed URL: {}'.format(url))
        return None
    return jsondata

def get_coords_by_ip(ip):
    log.message('Attempting to geolocate by IP.');
    url = 'http://uniapple.net/geoip/?ip={}'.format(ip)
    jsondata = get_json(url)
    if jsondata:
        lat = jsondata['latitude']
        lng = jsondata['longitude']
        return (lat, lng)
    else:
        # handle invalud json object
        log.error('Invalid JSON object. Giving up on host.')
        return None

'''@app.route('/log')
@login_required
def log():
    return render_template('log.html', beacons=[x.serialized for x in g.user.beacons])'''
