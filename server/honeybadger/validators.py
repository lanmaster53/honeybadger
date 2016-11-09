import re

# anything except blank
PASSWORD_REGEX = r'.+'
EMAIL_REGEX = r'[^@]+@[a-zA-Z\d-]+(?:\.[a-zA-Z\d-]+)+'

def is_valid_email(email):
    if not re.match(r'^{}$'.format(EMAIL_REGEX), email):
        return False
    return True

def is_valid_password(password):
    if not re.match(r'^{}$'.format(PASSWORD_REGEX), password):
        return False
    return True
