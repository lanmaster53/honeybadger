import re

# 1 upper, 1 lower, 1 special, 1 number, minimim 10 chars
PASSWORD_REGEX = r'(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*\(\)]).{10,}'
EMAIL_REGEX = r'[^@]+@[a-zA-Z\d-]+(?:\.[a-zA-Z\d-]+)+'

def is_valid_email(email):
    if not re.match(r'^{}$'.format(EMAIL_REGEX), email):
        return False
    return True

def is_valid_password(password):
    if not re.match(r'^{}$'.format(PASSWORD_REGEX), password):
        return False
    return True
