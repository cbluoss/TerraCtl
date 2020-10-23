from pcf8575 import PCF8575
import board
import neopixel
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
LED_PIN        = board.D18      # GPIO pin connected to the pixels (18 uses PWM!).



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


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

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

def boot_sequence(pcf, duration= 5):
    print("boot sequence started")
    ACTIVE_SEQUENCE = True
    STATE_RELAIS = [True, True, True, True, True, True, True, True,True, True, True, True, True, True, True, True]
    pcf.port = STATE_RELAIS
    STRIP[0] = (255, 0, 0)
    time.sleep((duration))
    STRIP.fill((0, 0, 0))
    time.sleep(duration)
    ACTIVE_SEQUENCE = False

if __name__ == "__main__":
    # Initialize the IO-Expander
    pcf = PCF8575(I2C_PORT, PCF_ADDR)

    STRIP = neopixel.NeoPixel(LED_PIN, LED_COUNT)

    boot_sequence()
    # set default daylight
    set_daylight(pcf, strip)