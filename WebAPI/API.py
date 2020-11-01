from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args':{'check_same_thread': False}}
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
