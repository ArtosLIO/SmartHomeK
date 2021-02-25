from tkinter import *
import tkinter.ttk as ttk
import datetime
from matplotlib import pyplot as plt # вывод графика температуры
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import configparser # запись/чтение файлов
import os
from pathlib import Path
from w1thermsensor import W1ThermSensor # Подключение к датчику температуры
import RPi.GPIO as GPIO # Подключение к вход/выход Малинки


GPIO.setwarnings(False)
security = True
sensor = W1ThermSensor()
temperature = 0.0
min_temperature = 0.0
max_temperature = 0.0
lighting = False # Проверка включен ли свет
pin_security = 14 # pin датчика движения
GPIO_temperature = 4 # pin датчика температуры
pin_light_security = 16 # Z 
pin_light_temperature = 20 # Z
GPIO_light = 21 # pin светодиода
GPIO.setmode(GPIO.BCM)
GPIO.setup([GPIO_temperature, GPIO_light, pin_light_security, pin_light_temperature], GPIO.OUT)
GPIO.setup(pin_security, GPIO.IN)
pwm = GPIO.PWM(GPIO_light, 8500)
pwm.start(0)
arrmini = []
arrmax = []
arrx = []
arry = []


conf = configparser.RawConfigParser()
patch = str(Path(__file__).parents[0])
if os.path.exists(patch+"/settings.conf"):
    conf.read(patch+"/settings.conf")
    max_temperature = conf.get("temperature", "top_border")
    min_temperature = conf.get("temperature", "low_border")
else:
    conf.add_section("temperature")
    conf.set("temperature", "top_border", 27)
    conf.set("temperature", "low_border", 23)
    max_temperature = 27
    min_temperature = 23
    with open(patch+"/setting.conf", "w") as config:
        conf.write(config)


root = Tk()
root.geometry('{w}x{h}'.format(w=root.winfo_screenwidth(), h=root.winfo_screenheight()))
root.title("SmartHome")
fig = plt.figure() # создание екзампляра контейнера графика
ax = fig.add_subplot(111) # Создание графика


def runSecurity():
    global security, pin_light_security
    if security:
        security = False
        bt_sectrity_run.configure(text='Включить систему безопасности')
        GPIO.output(pin_light_security, GPIO.HIGH)
    else:
        security = True
        bt_sectrity_run.configure(text='Выключить систему безопасности')
        GPIO.output(pin_light_security, GPIO.LOW)


def lamp_manipulate():
    global GPIO_light
    
    if not GPIO.input(GPIO_light):
        pwm.ChangeDutyCycle(100)
        sl_scaling_light.set(100)
        bt_lamp_manipulate.configure(text='Выключить свет')
        lb_lamp_vv.configure(text='Включен')
    else:
        pwm.ChangeDutyCycle(0)
        bt_lamp_manipulate.configure(text='Включить свет')
        lb_lamp_vv.configure(text='Выключен')
        sl_scaling_light.set(0)


def lamp_scaling(val): #Регулировка света
    global pwm

    if GPIO.input(GPIO_light):
        pwm.ChangeDutyCycle(int(val))


def heating_manipulate():
    global min_temperature, max_temperature
    
    try:
        if en_heating_manipulate_min.get() != '' and (en_heating_manipulate_min.get() < en_heating_manipulate_max.get()):
            min_temperature = int(en_heating_manipulate_min.get())
        if en_heating_manipulate_max.get() != '' and en_heating_manipulate_max.get() > en_heating_manipulate_min.get():
            max_temperature = int(en_heating_manipulate_max.get())
        
        lb_heating_min_size.configure(text=min_temperature)
        lb_heating_max_size.configure(text=max_temperature)
        lb_heating_manipulate_error.configure(text='')
    except Error as e:
        lb_heating_manipulate_error.configure(text='Введен неверный тип данных')


def send(pin):
    global pin_security, security

    if security:
        if GPIO.input(pin_security) == 1:
            try:
                lb_security_messenger.configure(text='В ДОМЕ ОПАСНО!')
            except:
                pass
        else:
            try:
                lb_security_messenger.configure(text='В ДОМЕ БЕЗОПАСНО')
            except:
                pass
    else:
        if GPIO.input(pin_security) == 1:
            pwm.ChangeDutyCycle(100)
            sl_scaling_light.set(100)
            lb_lamp_vv.configure(text='Включен')
            bt_lamp_manipulate.configure(text='Выключить свет')
        else:
            pwm.ChangeDutyCycle(0)
            sl_scaling_light.set(0)
            lb_lamp_vv.configure(text='Выключен')
            bt_lamp_manipulate.configure(text='Включить свет')


