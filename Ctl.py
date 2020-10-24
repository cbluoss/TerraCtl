import logging
from time import sleep
from Lib.lighting import HW_Ctrl
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


logging.basicConfig(level=logging.DEBUG)
NOW = datetime.now()

SUNRISE_AT = datetime(NOW.year, NOW.month, NOW.day, hour=6, minute=30)
FOG_STOP_AT = datetime(NOW.year, NOW.month, NOW.day, hour=7, minute=30)
HIGHNOON_AT = datetime(NOW.year, NOW.month, NOW.day, hour=12, minute=30)
SUNSET_AT = datetime(NOW.year, NOW.month, NOW.day, hour=22, minute=0)
TRIGGER = IntervalTrigger(hours=24)

def event_sunrise(hw):
    logging.info("start sunrise")
    try:
        hw.pcf.set_socket("BLUE", True) #Pump
        hw.pcf.set_socket("GREEN", True) #Fog
    except IOError:
        logging.debug("IO-Error")
        sleep(5)
        try:
            hw.pcf.set_socket("BLUE", True) #Pump
            hw.pcf.set_socket("GREEN", True) #Fog
        except IOError:
            pass
    hw.effect_color_fade(color_from=(5,5,5), color_to=(255,60,10),  delay_ms=150, steps=512)


def event_sunset(hw):
    logging.info("start sunset")
    hw.effect_color_fade(color_from=(255,60,10), color_to=(5,5,5),  delay_ms=150, steps=512)
    try:
        hw.pcf.set_socket("BLUE", False)
        hw.pcf.reset() #shut everything off
    except IOError:
        logging.debug("IO-Error")
        sleep(5)
        try:
            hw.pcf.set_socket("BLUE", False)
            hw.pcf.reset() #shut everything off
        except IOError:
            pass
    while datetime.now.day == NOW.day:
        hw.effect_twinkle(color=(10,20,30), count=2, delay_ms=200 ,duration=60*1000, bg_color=(5,5,5))

def event_disable_fog(hw):
    logging.info("stop fog")
    hw.strip.fill((0,240,20)) #compensation for the full spec leds
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
    logging.info("High Noon (1 Hour)")
    try:
        hw.pcf.set_white(True)
        sleep(60*60)
        hw.pcf.set_white(False)
    except IOError:
        logging.debug("IO-Error")
        sleep(5)
        try:
            hw.pcf.set_socket("GREEN", False)
            hw.pcf.set_full_spec(True)
        except IOError:
            pass

if __name__ == "__main__":
    logging.info("start main")
    scheduler = BackgroundScheduler()
    scheduler.start()

    HW = HW_Ctrl()

    scheduler.add_job(func=event_sunrise,trigger=TRIGGER, next_run_time=SUNRISE_AT, name="sunrise", args=[HW,])
    scheduler.add_job(func=event_sunset, trigger=TRIGGER, next_run_time=SUNSET_AT, name="sunset", args=[HW,])
    scheduler.add_job(func=event_disable_fog, trigger=TRIGGER, next_run_time=FOG_STOP_AT, name="fog_stop", args=[HW,])
    scheduler.add_job(func=event_high_noon, trigger=TRIGGER, next_run_time=HIGHNOON_AT, name="highnoon", args=[HW,])

    logging.info(scheduler.print_jobs())

    while True:
        sleep(15)