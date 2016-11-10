import binascii
import os
import uuid

def get_guid():
    return str(uuid.uuid4())

def get_token(n=40):
    return binascii.hexlify(os.urandom(n))