def animation(i):
    global min_temperature, max_temperature, arrx, arry, arrmax, arrmini, pin_light_temperature
    
    if sensor.get_temperature() < min_temperature:
        GPIO.output(pin_light_temperature, GPIO.HIGH)
        lb_heating_vv.configure(text='Включен')
    elif sensor.get_temperature() > max_temperature:
        GPIO.output(pin_light_temperature, GPIO.LOW)
        lb_heating_vv.configure(text='Выключен')
    
    if len(arry) >= 100:
        arry.pop(0)
        arrx.pop(0)
        arrmax.pop(0)
        arrmini.pop(0)
    
    arry.append(sensor.get_temperature())
    arrx.append(datetime.datetime.now())
    arrmini.append(min_temperature)
    arrmax.append(max_temperature)
    
    ax.clear()
    ax.plot(arrx, arry, 'r', arrx, arrmax, 'g', arrx, arrmini, 'b') #для вывода данных
    
    plt.title('Зависимость')
    plt.xlabel('Время')
    plt.ylabel('Температура')
    
    xfmt = mdates.DateFormatter('%H:%M:%S') #формат отображения данных
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis_date()

canvas = FigureCanvasTkAgg(fig, master=root) #отображение в окне
anim = FuncAnimation(fig, animation, interval=500)



lb_lamp = Label(text='Состояние освещения:')
lb_lamp_vv = Label(text='Выключен')

lb_heating = Label(text='Состояния отопления: ')
lb_heating_vv = Label(text='Выключен')

lb_heating_min = Label(text='Порог минимальной температуры: ')
lb_heating_min_size = Label(text=min_temperature)

lb_heating_max = Label(text='Порог максимальной температуры: ')
lb_heating_max_size = Label(text=max_temperature)

lb_heating_manipulate = Label(text='Изменить пороги температуры', font=20)
lb_heating_manipulate_min = Label(text='Минимальная температура').grid(row=6, column=1)
lb_heating_manipulate_max = Label(text='Максимальная температура').grid(row=7, column=1)
lb_heating_manipulate_error = Label()

en_heating_manipulate_min = Entry(width=4)
en_heating_manipulate_max = Entry(width=4)

bt_heating_manipulate = Button(text='Подтвердить изменение', command=heating_manipulate)
bt_lamp_manipulate = Button(text='Включить свет', command=lamp_manipulate)
bt_sectrity_run = Button(text='Выключить систему безопасности', command=runSecurity)

lb_scaling_light = Label(root, text="Регулировка яркости")
sl_scaling_light = Scale(root, orient=HORIZONTAL, from_=0, to=100, resolution=1, length=200, command=lamp_scaling)

lb_security_messenger = Label(text='В доме безопасно')



lb_lamp.grid(row=1, column=1)
lb_lamp_vv.grid(row=1, column=2)
lb_heating.grid(row=2, column=1)
lb_heating_vv.grid(row=2, column=2)

lb_heating_min.grid(row=3, column=1)
lb_heating_min_size.grid(row=3, column=2)
lb_heating_max.grid(row=4, column=1)
lb_heating_max_size.grid(row=4, column=2)

lb_heating_manipulate.grid(row=5, column=1, columnspan=2)
en_heating_manipulate_min.grid(row=6, column=2)
en_heating_manipulate_max.grid(row=7, column=2)
lb_heating_manipulate_error.grid(row=8, column=1, columnspan=2)

bt_lamp_manipulate.grid(row=1, column=3, columnspan=2)
bt_heating_manipulate.grid(row=5, column=2, columnspan=2)
bt_sectrity_run.grid(row=9, column=1, columnspan=2)
lb_security_messenger.grid(row=9, column=3)

lb_scaling_light.grid(row=10, column=1)
sl_scaling_light.grid(row=10, column=2, columnspan=2)

canvas.get_tk_widget().grid(row=11, column=1, columnspan=3)


GPIO.add_event_detect(pin_security, GPIO.BOTH, callback=send)

if __name__ == "__main__":
    root.mainloop()
    GPOI.cleanup()
