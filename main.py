'''
 pip install PyAutoGUI
 pip install Pillow
 pip install yolov5
 pip install keyboard

    минимально достижимый "шаг" смещения прицела = 3.7 пикселя
    за минимальный импульс = 0.0152 сеунды
    все более короткие импульсы вызывают смещение примерно на 3.7 пикселя

    Для того чтобы переместить прицел на меньшее расстояние, чем длина
    минимального шага, можно сдвинуть дальше и вернуть чуть меньше.
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

kx = float(0.0152)  # Коэффициенты, управляющие продолжительностью нажатия на клавиши наводки
ky = float(0.0152)
aim_step = 3.7      # минимальный шаг смешения прицела

keyb = {
        'esc': 'Esc',  # сброс
        'shoot': '=',  # выстрел
        'aim': 'o',     # преключение прицела
        'reload': 'r'  # перезарядка
        }

key_shoot      = '='      # клавиша выстрела
key_onaim      = 'o'      # клавиша прицеливания
full_cartridge = 7        # ёмкость магазина
time_reload    = 2.5      # время на перезарядку

cartridge = full_cartridge  # счетчик патронов в магазине

model = torch.hub.load('ultralytics/yolov5', 'custom', path='wtl_target.pt')


def press(key, pause = 0.01):
    keyboard.press(key)
    time.sleep(pause)
    keyboard.release(key)


# перезарядка магазина
def cartridge_control():
    global full_cartridge, cartridge, time_reload
    global keyb
    cartridge -= 1
    if cartridge < 1:
        press(keyb['reload'])
        time.sleep(time_reload)
        cartridge = full_cartridge


# Выстрел
def shoot():
    global cartridge, keyb
    press(keyb['aim'])    # навести прицел
    time.sleep(0.5)
    press(keyb['shoot'])  # выстрел
    time.sleep(0.1)
    press(keyb['aim'])    # опустить оружие
    time.sleep(0.6)
    cartridge_control()

def aim_move(side, d):
    global kx, ky, aim_step

    rside = ''
    key = 0

    if side == 'right':
        rside = 'left'
        key = kx
    elif side == 'left':
        rside = 'right'
        key = kx
    elif side == 'up':
        rside = 'down'
        key = ky
    elif side == 'down':
        rside = 'up'
        key = ky

    if d < aim_step:
        press(side, 0.13)
        time.sleep( 0.1 )
        press(rside, 0.12)
    else:
        press(side, key * d / aim_step)

    time.sleep( 0.25 )


# Наведение и выстрел
def aiming(x, y):
    global aim_x, aim_y
    exactness_x = 2.0  # точность прицеливания по X
    exactness_y = 3.5   # точность прицеливания по Y

    dx = aim_x - x
    dy = aim_y - y

    # контроль наличия калибровки по X и Y
    if aim_x < 10.0: return
    if aim_y < 10.0: return

    # Выстрел
    if (abs(dx) < exactness_x) and (abs(dy) < exactness_y):
        shoot()
        return

    # Наведение по горизонтали
    if abs(dx) >= exactness_x:
        if dx < 0:
            aim_move('right', abs(dx))
        else:
            aim_move('left', dx)

    # Наведение по вертикали
    if abs(dy) >= exactness_y:
        if dy < 0:
            aim_move('down', abs(dy))
        else:
            aim_move('up', dy)


# Установка координат прицела при запуске.
# Привязано на горячую клавишу Shift, которую следует
# нажать при наведя оружие точно в центр найденной мишени
def aim_point_setup():
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
keyboard.add_hotkey('right shift', aim_point_setup)
# остановка цикла
keyboard.add_hotkey('right ctrl', robot_stop)

errors_ctrl = 0  # счетчик идущих подряд ошибок обнаружения
humans_ctrl = 0  # счетчик имитации ответа человека на заставку с [ Esc ]

while run:
    image = pyautogui.screenshot(region=(window_x0, window_y0, window_x1, window_y1))
    t = model(image).xyxy[0]
    target = t.numpy()

    # Если больше 12 секунд нет обнаружения, то нажать 'Esc'
    if errors_ctrl > 12:
        press(keyb['esc'], 0.2)
        humans_ctrl += 1
        errors_ctrl = 0

    # Если подряд 4 раза нажата 'Esc', а обнаружения нет, то прекратить выполение
    if humans_ctrl > 4:
        robot_stop()

    if numpy.size(target) > 0:
        aiming(target[0, 0], target[0, 1])
        errors_ctrl = 0
        humans_ctrl = 0
    else:
        print("no target found")
        time.sleep(1.0)      # подождать 1 секунду
        errors_ctrl += 1     # подсчет числа идущих подряд сбоев обнаружения

