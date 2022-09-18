'''
 pip install PyAutoGUI
 pip install Pillow
 pip install yolov5
 pip install keyboard

    минимально достижимый "шаг" смещения прицела:
        - минимальный импульс:  0.0152 сеунды
        - cреденее перемещение: 3,7 пикселя

    Для того чтобы переместить прицел на меньшее расстояние, чем длина
    минимального импульса, можно сдвинуть дальше и вернуть чуть меньше.
    Такая схема реализуется при использовании задержки 0.13 к 0.12
'''
import torch
import pyautogui
import numpy
import keyboard
import time


run = True  # переменная рабочего цикла

# границы скриншота для поиска мишени
window_width = 1600
window_height = 900
window_x0 = 2
window_x1 = window_x0 + window_width
window_y0 = 32
window_y1 = window_y0 + window_height

# x-коррдинаты прицела
aim_x = 0.0
aim_y = 0.0

# Коэффициенты, управляющие продолжительностью нажатия на клавиши наводки
kx = float(0.0033)
ky = float(0.0033)

# Подсчет числа шагов при наведении на мишень до выстрела
# используется для настройки длительности нажатия на клавиши наводки
steps_r = 0
steps_l = 0
steps_u = 0
steps_d = 0

key_shoot      = '='        # клавиша выстрела
key_onaim      = 'o'        # клавиша прицеливания
full_cartridge = 18         # ёмкость магазина
time_reload    = 2.5        # время на перезарядку

cartridge = full_cartridge  # счетчик патронов в магазине

model = torch.hub.load('ultralytics/yolov5', 'custom', path='wtl_target.pt')


# перезарядка магазина
def cartridge_control():
    global full_cartridge, cartridge, time_reload
    cartridge -= 1
    if cartridge < 1:
        keyboard.press('r')
        time.sleep(0.01)
        keyboard.release('r')
        time.sleep(time_reload)
        cartridge = full_cartridge


# Выстрел
def shoot():
    global cartridge
    global steps_r, steps_l, steps_u, steps_d
    steps_r = 0
    steps_l = 0
    steps_u = 0
    steps_d = 0

    keyboard.press(key_onaim)    # навести прицел
    time.sleep(0.01)
    keyboard.release(key_onaim)
    time.sleep(0.25)

    keyboard.press(key_shoot)    # выстрел
    time.sleep(0.01)
    keyboard.release(key_shoot)
    time.sleep(0.25)

    keyboard.press(key_onaim)    # опустить оружие
    time.sleep(0.01)
    keyboard.release(key_onaim)
    time.sleep(0.7)

    cartridge_control()


def move_x(d):
    global kx, steps_r, steps_l
    if d < 0:
        steps_r += 1
        keyboard.press('right')
        time.sleep(float(kx) * float(abs(d)))
        keyboard.release('right')
    else:
        steps_l += 1
        keyboard.press('left')
        time.sleep(float(kx) * float(d))
        keyboard.release('left')


def move_y(d):
    global ky, steps_d, steps_u
    if d < 0:
        steps_d += 1
        keyboard.press('down')
        time.sleep(float(ky) * float(abs(d)))
        keyboard.release('down')
    else:
        steps_u += 1
        keyboard.press('up')
        time.sleep(float(ky) * float(d))
        keyboard.release('up')


def calibration(k, s1, s2):
    if (s1 == 0) and (s2 > 2):
        k *= 1 + 0.1 * s2

    if (s2 == 0) and (s1 > 2):
        k *= 1 + 0.1 * s1

    if (s1 > 0) and (s2 > 0):
        k /= 1.01

    return k


# Калибровка множителей задерки нажатия
def moving_calibration():
    global kx, ky
    global steps_r, steps_l, steps_d, steps_u
    kx = float(calibration(kx, steps_r, steps_l))
    ky = float(calibration(ky, steps_d, steps_u))
    print('kx =', kx, 'ky =', ky)
    return


# Прицеливание
def aiming(x, y):
    global aim_x, aim_y
    exactness = 0.9  # точность прицеливания
    dx = aim_x - x
    dy = aim_y - y

    # контроль наличия калибровки по X
    if aim_x < 10.0:
        return

    # контроль наличия калибровки по Y
    if aim_y < 10.0:
        return

    if (abs(dx) < exactness) and (abs(dy) < 1.0):
        #moving_calibration()
        shoot()
        return

    if abs(dx) >= exactness:
        move_x(dx)
    if abs(dy) >= 1.0:
        move_y(dy)


# Калибровка прицела при запуске приложения.
# Привязано на горячую клавишу Shift, которую следует
# нажать при наведенном точно в центр мишени оружии
def aim_calibtation():
    global aim_x, aim_y, model
    global window_x0, window_y0, window_x1, window_y1

    img = pyautogui.screenshot(region=(window_x0, window_y0, window_x1, window_y1))
    my_t = model(img).xyxy[0]
    my_n = my_t.numpy()
    if numpy.size(my_n) > 0:
        aim_x = my_n[0, 0]
        aim_y = my_n[0, 1]
        print(aim_x, aim_y)
    else:
        print('Can not set up aim - no target found.')


def robot_stop():
    global run
    run = False

# калибровка прицела
keyboard.add_hotkey('right shift', aim_calibtation)
# остановка цикла
keyboard.add_hotkey('right ctrl', robot_stop)


erros_ctrl= 0
while run:
    image = pyautogui.screenshot(region=(window_x0, window_y0, window_x1, window_y1))
    t = model(image).xyxy[0]
    target = t.numpy()

    # Если больше 100 секунд нет обнаружения, то прекратить выполнение
    if erros_ctrl> 100: robot_stop()

    if numpy.size(target) > 0:
        aiming(target[0, 0], target[0, 1])
        erros_ctrl= 0
    else:
        print("no target found")
        time.sleep(1.0) # подождать 1 секунду
        erros_ctrl+= 1    # подсчет числа ошибок обнаружения идущих подряд

