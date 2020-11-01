from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, unique=True, nullable=False)
    state = db.Column(db.Text, unique=True, nullable=False)

    def __repr__(self):
        return '<State at %r>' % self.date

