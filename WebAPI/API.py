from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
from db import SQLALCHEMY_DATABASE_URI
import json

TEST_DB = False
app = Flask(__name__)
ma = Marshmallow(app)

if TEST_DB:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args':{'check_same_thread': False}}
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now())
    state = db.Column(db.Text, nullable=False)

    def __init__(self, state={}, date=datetime.now()):
        self.state = json.dumps(state)
        self.date = date
    def __repr__(self):
        return '<State at %r>' % self.date.isoformat()

    @property
    def state_dict(self):
        return json.loads(self.state)
class StateSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ("id", "date", "state_dict")

state_schema = StateSchema()
states_schema = StateSchema(many=True)

@app.route('/state/all')
def ctrl_states():
    all_states = State.query.all()
    return json.dumps(states_schema.dump(all_states))

@app.route("/state/<id>")
def ctrl_state_detail(id):
    state = State.query.get(id)
    return json.dumps(state_schema.dump(state))