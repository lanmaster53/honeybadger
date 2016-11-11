from honeybadger.constants import COLORS
import binascii
import os
import uuid

def get_guid():
    return str(uuid.uuid4())

def get_token(n=40):
    return binascii.hexlify(os.urandom(n))

class Logger(object):

    def error(self, s):
        print('{}[!] {}{}'.format(COLORS.R, s, COLORS.N))

    def message(self, s):
        print('{}[*] {}{}'.format(COLORS.B, s, COLORS.N))
