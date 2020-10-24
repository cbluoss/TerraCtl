import logging
from Lib.lighting import HW_Ctrl
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


logging.basicConfig(level=logging.DEBUG)
NOW = datetime.now()

SUNRISE_AT = datetime(NOW.year, NOW.month, NOW.day, hour=6, minute=30)
SUNSET_AT = datetime(NOW.year, NOW.month, NOW.day, hour=22, minute=0)
TRIGGER = IntervalTrigger(hours=24)

def event_sunrise(hw):
    logging.info("start sunrise")
    hw.effect_color_fade(color_from=(5,5,5), color_to=(255,60,10),  delay_ms=150, steps=255)
    hw.pcf.set_socket("BLUE", True)

def event_sunset(hw):
    logging.info("start sunset")
    hw.effect_color_fade(color_from=(255,60,10), color_to=(5,5,5),  delay_ms=150, steps=255)
    hw.pcf.set_socket("BLUE", False)


if __name__ == "__main__":
    logging.info("start main")
    scheduler = BackgroundScheduler()
    scheduler.start

    HW = HW_Ctrl()

    scheduler.add_job(func=event_sunrise,trigger=TRIGGER, next_run_time=SUNRISE_AT, name="sunrise", args=[HW,])
    scheduler.add_job(func=event_sunset, trigger=TRIGGER, next_run_time=SUNSET_AT, name="sunset", args=[HW,])

    logging.info(scheduler.print_jobs())