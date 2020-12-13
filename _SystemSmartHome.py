from tkinter import *
import tkinter.ttk as ttk
import datetime
import random
from matplotlib import pyplot as plt # вывод графика температуры
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import configparser # запись/чтение файлов
import os
from pathlib import Path
import mysql.connector # подключение к БД
from mysql.connector import Error
from w1thermsensor import W1ThermSensor # Подключение к датчику температуры
import RPi.GPIO as GPIO # Подключение к вход/выход Малинки


security = True
sensor = W1ThermSensor()
temperature = 0.0
min_temperature = 0.0
max_temperature = 0.0
date_time_temperature = 0
connect_bd = False # Проверка подключения БД
lighting = False # Проверка включен ли свет
connuser = 'myuser'
connpass = '123qwe'
addr_from = "lukienko.igor411@gmail.com"
addr_to = "lukienko.igor411@gmail.com"
password = "23l07i04o06"
pin_security = # pin датчика движения
GPIO_light = # pin светодиода
GPIO_temperature = # pin датчика температуры
GPIO.setmode(GPIO.BCM)
GPIO.setup([pin_security, GPIO_light, GPIO_temperature], GPIO.OUT)
pwm = GPIO.PWM(GPIO_light, 8500)
pwm.start(0)
arrmini = []
arrmax = []
arrx = []
arry = []

style = ttk.Style()
style.configure(".", foreground="black", background="white")


conf = configparser.RawConfigParser()
patch = str(Path(__file__).parents[0])
if os.path.exists(patch+"/settings.conf"):
    conf.read(patch+"/settings.conf")
    max_temperature = conf.get("temperature", "top_border")
    min_temperature = conf.get("temperature", "low_border")
else:
    conf.add_section("temperature")
    conf.set("temperature", "top_border", max_temperature)
    conf.set("temperature", "low_border", min_temperature)
    with open(patch+"/setting.conf", "w") as config:
        conf.write(config)


root = Tk()
root.geometry('{w}x{h}'.format(w=root.winfo_screenwidth(), h=root.winfo_screenheight()))
fig = plt.figure() #создание екзампляра контейнера графика
ax = fig.add_subplot(111) #Создание графика


try:
    connector = mysql.connector.connect(
        user=connuser,
        password=connpass,
        host='localhost',
        database='smarthome'
        )
    print("Connect by BD: successfully")
    connect_bd = True
except:
    print("Connect by BD: Error")
    

def lamp_manipulate():
    global lighting
    
    if not lighting:
        lighting = True
        GPIO.output(GPIO_light, GPIO.HIGH)
        bt_lamp_manipulate.configure(text='Выключить свет')
    else:
        lighting = False
        GPIO.output(GPIO_light, GPIO.LOW)
        bt_lamp_manipulate.configure(text='Включить свет')


def lamp_scaling(val): #Регулировка света
    global pwm, lighting

    if lighting:
        pwm.ChangeDutyCycle(int(val))


def heating_manipulate():
    global min_temperature, max_temperature
    
    try:
        if en_heating_manipulate_min.get() != '' and en_heating_manipulate_min.get() < en_heating_manipulate_max.get():
            min_temperature = int(en_heating_manipulate_min.get())
        if en_heating_manipulate_max.get() != '' and en_heating_manipulate_max.get() > en_heating_manipulate_min.get():
            max_temperature = int(en_heating_manipulate_max.get())
        
        lb_heating_min_size.configure(text=min_temperature)
        lb_heating_max_size.configure(text=max_temperature)
        lb_heating_manipulate_error.configure(text='')
    except Error as e:
        lb_heating_manipulate_error.configure(text='Введен неверный тип данных')


def send(pin):
    msg = MIMEMultipart()
    msg["From"] = addr_from #нет переменной
    msg["To"] = addr_to
    msg["Subject"] = 'Безопасность дома'
    if GPIO.input(pin) == 1:
        lb_security_messenger.configure(text='В доме не безопасно')
        body = 'В доме не безопасно'
    else GPIO.input(pin) == 0:
        lb_security_messenger.configure(text='В доме безопасно')
        body = 'В доме безопасно'
    lb.config(text=body)
    print(GPIO.input(pin))
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(addr_from, password)
    server.send_message(msg)
    server.quit()


