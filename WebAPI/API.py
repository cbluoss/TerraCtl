from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .db import SQLALCHEMY_DATABASE_URI
import json

DEBUG = True
app = Flask(__name__)
if DEBUG:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args':{'check_same_thread': False}}
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now())
    state = db.Column(db.Text, unique=True, nullable=False)

    def __init__(self, state={}, date=datetime.now()):
        self.state = json.dumps(state)
        self.date = date


    def __repr__(self):
        return '<State at %r>' % self.date.isoformat()
