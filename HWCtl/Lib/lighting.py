from .pcf8575 import PCF8575
import Adafruit_DHT
import board
import busio
import adafruit_pca9685
import board
import neopixel
import time
import math
import logging
from random import randint
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import subprocess

I2C_PORT = 1
PCF_ADDR = 0x20
DISPLAY_ADDR = 0x3c
DHT_PINS = [5,6]
DHT_TYPE = Adafruit_DHT.DHT22

LED_COUNT      = 122      # Number of LED pixels.
LED_PIN        = board.D18      # GPIO pin connected to the pixels (18 uses PWM!).


class WhiteLight():
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = adafruit_pca9685.PCA9685(i2c)
        self.pca.frequency = 240
        self.MAX_BRIGHTNESS = 0xffff

        self.left_strip = self.pca.channels[0]
        self.middle_strip = self.pca.channels[1]
        self.right_strip = self.pca.channels[2]

        self.strips = [self.left_strip, self.middle_strip, self.right_strip]

    def set_all(self, brightness):
        # brightness from 0 to 1
        for i in self.strips:
            i.duty_cycle = int(brightness * self.MAX_BRIGHTNESS)

    def effect_fade(self, fromBrightness=0, toBrightness=1.0, delay_ms=50, steps=1000):
        step = (toBrightness - fromBrightness) / steps
        for i in range(steps):
            print(step, i, self.MAX_BRIGHTNESS, int(step*i*self.MAX_BRIGHTNESS))
            self.set_all(int(step*i*self.MAX_BRIGHTNESS))
            time.sleep(delay_ms/1000)

class Display_Wrapper:
    def __init__(self):
        from board import SCL, SDA
        import busio
        import adafruit_ssd1306
        self.i2c = busio.I2C(SCL, SDA)
        self.display = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)

        # Clear display.
        self.display.fill(0)
        self.display.show()

        self.font = ImageFont.load_default()


    def create_blank_image(self):
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.image = Image.new("1", (self.display.width, self.display.height))
        self.drawing = ImageDraw.Draw(self.image)
        self.drawing.rectangle((0, 0, self.display.width, self.display.height), outline=0, fill=0)

    def refresh_image(self, sensor_data=[]):
        # First define some constants to allow easy resizing of shapes.
        padding = -2
        top = padding

        bottom = self.display.height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        x = 0

        self.create_blank_image()

        cmd = "hostname -I | cut -d' ' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
        self.drawing.text((x, top + 0), "IP: " + IP, font=self.font, fill=255)

        time = datetime.now().strftime("%H:%M")
        self.drawing.text((x, top + 8), "Zeit: " + time, font=self.font, fill=255)

        i = 16
        for s in sensor_data:
            if 'humidity' in s:
                self.drawing.text((x, top + i), "T: %2.1f°C | H: %i%%" % (s['temperature'], s['humidity']), font=self.font, fill=255)
            else:
                self.drawing.text((x, top + i), "T: %2.1f°C" % s['temperature'] , font=self.font, fill=255)
            i += 8

        self.display.image(self.image)
        self.display.show()


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

    def get_state(self):
        result = {}
        # Be aware that raw is still inverted
        result['raw'] = self.state
        result['sockets'] = {'RED': not self.state[14], 'YELLOW': not self.state[12], 'BLUE': not self.state[10], 'GREEN': not self.state[8]}
        result['12v'] = not self.state[15]
        result['leds'] = {}
        result['leds']['white_left'] = not (self.state[6] and self.state[7])
        result['leds']['white_right'] = not(self.state[5] and self.state[7])
        result['leds']['full_spec'] = not(self.state[4] and self.state[7])
        return result

    def reset(self):
        self.state = [True, True, True, True, True, True, True, True,True, True, True, True, True, True, True, True]
        self.instance.port = self.state
        
    def all_on(self):
        self.state = [False, False, False, False, False, False, False, False,False, False, False, False, False, False, False, False]
        self.instance.port = self.state
    def set_12v_psu(self, state=False):
        """Set state for the 12v PSU"""
        # default is off
        self.state[15] = not state
        self.instance.port = self.state

    # def set_white_left(self, state=False):
    #     """Set state for left white LEDs"""
    #     if state:
    #         self.state[7] = False
    #         self.state[6] = False
    #         self.instance.port = self.state
    #     else:
    #         # Be aware: PSU won't be powered off
    #         self.state[6] = True
    #         self.instance.port = self.state
    #
    # def set_white_right(self, state=False):
    #     """Set state for right white LEDs"""
    #     if state:
    #         self.state[7] = False
    #         self.state[5] = False
    #         self.instance.port = self.state
    #     else:
    #         # Be aware: PSU won't be powered off
    #         self.state[5] = True
    #         self.instance.port = self.state
    #
    # def set_white(self, state=False):
    #     """Set state for all white LEDs"""
    #     if state:
    #         self.set_white_left(True)
    #         self.set_white_right(True)
    #     else:
    #         self.set_white_left(False)
    #         self.set_white_right(False)
    #
    # def set_full_spec(self, state=False):
    #     """Set state for the full spectrum LEDs"""
    #     if state:
    #         self.state[7] = False
    #         self.state[4] = False
    #         self.instance.port = self.state
    #     else:
    #         # Be aware: PSU won't be powered off
    #         self.state[4] = True
    #         self.instance.port = self.state
    #
    # def set_socket(self, socket, state=False):
    #     if socket == "RED":
    #         self.state[14] = not state
    #         self.state[15] = not state
    #     elif socket == "YELLOW":
    #         self.state[12] = not state
    #         self.state[13] = not state
    #     elif socket == "BLUE":
    #         self.state[10] = not state
    #         self.state[11] = not state
    #     elif socket == "GREEN":
    #         self.state[8] = not state
    #         self.state[9] = not state
    #     self.instance.port = self.state
        