def animation(i):
    global min_temperature, max_temperature, connector, date_time_temperature, arrx, arry, arrmax, arrmini

    if connect_bd:
        try:
            dt = datetime.datetime.now().replace(microsecond=0)
            date_now = '{}-{}-{} {}:{}:{}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            
            if date_time_temperature == 0:
                hour = dt.hour - 1
                date_future = '{}-{}-{} {}:{}:{}'.format(dt.year, dt.month, dt.day, hour, dt.minute, dt.second)
            elif date_time_temperature == 1:
                day = dt.day - 1
                date_future = '{}-{}-{} {}:{}:{}'.format(dt.year, dt.month, day, dt.hour, dt.minute, dt.second)
            elif date_time_temperature == 2:
                month = dt.month - 1
                date_future = '{}-{}-{} {}:{}:{}'.format(dt.year, month, dt.day, dt.hour, dt.minute, dt.second)
            
            cursor = connector.cursor()
            cursor.execute('''SELECT * FROM data_temperature WHERE `date` BETWEEN \'{}\' AND \'{}\''''.format(date_future, date_now))
            result = cursor.fetchone()
            while result is not None:
                arry.append(result[1])
                arrx.append(result[2])
                arrmini.append(min_temperature)
                arrmax.append(max_temperature)
                result = cursor.fetchone()
        except:
            pass
    else:
        if len(arry) >= 100:
            arry.pop(0)
            arrx.pop(0)
            arrmax.pop(0)
            arrmini.pop(0)

#         arry.append(sensor.get_temperature())
        arry.append(random.gauss(25, 2))
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
anim = FuncAnimation(fig, animation, interval=1000)


def graph():
    global index_graph, arry, arrx
    if index_graph == 0:
        canvas.get_tk_widget().grid(row=11, column=1, columnspan=3)
        index_graph = 1
        bt_graph.configure(text='Убрать график')
    else:
        canvas.get_tk_widget().grid_forget()
        index_graph = 0
        bt_graph.configure(text='Вывести график')


def box_graph(box_i):
    global date_time_temperature
    if str(cb_graph.get()) == 'час':
        date_time_temperature = 0
    elif str(cb_graph.get()) == 'день':
        date_time_temperature = 1
    elif str(cb_graph.get()) == 'месяц':
        date_time_temperature = 2


lb_lamp = Label(text='Состояние освещения:')
lb_lamp_vv = Label()

lb_heating = Label(text='Состояния отопления: ')
lb_heating_vv = Label()

lb_heating_min = Label(text='Порог минимальной температуры: ')
lb_heating_min_size = Label(text=min_temperature)

lb_heating_max = Label(text='Порог максимальной температуры: ')
lb_heating_max_size = Label(text=max_temperature)

lb_heating_manipulate = Label(text='Изменить пороги температуры', font=20)
lb_heating_manipulate_min = Label(text='Минимальная температура').grid(row=6, column=1)
lb_heating_manipulate_max = Label(text='Максимальная температура').grid(row=7, column=1)
lb_heating_manipulate_error = Label()

lb_grahp = Label(text='Вывести график за последний')
cb_graph = ttk.Combobox(values=[u'час', u'день', u'месяц'])
cb_graph.set(u'час')
cb_graph.bind('<<ComboboxSelected>>', box_graph)

en_heating_manipulate_min = Entry(width=4)
en_heating_manipulate_max = Entry(width=4)

bt_heating_manipulate = Button(text='Подтвердить изменение', command=heating_manipulate)
bt_lamp_manipulate = Button(text='Включить свет', command=lamp_manipulate)
bt_graph = Button(text='Вывести график', command=graph)

lb_security_messenger = Label(text='В доме безопасно')




lb_lamp.grid(row=1, column=1)
lb_lamp_vv.grid(row=1, column=2)
lb_heating.grid(row=2, column=1)
lb_heating_vv.grid(row=2, column=2)
lb_heating_min.grid(row=3, column=1)
lb_heating_max_size.grid(row=3, column=2)
lb_heating_max.grid(row=4, column=1)
lb_heating_max_size.grid(row=4, column=2)
lb_heating_manipulate.grid(row=5, column=1, columnspan=2)

en_heating_manipulate_min.grid(row=6, column=2)
en_heating_manipulate_max.grid(row=7, column=2)
lb_heating_manipulate_error.grid(row=8, column=1, columnspan=2)

bt_lamp_manipulate.grid(row=9, column=3, columnspan=2)
bt_heating_manipulate.grid(row=9, column=1, columnspan=2)
bt_graph.grid(row=10, column=1)

lb_grahp.grid(row=10, column=2)
cb_graph.grid(row=10, column=3)

lb_security_messenger.grid(row=8, column=3)

GPIO.add_event_detect(pin_security, GPIO.BOTH, callback=send)

if __name__ == "__main__":
    root.mainloop()
    GPOI.cleanup()
