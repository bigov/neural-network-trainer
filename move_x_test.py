import keyboard
import time

run = True
start = False

def app_start():
    global start
    start = not start


def app_exit():
    global run
    run = False


keyboard.add_hotkey('right shift', app_start)
keyboard.add_hotkey('right ctrl', app_exit)

'''
.0152: 3,7p
.0155: 6,5p
.0160: 6,1p
.0170: 7,4p
.0180: 15
.0190: 12
.0200: 13
.0250: 13
.0300: 13
.0310: 13, 12
.0311: 10
.0312: 9
.0315: 9
.0320: 10
.0350: 10
.0400: 9
.4260: 1            [ 104p  ] шаг = 3,7
'''
move_right = 0.13
move_left  = 0.12
pause = 0.2
n = 0

while run:
    if start:
        keyboard.press('right')
        time.sleep(move_right)
        keyboard.release('right')

        time.sleep(pause)

        keyboard.press('left')
        time.sleep(move_left)
        keyboard.release('left')

        time.sleep(pause*4)
        #start = not start
    else:
        time.sleep(0.333)
        n = 0

