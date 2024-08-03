#!/usr/bin/python
from flask import Flask, render_template, Response, stream_with_context, redirect, flash
from flask_socketio import SocketIO, send, emit
import shlex, subprocess, json, random, time
from datetime import datetime
from own_networking import get_host_ip, check_AP_on, return_ESSID
from own_tree import buttons_input, system_init, write_lcd_menu, find_active_node, find_siblings, find_previous_sibling, find_next_sibling
import os, sys, shutil, drivers, glob, signal
import pandas as pd
from radio_library import init_adbs, datos_adsb
from radio_library import datos_satelite_init
from radio_library import init_radiosonda, datos_radiosonda


sys.path.append("/home/pi/devs/misc/lcd")

path_auto_rx = "/home/pi/test/radiosonde_auto_rx/auto_rx/"   #Path for radiosondes
path_dump1090 = "/home/pi/test/dump1090/"
path_satelite = "/home/pi/test/satelite/"
path_wxtoimg = "/home/pi/"

print("INITIALIZING...")
backlight = "ON"
menu = system_init()

display = drivers.Lcd()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

modo = "satelite_init"
contador_lineas=0
processes=[]

#-------------------------------UTILS------------------------------------------------

def configuracion_check():
    if check_AP_on():
        Configuracion = "AP ON"
    else:
        Configuracion = return_ESSID()
    return Configuracion

def mensaje_terminal():
    global modo
    global contador_lineas
    global display
    global processes
    global proc

    print("EL MODO DEL MENSAJE TERMINAL ES:")
    print(modo)
    limite_de_lineas = 15
    if modo=="reset":
        print("MODO RESET")
        print(processes)
        modo=""

    data=""
    if modo=="Radiosonda":
       data = datos_radiosonda(path_auto_rx, display, proc)

    if modo=="ADS-B (Avion)":
       data, proc = datos_adsb(path_dump1090, display)
       processes.append(proc)

    if modo=="satelite_init":
       data = datos_satelite_init(path_satelite, display)

    if modo=="reset":
        print("MODO RESET")
        print(processes)

    print(data)
    if not modo=="":
        if modo=="satelite_init":
           modo=""
        if contador_lineas<limite_de_lineas:
            json_data = json.dumps(
                    {"packet":"terminal", "data":data})
            emit("append_message",json_data, ignore_queue=True)
            contador_lineas=contador_lineas+1
        else:
            contador_lineas=0
            json_data = json.dumps(
                    {"packet":"terminal", "data":modo+"...&#13;&#10;"})
            emit("init_message",json_data)
        time.sleep(6)
    else:
            data=""
            #json_data = json.dumps(
            #        {"packet":"terminal", "data":modo+"...&#13;&#10;"})
            #emit("append_message",json_data, ignore_queue=True)
            time.sleep(6)


def posicion_actual():
    try:
        print(path_wxtoimg + ".wxtoimgrc")
        f=open(path_wxtoimg + ".wxtoimgrc")
        lineas = f.readlines()
        linea_latitud = lineas[0]
        linea_longitud = lineas[1]
        latitud=linea_latitud.split()
        longitud = linea_longitud.split()
        latit = str(latitud[1])
        longit = str(longitud[1])
        return latit, longit
    except:
        print("wxtoimg no esta instalado!")
        latit = 0
        longit = 0
        return latit, longit

#----------------------------------------------------FIN UTILS -----------------------------------



@app.route('/')
@app.route('/index')
def index():
    global menu
    global modo
    active_node = find_active_node(menu)
    print(active_node.node_string)
    siblings=find_siblings(menu,active_node)
    print(find_next_sibling(siblings,active_node).node_string)
    latit,longit = posicion_actual()
    connection_string='http://'+get_host_ip()+':5000'
    print("To connect, please use:", connection_string)
    return render_template('index.html', title='Home',
           Configuracion = configuracion_check(), host_ip_address=get_host_ip(),socket_addr=connection_string,
           previous_item = find_previous_sibling(siblings,active_node).node_string,
	   active=active_node.node_string,
           next_item=find_next_sibling(siblings,active_node).node_string, latit=latit, longit=longit)


