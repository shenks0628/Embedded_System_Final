from machine import Pin, PWM
import utime
pin = Pin(15, Pin.OUT)
music_end = [(3,1,0,0.3), (2,5,0,0.3), (2,4,1,0.3), (2,5,0,0.3),
             (3,1,0,0.3), (2,5,0,0.3), (2,4,1,0.3), (2,5,0,0.3),
             (3,1,0,0.3), (2,5,0,0.3), (3,1,0,0.3), (2,5,0,0.3),
             (3,1,0,0.3), (2,5,0,0.3), (2,4,1,0.3), (2,5,0,0.3),
             (3,1,0,0.3), (2,5,0,0.3), (3,1,0,0.3), (3,3,0,0.3), (3,5,0,0.3), (0,0,0,0.9),
             (3,5,0,0.6), (3,4,0,0.3), (3,3,0,0.3),
             (3,2,0,0.6), (3,3,0,0.3), (3,2,0,0.3),
             (3,1,0,0.6), (3,2,0,0.3), (3,3,0,0.3),
             (2,5,0,0.3), (2,6,0,0.2), (2,5,0,0.3),
             (3,5,0,0.6), (3,4,0,0.3), (3,3,0,0.3),
             (3,6,0,0.6), (3,5,0,0.3), (3,3,0,0.3),
             (3,4,0,0.3), (3,5,0,0.15), (3,4,0,0.15), (3,3,0,0.3), (3,4,0,0.15), (3,3,0,0.15),
             (3,2,0,0.3), (0,0,0,0.9),
             (3,2,0,0.3),(3,2,0,0.15),(3,2,0,0.15), (3,1,0,0.3),(3,2,0,0.3),
             (3,3,0,0.3), (3,4,0,0.3), (3,5,0,0.6),
             (3,2,0,0.3), (3,3,0,0.3), (3,4,0,0.6),
             (3,3,0,0.3), (3,2,0,0.3), (3,1,0,0.6),
             (3,2,0,0.3),(3,2,0,0.15),(3,2,0,0.15), (3,1,0,0.3),(3,2,0,0.3),
             (3,3,0,0.3), (3,4,0,0.3), (3,5,0,0.6),
             (3,4,1,0.3), (3,5,0,0.3), (3,6,0,0.3), (3,7,0,0.3),
             (3,5,0,0.3), (0,0,0,0.9)
             ]
def play_sound(i): # 播音
    h, x, y, t = i
    try:
        x = int(x)
    except:
        return
    if h == 0:
        utime.sleep(0.3)
        return
    elif h == 1:
        if x == 1 and not y:
            pwm = PWM(pin, freq = 262, duty = 512)
        elif x == 1 and y:
            pwm = PWM(pin, freq = 277, duty = 512)
        elif x == 2 and not y:
            pwm = PWM(pin, freq = 294, duty = 512)
        elif x == 2 and y:
            pwm = PWM(pin, freq = 311, duty = 512)
        elif x == 3 and not y:
            pwm = PWM(pin, freq = 330, duty = 512)
        elif x == 4 and not y:
            pwm = PWM(pin, freq = 349, duty = 512)
        elif x == 4 and y:
            pwm = PWM(pin, freq = 370, duty = 512)
        elif x == 5 and not y:
            pwm = PWM(pin, freq = 392, duty = 512)
        elif x == 5 and y:
            pwm = PWM(pin, freq = 415, duty = 512)
        elif x == 6 and not y:
            pwm = PWM(pin, freq = 440, duty = 512)
        elif x == 6 and y:
            pwm = PWM(pin, freq = 466, duty = 512)
        elif x == 7 and not y:
            pwm = PWM(pin, freq = 494, duty = 512)
    elif h == 2:
        if x == 1 and not y:
            pwm = PWM(pin, freq = 523, duty = 512)
        elif x == 1 and y:
            pwm = PWM(pin, freq = 554, duty = 512)
        elif x == 2 and not y:
            pwm = PWM(pin, freq = 587, duty = 512)
        elif x == 2 and y:
            pwm = PWM(pin, freq = 622, duty = 512)
        elif x == 3 and not y:
            pwm = PWM(pin, freq = 659, duty = 512)
        elif x == 4 and not y:
            pwm = PWM(pin, freq = 698, duty = 512)
        elif x == 4 and y:
            pwm = PWM(pin, freq = 740, duty = 512)
        elif x == 5 and not y:
            pwm = PWM(pin, freq = 784, duty = 512)
        elif x == 5 and y:
            pwm = PWM(pin, freq = 831, duty = 512)
        elif x == 6 and not y:
            pwm = PWM(pin, freq = 880, duty = 512)
        elif x == 6 and y:
            pwm = PWM(pin, freq = 932, duty = 512)
        elif x == 7 and not y:
            pwm = PWM(pin, freq = 988, duty = 512)
    elif h == 3:
        if x == 1 and not y:
            pwm = PWM(pin, freq = 1046, duty = 512)
        elif x == 1 and y:
            pwm = PWM(pin, freq = 1109, duty = 512)
        elif x == 2 and not y:
            pwm = PWM(pin, freq = 1175, duty = 512)
        elif x == 2 and y:
            pwm = PWM(pin, freq = 1245, duty = 512)
        elif x == 3 and not y:
            pwm = PWM(pin, freq = 1318, duty = 512)
        elif x == 4 and not y:
            pwm = PWM(pin, freq = 1397, duty = 512)
        elif x == 4 and y:
            pwm = PWM(pin, freq = 1480, duty = 512)
        elif x == 5 and not y:
            pwm = PWM(pin, freq = 1568, duty = 512)
        elif x == 5 and y:
            pwm = PWM(pin, freq = 1661, duty = 512)
        elif x == 6 and not y:
            pwm = PWM(pin, freq = 1760, duty = 512)
        elif x == 6 and y:
            pwm = PWM(pin, freq = 1865, duty = 512)
        elif x == 7 and not y:
            pwm = PWM(pin, freq = 1976, duty = 512)
    utime.sleep(t)
    pwm.deinit()
def play_win():
    for x in music_end:
        play_sound(x)