class HW_Ctrl:
    """low level lighting controls, including the WS2812 strip as well as relais/pwm controlled high power leds"""
    def __init__(self, pcf_instance=PCF_Wrapper(), led_pin=LED_PIN, led_count=LED_COUNT, display_instance=Display_Wrapper()):
        self.led_count = led_count
        self.pcf = pcf_instance
        self.display = display_instance
        self.strip = neopixel.NeoPixel(led_pin, led_count, pixel_order=neopixel.GRBW)
        self.white = WhiteLight()

        #enforce default state:
        self.default_state()

    def default_state(self):
        self.strip.fill((0,0,0))
        self.strip.show()
        self.pcf.reset()

    def get_state(self):
        # We don't have a known state for the neopixel/ws2812b strip anyways.
        return self.pcf.get_state()

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

    def effect_sine_wave(self, color=(5,5,5), delay_ms=100,multi=4, cycles=1, waves=2,smooth=True):
        BASE_LEVEL = 10
        strip = [color for x in range(0,self.led_count)]

        for x in range(0,len(strip)):
            step = waves*2*3.1415 / len(strip)
            strip[x]  = (max(0,int(color[0]+(math.sin(step*x)*multi))),max(0,int(color[1]+(math.sin(step*x)*multi))),max(0,int(color[2]+(math.sin(step*x)*multi))))

        def shift(list, n=1):
            for i in range(n):
                temp = list.pop()
                list.insert(0, temp)

        def smooth(curr,prev):
            return (curr[0]+prev[0])/2,(curr[1]+prev[1])/2,(curr[2]+prev[2])/2

        for n in range(0,self.led_count*cycles):
            for i in range(self.led_count):
                if not smooth:
                    self.strip[i] = strip[i]
                else:
                    self.strip[i] = smooth(strip[i], strip[i-1])
            shift(strip, 1)
            time.sleep(delay_ms/1000)


    def get_DHT_values(self):
        result = []
        for pin in DHT_PINS:
            try:
                values = Adafruit_DHT.read_retry(DHT_TYPE, pin)
                result.append({'humidity': values[0], 'temperature': values[1]})
            except:
                logging.info("An error occured while reading the Sensor on Pin %s" % pin)
        return result

    def get_DS1820_value(self):
        ds1820_path = '/sys/bus/w1/devices/28-3c01d075d0b4/temperature'
        with open(ds1820_path) as file:
            raw = file.readline()
            temp = int(raw) / 1000.0
        return [{'temperature': temp}]
