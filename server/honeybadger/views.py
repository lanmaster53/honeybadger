from flask import request, make_response, session, g, redirect, url_for, render_template, jsonify, flash, abort
from flask_cors import cross_origin
from honeybadger import app, db, logger
from honeybadger.processors import process_known_coords, process_wlan_survey, process_ip, process_json
from honeybadger.validators import is_valid_email, is_valid_password
from honeybadger.decorators import login_required, roles_required
from honeybadger.constants import ROLES
from honeybadger.utils import generate_token, generate_nonce
from honeybadger.models import User, Target, Beacon, Log
import os
from base64 import b64decode as b64d

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
    return render_template('map.html', key=app.config['GOOGLE_API_KEY'])

@app.route('/beacons')
@login_required
def beacons():
    beacons = [b.serialized for t in Target.query.all() for b in t.beacons.all()]
    columns = ['id', 'target', 'agent', 'lat', 'lng', 'acc', 'ip', 'created']
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
                token=generate_token(),
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
                user.token = generate_token()
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
    text = None
    if request.method == 'POST':
        text = request.values['text']
        key = request.values['key']
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

@app.route('/log')
@login_required
def log():
    # hidden capability to clear logs
    if request.values.get('clear'):
        Log.query.delete()
        db.session.commit()
        return redirect(url_for('log'))
    content = ''
    logs = Log.query.order_by(Log.created).all()
    for log in logs:
        content += '[{}] [{}] {}{}'.format(log.created_as_string, log.level_as_string, log.message, os.linesep)
    return render_template('log.html', content=content)

# control panel api views

@app.route('/api/beacons')
@login_required
def api_beacons():
    beacons = [b.serialized for t in Target.query.all() for b in t.beacons.all()]
    return jsonify(beacons=beacons)

# agent api views

@app.route('/api/beacon/<target>/<agent>', methods=['GET', 'POST'])
@cross_origin()
def api_beacon(target, agent):
    logger.info('{}'.format('='*50))
    data = {'target': target, 'agent': agent}
    logger.info('Target: {}'.format(target))
    logger.info('Agent: {}'.format(agent))
    # check if target is valid
    if target not in [x.guid for x in Target.query.all()]:
        logger.error('Invalid target GUID.')
        abort(404)
    # extract universal parameters
    #comment = request.values.get('comment', '').decode('base64') or None
    comment = b64d(request.values.get('comment', '')) or None
    ip = request.environ['REMOTE_ADDR']
    port = request.environ['REMOTE_PORT']
    useragent = request.environ['HTTP_USER_AGENT']
    data.update({'comment': comment, 'ip': ip, 'port': port, 'useragent': useragent})
    logger.info('Connection from {} @ {}:{} via {}'.format(target, ip, port, agent))
    logger.info('Parameters: {}'.format(request.values.to_dict()))
    logger.info('User-Agent: {}'.format(useragent))
    logger.info('Comment: {}'.format(comment))
    data.update(request.values.to_dict())
    # process json payloads
    if request.json:
        if process_json(data, request.json):
            abort(404)
    # process known coordinates
    if all(k in data for k in ('lat', 'lng', 'acc')):
        if process_known_coords(data):
            abort(404)
    # process wireless survey
    elif all(k in data for k in ('os', 'data')):
        if process_wlan_survey(data):
            abort(404)
    # process ip geolocation (includes fallback)
    process_ip(data)
    abort(404)
