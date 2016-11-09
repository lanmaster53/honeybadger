from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os

basedir = '/tmp'#os.path.abspath(os.path.dirname(__file__))

# configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.db')
DEBUG = True
SECRET_KEY = 'development key'
SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config.from_object(__name__)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

def initdb():
    db.create_all()
    print 'Database initialized.'

def dropdb():
    db.drop_all()
    print 'Database dropped.'

import models
import views
