from .pcf8575 import PCF8575
import board
import neopixel
import time
import math
from random import randint

I2C_PORT = 1
PCF_ADDR = 0x20

LED_COUNT      = 46      # Number of LED pixels.
LED_PIN        = board.D18      # GPIO pin connected to the pixels (18 uses PWM!).

class PCF_Wrapper:
    def __init__(self, i2c_port=I2C_PORT, pcf_addr=PCF_ADDR):
        # In this case the 16 relais are as follows:
        # Caution: True is OFF in Hardware | False is ON
        # 0:  not in use
        # 1:  not in use
        # 2:  5v toggle
        # 3:  5v toggle
        # 4:  Full Spec LEDs
        # 5:  White LEDs Right
        # 6:  White LEDs Left
        # 7:  3.3v PSU
        # 8:  GREEN Socket
        # 9:  GREEN Socket
        # 10: Blue Socket
        # 11: BLUE Socket
        # 12: YELLOW Socket
        # 13: YELLOW Socket
        # 14: RED Socket
        # 15: RED Socket

        self.instance = PCF8575(i2c_port, pcf_addr)
        # all off!
        self.reset()

    def reset(self):
        self.state = [True, True, True, True, True, True, True, True,True, True, True, True, True, True, True, True]
        self.instance.port = self.state
        
    def all_on(self):
        self.state = [False, False, False, False, False, False, False, False,False, False, False, False, False, False, False, False]
        self.instance.port = self.state
    def set_3v_psu(self, state=True):
        """Set state for the 3.3v PSU"""
        # default is off
        self.state[7] = state
        self.instance.port = self.state

    def set_white_left(self, state=False):
        """Set state for left white LEDs"""
        if state:
            self.state[7] = False
            self.state[6] = False
            self.instance.port = self.state
        else:
            # Be aware: PSU won't be powered off
            self.state[6] = True
            self.instance.port = self.state

    def set_white_right(self, state=False):
        """Set state for right white LEDs"""
        if state:
            self.state[7] = False
            self.state[5] = False
            self.instance.port = self.state
        else:
            # Be aware: PSU won't be powered off
            self.state[5] = True
            self.instance.port = self.state

    def set_white(self, state=False):
        """Set state for all white LEDs"""
        if state:
            self.set_white_left(True)
            self.set_white_right(True)
        else:
            self.set_white_left(False)
            self.set_white_right(False)

    def set_full_spec(self, state=False):
        """Set state for the full spectrum LEDs"""
        if state:
            self.state[7] = False
            self.state[4] = False
            self.instance.port = self.state
        else:
            # Be aware: PSU won't be powered off
            self.state[4] = True
            self.instance.port = self.state

    def set_socket(self, socket, state=False):
        if socket == "RED":
            self.state[14] = not state
            self.state[15] = not state
        elif socket == "YELLOW":
            self.state[12] = not state
            self.state[13] = not state
        elif socket == "BLUE":
            self.state[10] = not state
            self.state[11] = not state
        elif socket == "GREEN":
            self.state[8] = not state
            self.state[9] = not state
        self.instance.port = self.state
        
class HW_Ctrl:
    """low level lighting controls, including the WS2812 strip as well as relais controlled high power leds"""
    def __init__(self, pcf_instance=PCF_Wrapper(), led_pin=LED_PIN, led_count=LED_COUNT):
        self.led_count = led_count
        self.pcf = pcf_instance
        self.strip = neopixel.NeoPixel(led_pin, led_count)
        self.strip = neopixel.NeoPixel(led_pin, led_count)
        self.strip = neopixel.NeoPixel(led_pin, led_count)

        #enforce default state:
        self.default_state()

    def default_state(self):
        self.strip.fill((0,0,0))
        self.strip.show()
        self.pcf.reset()

    # Effect functions, focused on the LED strip.
    def effect_wheel(self, pos):
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
        return (r, g, b)


    def effect_rainbow_cycle(self,delay_ms=50):
        for j in range(255):
            for i in range(self.led_count):
                pixel_index = (i * 256 // self.led_count) + j
                self.strip[i] = self.effect_wheel(pixel_index & 255)
            self.strip.show()
            time.sleep(delay_ms/1000)

    def effect_boot(self, duration=5, color=(255,0,0)):
        self.strip.fill((0,0,0))
        for i in range(self.led_count):
            self.strip[i] = color
            time.sleep((duration-1)/self.led_count)
        self.strip.fill((0,0,0))
        time.sleep(0.2)
        self.strip.fill(color)
        time.sleep(0.5)
        self.strip.fill((0,0,0))

    def effect_fade_in(self, delay_ms=50, color=(255,60,10)):
        for i in range(256):
            self.strip.fill((color[0]/255*i, color[1]/255*i, color[2]/255*i))
            time.sleep(delay_ms/1000)

    def effect_fade_out(self, delay_ms=50, color=(255,60,10)):
        for i in range(255,0,-1):
            self.strip.fill((color[0]/255*i, color[1]/255*i, color[2]/255*i))
            time.sleep(delay_ms/1000)

    def effect_twinkle(self, color=(20,30,50), count=3, delay_ms=50 ,duration=60*1000, bg_color=(0,0,0)):
        self.strip.fill(bg_color)

        for i in range(count):
            pixel = randint(0,self.led_count-1)
            self.strip[pixel] = color
            time.sleep(delay_ms/1000)

        time.sleep(delay_ms/1000)

    def effect_sparkle(self, color=(20,30,50), delay_ms=20, bg_color=(0,0,0)):
        pixel = randint(0,self.led_count-1)
        self.strip[pixel] = color
        time.sleep(delay_ms/1000)
        self.strip[pixel] = bg_color

    def effect_color_fade(self, color_from=(5,5,5), color_to=(255,60,10),  delay_ms=50, steps=255):
        step_R = (color_to[0] - color_from[0]) / steps
        step_G = (color_to[1] - color_from[1]) / steps
        step_B = (color_to[2] - color_from[2]) / steps
        color_is = list(color_from)

        for x in range(steps):
            c = color_is
            self.strip.fill(c)
            time.sleep(delay_ms / 1000.0)
            color_is[0] += step_R
            color_is[1] += step_G
            color_is[2] += step_B

    def effect_sine_wave(self, color=(10,10,10), delay_ms=50,multi=5, cycles=1):
        BASE_LEVEL = 10
        strip = [color for x in range(0,self.led_count)]

        for x in range(0,len(strip)):
            step = 2*3.1415 / len(strip)
            strip[x]  = (int(color[0]+(math.sin(step*x)*multi)),int(color[1]+(math.sin(step*x)*multi)),int(color[2]+(math.sin(step*x)*multi)))

        def shift(list, n=1):
            for i in range(n):
                temp = list.pop()
                list.insert(0, temp)

        for n in range(0,self.led_count*cycles):
            for i in range(self.led_count):
                self.strip[i] = strip[i]
            shift(strip, 1)
            time.sleep(delay_ms/1000)