socketio.on_event('terminal_event', mensaje_terminal)

@socketio.on("message")

def buttonpressed(message):
    print(message)
    global menu
    global modo
    global display
    global processes
    global proc
    if message == "connect_event":
        modo = "satelite_init"
        mensaje_terminal()

    print("DENTRO DE BUTTOM PRESSED. EL MODO ES")
    print(modo)
    if message == "terminal_event":
        mensaje_terminal()

    if message == "light":
        global backlight
        if backlight=="ON":
            display.lcd_backlight(0)
            backlight="OFF"
        else:
           display.lcd_backlight(1)
           backlight="ON"
    if message == "cuenta":
      print("TIMER ON")
      json_data = json.dumps({"packet":"web","data":"CUENTA ATRAS INICIADA!!&#13;&#10;--> Contando hacia atras&#13;&#10;"})
      emit("timer_message",json_data)
      command = "/home/pi/ops/startup/demo_clock.py"
      args = shlex.split(command)
      p = subprocess.Popen(args)
#      # p.wait()
      # send("<h1>Countdown completed...</h1>", broadcast=True)

    menu = buttons_input(menu, message)
    active_node = find_active_node(menu)
    siblings = find_siblings(menu,active_node)

    previous_item = find_previous_sibling(siblings,active_node).node_string,
    active=active_node.node_string,
    next_item=find_next_sibling(siblings,active_node).node_string

    json_data3 = json.dumps(
                {"packet":"status", "data":{'prenode': previous_item, 'activenode': active, 'postnode': next_item}})
    emit("status_message",json_data3)
    print(message)
    if message=="enter":
       print("inside enter")
       print(active[0])
       if active[0] == "Radiosonda":
           print("INIT RADIOSONDA")
           modo = "Radiosonda"
           data, proc = init_radiosonda(path_auto_rx, display)
           processes.append(proc)
           json_data = json.dumps(
                      {"packet":"terminal", "data":data})
           emit("init_message",json_data)

       if active[0] == "ADS-B (Avion)":
           modo = "ADS-B (Avion)"
           data, proc = init_adbs(path_dump1090, display, proc)
           processes.append(proc)
           json_data = json.dumps(
                      {"packet":"terminal", "data":data})
           emit("init_message",json_data)

    if message=="reset":
          print("THIS IS RESET")
          print(processes)
          for i in processes:
              os.kill(i.pid,signal.SIGINT)
          modo=""
          json_data = json.dumps(
                      {"packet":"terminal", "data":"Se ha ejecutado un Reset. El sistema se reiniciara ahora"})
          emit("init_message",json_data)
          time.sleep(5)
          os.system("sudo reboot now")

#STREAMING DOWN

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    print(form.username.data)
    if check_AP_on():
        Configuracion = "AP ON"
    else:
        Configuracion = return_ESSID()

    #print subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect('/index')
    return render_template('login.html', title='Sign In', form=form, Configuracion=Configuracion, host_ip_addr=get_host_ip())


#@app.route('/data_in')
def chart_data():
    def generate_random_data():
            global menu
            active_node = find_active_node(menu)
            siblings=find_siblings(menu,active_node)
            previous_item = find_previous_sibling(siblings,active_node).node_string,
            active=active_node.node_string,
            next_item=find_next_sibling(siblings,active_node).node_string
            json_data = json.dumps(
                {'prenode': previous_item, 'activenode': active, 'postnode': next_item})
            yield f"data:{json_data}\n\n"

    response = Response(stream_with_context(generate_random_data()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

print("STARTING...")
if __name__ == '__main__':
    socketio.run(app, host=get_host_ip())

