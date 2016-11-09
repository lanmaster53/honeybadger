from flask import g, redirect, url_for
from functools import wraps

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if g.user:
            return func(*args, **kwargs)
        return redirect(url_for('login'))
    return decorated_view
