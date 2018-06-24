import binascii
import os
import base64
import uuid

def generate_guid():
    return str(uuid.uuid4())

def generate_token(n=40):
    return binascii.hexlify(os.urandom(n))

def generate_nonce(n):
    return base64.b64encode(os.urandom(n)).decode()

from honeybadger.constants import CHANNELS

def freq2channel(freq):
    for channel in CHANNELS:
        if freq in CHANNELS[channel]:
            return channel

from honeybadger.models import Log
from honeybadger import db

class Logger(object):

    def _log(self, l, s):
        log = Log(
            level=l,
            message=s,
        )
        db.session.add(log)
        db.session.commit()

    def debug(self, s):
        self._log(10, s)

    def info(self, s):
        self._log(20, s)

    def warn(self, s):
        self._log(30, s)

    def error(self, s):
        self._log(40, s)

    def critical(self, s):
        self._log(50, s)
