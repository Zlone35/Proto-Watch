import machine
import ssd1306
from pyb import ADC
from machine import Pin, Signal, Timer
import time
from pyb import RTC   # or import from machine depending on your micropython version


global oled
global adc

HEART = [
[ 0, 0, 0, 0, 0, 0, 0, 0, 0],
[ 0, 1, 1, 0, 0, 0, 1, 1, 0],
[ 1, 1, 1, 1, 0, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 0, 1, 1, 1, 1, 1, 1, 1, 0],
[ 0, 0, 1, 1, 1, 1, 1, 0, 0],
[ 0, 0, 0, 1, 1, 1, 0, 0, 0],
[ 0, 0, 0, 0, 1, 0, 0, 0, 0],
]

EMPTY_HEART = [
[ 0, 0, 0, 0, 0, 0, 0, 0, 0],
[ 0, 1, 1, 0, 0, 0, 1, 1, 0],
[ 1, 0, 0, 1, 0, 1, 0, 0, 1],
[ 1, 0, 0, 0, 0, 0, 0, 0, 1],
[ 1, 0, 0, 0, 0, 0, 0, 0, 1],
[ 0, 1, 0, 0, 0, 0, 0, 1, 0],
[ 0, 0, 1, 0, 0, 0, 1, 0, 0],
[ 0, 0, 0, 1, 0, 1, 0, 0, 0],
[ 0, 0, 0, 0, 1, 0, 0, 0, 0],
]

rtc = machine.RTC()
rtc.datetime((2023, 4, 17, 1, 10, 15, 0, 0))

#Display 


def display_time():
    year, month, day, weekday, hour, mins, secs, millisecs = rtc.datetime() 
    oled.text("{:02d}:{:02d}".format(hour, mins), 85, 3)

def draw_heart():
    for y, row in enumerate(HEART):
        for x, c in enumerate(row):
            oled.pixel(x+2, y+2, c)
    draw_outline()

def draw_empty_heart():
    for y, row in enumerate(EMPTY_HEART):
        for x, c in enumerate(row):
            oled.pixel(x+2, y+2, c)
    draw_outline()

def draw_outline():
    oled.hline(0, 0, 128, 1)
    oled.hline(0, 63, 128, 1)
    oled.hline(0, 12, 128, 1)
    oled.vline(0, 0, 64, 1)
    oled.vline(127, 0, 64, 1)

i2c = machine.I2C(scl=machine.Pin('B9'),sda=machine.Pin('B8'), freq=200000)
i2c.scan()

oled = ssd1306.SSD1306_I2C(128, 64, i2c)

draw_outline()

#Sensor

oled.show()

oled.hw_scroll_off()

MAX_HISTORY = 250
TOTAL_BEATS = 30


def calculate_bpm(beats):
    if beats:
        beat_time = beats[-1] - beats[0]
        if beat_time:
            return (len(beats) / (beat_time)) * 60

def detect():
    # Maintain a log of previous values to
    # determine min, max and threshold.
    history = []
    beats = []
    bpm = None
    beat = False

    while True:
        v = adc.read()

        history.append(v)

        # Get the tail, up to MAX_HISTORY length
        history = history[-MAX_HISTORY:]

        minima, maxima = min(history), max(history)

        threshold_on = (minima + maxima * 3) // 4   # 3/4
        threshold_off = (minima + maxima) // 2      # 1/2

        if v > threshold_on and beat == False:
            beat = True
            beats.append(time.time())
            beats = beats[-TOTAL_BEATS:]
            bpm = calculate_bpm(beats)

        if v < threshold_off and beat == True:
            draw_empty_heart()
            beat = False
        refresh(bpm, beat, v, minima, maxima)

last_y = 0

def refresh(bpm, beat, v, minima, maxima):
    global last_y

    oled.scroll(-1,0)

    #if maxima-minima > 0:
        #y = 51 - int(32 * (v-minima) / (maxima-minima))
        #oled.line(124, last_y + 13, 125, y + 13, 1)
        #last_y = y
    oled.fill_rect(1,1,126, 10,0)

    if bpm:
        oled.text("%d bpm" % bpm, 12, 3)

    if beat:
        draw_heart()
    display_time()
    oled.show()
    

machine.Pin('A1', machine.Pin.IN)
adc = ADC('A1')

detect()