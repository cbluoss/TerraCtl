import logging
from time import sleep
import json
from Lib.lighting import HW_Ctrl
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

ENABLE_DB = False

if ENABLE_DB:
    logging.info("db is enabled.")
    from db import SQLALCHEMY_DATABASE_URI
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    import sqlalchemy as db
    engine = create_engine(SQLALCHEMY_DATABASE_URI)

    Base = declarative_base()


    class State(Base):
        __tablename__ = 'state'
        id = db.Column(db.Integer, primary_key=True)
        date = db.Column(db.DateTime, default=datetime.now())
        state = db.Column(db.Text, nullable=False)

        def __init__(self, state={}, date=datetime.now()):
            self.state = json.dumps(state)
            self.date = date
        def __repr__(self):
            return '<State at %r>' % self.date.isoformat()

logging.basicConfig(level=logging.DEBUG)
NOW = datetime.now()

SUNRISE_AT = datetime(NOW.year, NOW.month, NOW.day, hour=7, minute=0)
FOG_STOP_AT = datetime(NOW.year, NOW.month, NOW.day, hour=7, minute=30)
HIGHNOON_AT = datetime(NOW.year, NOW.month, NOW.day, hour=12, minute=0)
SUNSET_AT = datetime(NOW.year, NOW.month, NOW.day, hour=20, minute=15)
TRIGGER = IntervalTrigger(hours=24)

def event_sunrise(hw):
    logging.info("start sunrise")
    try:
        hw.pcf.set_12v_psu(True)
    except IOError:
        logging.debug("IO-Error")
        sleep(5)
        try:
            hw.pcf.set_12v_psu(True)
        except IOError:
            pass
    #hw.effect_color_fade(color_from=(5,5,5), color_to=(255,60,10),  delay_ms=250, steps=512)
    hw.white.effect_fade(toBrightness=0.5)

def event_sunset(hw):
    logging.info("start sunset")
    hw.white.effect_fade(fromBrightness=0.5, toBrightness=0.0)
    try:
        hw.pcf.reset() #shut everything off
    except IOError:
        logging.debug("IO-Error")
        sleep(5)
        try:
            hw.pcf.reset() #shut everything off
        except IOError:
            pass


    while 20 < datetime.now().hour or datetime.now().hour < 5:
        hw.effect_sparkle(color=(0,0,5,10), delay_ms=20, bg_color=(0,0,0,1))
        # hw.effect_sine_wave(color=(0,0,0), delay_ms=300,multi=5, cycles=1)
        pass

def event_disable_fog(hw):
    logging.info("stop fog")
    hw.strip.fill((0,0,0)) #compensation for the full spec leds not longer needed
    try:
        hw.pcf.set_socket("GREEN", False)
        hw.pcf.set_full_spec(True)
    except IOError:
        logging.debug("IO-Error")
        sleep(5)
        try:
            hw.pcf.set_socket("GREEN", False)
            hw.pcf.set_full_spec(True)
        except IOError:
            pass
def event_high_noon(hw):
    logging.info("High Noon (2 Hours)")
    try:
        hw.white.effect_fade(fromBrightness=0.5, toBrightness=1.0)
        sleep(60*60*3)
        hw.white.effect_fade(fromBrightness=1, toBrightness=0.5)
    except IOError:
        logging.debug("IO-Error")
        sleep(5)


if __name__ == "__main__":
    logging.info("start main")
    scheduler = BackgroundScheduler()
    scheduler.start()
    if ENABLE_DB:
        Session = db.orm.sessionmaker(bind=engine)
        db_session = Session()

    HW = HW_Ctrl()

    #Set some basic light. Normal lighting starts with the first event.
    HW.pcf.set_12v_psu(True)
    HW.white.set_all(0.5)

    scheduler.add_job(func=event_sunrise,trigger=TRIGGER, next_run_time=SUNRISE_AT, name="sunrise", args=[HW,])
    scheduler.add_job(func=event_sunset, trigger=TRIGGER, next_run_time=SUNSET_AT, name="sunset", args=[HW,])
    # scheduler.add_job(func=event_disable_fog, trigger=TRIGGER, next_run_time=FOG_STOP_AT, name="fog_stop", args=[HW,])
    scheduler.add_job(func=event_high_noon, trigger=TRIGGER, next_run_time=HIGHNOON_AT, name="highnoon", args=[HW,])

    logging.info(scheduler.print_jobs())

    while True:
        if ENABLE_DB:
            logging.info("write state to db")
            state = State(state=HW.get_state(), date=datetime.now())
            db_session.add(state)
            logging.info("session state: ", db_session.new)
            db_session.commit()
        try:
            HW.display.refresh_image(HW.get_DS1820_value())
        except:
            logging.info('Sensor not found')
        sleep(60)
