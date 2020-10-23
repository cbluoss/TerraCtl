from pcf8575 import PCF8575
from rpi_ws281x import *
import time

# Main Program managing the terrarium systems.
# Designed to run on:
# * 1 raspberry pi (Zero)
# * 1 PCF8575 16Port IO-Expander via i2c controlling 16 Relais (4x 230V power sockets, a 3.3v psu for some high power leds, 3 sets of LEDs + 2 general purpose 5V lines, 2 currently not in use)
# * a 46 WS2812b Strip
# * 2 DHT22 (not yet connected)
# * a SSD1306 128x64 oled display (not yet connected)
# Default state: everything off except the pi.
#
# I2C configuration (currently just the IO expander)
I2C_PORT = 1
PCF_ADDR = 0x20
# actually  wrong side would be turned on (the 230c relais)
# True = off (True|High is default at start)
# pcf.port =  [True, True, True, True, True, True, True, True, False, False, False, False, False, False, False, False]

# LED strip configuration:
LED_COUNT      = 46      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

#EVENT Times, Format (HOUR,MINUTES) (local time)
TIME_SUNRISE = (6,20)
TIME_SUNSET = (23,0)
TIME_HIGH_NOON = (13,0)

# Duration (in seconds)
DURATION_HIGH_NOON = 60*60

#Is there already an active sequence?
ACTIVE_SEQUENCE = False

STATE_3V = False
STATE_W_LEFT = False
STATE_W_RIGHT = False
STATE_FULL_SPEC = False

STATE_RELAIS = [True, True, True, True, True, True, True, True,True, True, True, True, True, True, True, True]
# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def set_3v_psu(pcf, state=False):
    # Libs behaves strangely. pcf.port[x] = True|False is quite unpredictable. Pushing the whole 16Element list works though
    # [7] is the need relais
    if state:
        STATE_RELAIS[7] = False
        pcf.port = STATE_RELAIS
    else:
        STATE_RELAIS[7] = True
        pcf.port = STATE_RELAIS

def set_white_left(pcf, state=False):
    # Libs behaves strangely. pcf.port[x] = True|False is quite unpredictable. Pushing the whole 16Element list works though
    # [6] is the need relais
    if state:
        set_3v_psu(pcf, True)
        STATE_RELAIS[6] = False
        pcf.port = STATE_RELAIS
    else:
        STATE_RELAIS[6] = True
        pcf.port = STATE_RELAIS

def set_white_right(pcf, state=False):
    # Libs behaves strangely. pcf.port[x] = True|False is quite unpredictable. Pushing the whole 16Element list works though
    # [5] is the need relais
    if state:
        set_3v_psu(pcf, True)
        STATE_RELAIS[5] = False
        pcf.port = STATE_RELAIS
    else:
        STATE_RELAIS[5] = True
        pcf.port = STATE_RELAIS

def set_white(pcf, state=False):
    if state:
        set_white_left(pcf,True)
        set_white_right(pcf,True)
    else:
        set_white_left(pcf,False)
        set_white_right(pcf,False)

def set_full_spec(pcf, state=False):
    # Libs behaves strangely. pcf.port[x] = True|False is quite unpredictable. Pushing the whole 16Element list works though
    # [4] is the need relais
    if state:
        set_3v_psu(pcf, True)
        STATE_RELAIS[4] = False
        pcf.port = STATE_RELAIS
    else:
        STATE_RELAIS[4] = True
        pcf.port = STATE_RELAIS

def set_daylight(pcf, strip):
    print("set daylight with 60,220,140 + full spec")
    # More or less white impression with the full spectrum leds on
    colorWipe(strip, Color(60,220,140), 10)
    set_full_spec(pcf, True)

def boot_sequence(strip, duration= 5):
    print("boot sequence started")
    ACTIVE_SEQUENCE = True
    rainbow(strip)
    time.sleep((duration))
    colorWipe(strip, Color(0,0,0), 10)
    time.sleep(5)
    ACTIVE_SEQUENCE = False

if __name__ == "__main__":
    # Initialize the IO-Expander
    pcf = PCF8575(I2C_PORT, PCF_ADDR)

    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    boot_sequence(strip)
    # set default daylight
    set_daylight(pcf, strip)