import shutil, drivers, glob, os, sys, shlex, subprocess, json, random, time, datetime
import pandas as pd

sys.path.append("/home/pi/devs/misc/lcd")


#****************** UTILS **************************
def move_logs(source_dir, target_dir):
    file_names = os.listdir(source_dir)
    for file_name in file_names:
        shutil.move(os.path.join(source_dir, file_name), target_dir)


def file_expired(path_to_file, filename, refresh_time):
#refresh time in hours, returns True if file is older than refresh time
    refresh_time_seconds = refresh_time * 60 * 60 #hours to minutes to seconds
    current_time_seconds = time.time()
    try:
       filedata = os.stat(path_to_file+filename)
    except:
       return True #file does not exist, need a new one
    if (current_time_seconds > (filedata.st_mtime+refresh_time_seconds)):
        return True
    else:
        return False


#***************RADIOSONDAS**************************

def leer_log_sonda(log_sonda):
    df = pd.read_csv(log_sonda)
    ultimo = len(df.lat)-1
    latit = df.lat[ultimo]
    longi = df.lon[ultimo]
    tipo = df.serial[ultimo][:7]
    return tipo, str(latit), str(longi)


def init_radiosonda(path_auto_rx, display):
    display.lcd_clear()
    display.lcd_display_string("BUSCANDO",1)
    display.lcd_display_string("RADIOSONDA...",2)
    auto_rx = "python " + path_auto_rx + "auto_rx.py -t 180"
    os.chdir(path_auto_rx)
    args=shlex.split(auto_rx)
    print("Moving old logs...")
    source_dir = path_auto_rx+"log/"
    target_dir = path_auto_rx+"old_log/"
    move_logs(source_dir, target_dir)
    print("Capturando paquetes de radiosondas")
    proc = subprocess.Popen(auto_rx, shell=True)
    time.sleep(20)
           #llamar a un procedimiento solo para enviar el mensaje a ver si asi va
    data="RADIOSONDA...&#13;&#10;"

    return data, proc


def datos_radiosonda(path_auto_rx, display, proc):
    source_dir = path_auto_rx+"log/"
    os.chdir(source_dir)
    filenames = os.listdir(source_dir)
    if filenames:
       if len(filenames)==2:
           proc.kill()
           sonda_log_filename = glob.glob(source_dir+"*sonde.log")
           print(sonda_log_filename[0])
           sonda,latit,longi = leer_log_sonda(sonda_log_filename[0])
           data = "Sonda "+sonda+" detectada en lat,lon: "+latit+", "+longi+"&#13;&#10;"
           display.lcd_clear()
           display.lcd_display_string(sonda[:3]+" Lat:"+latit,1)
           display.lcd_display_string("    Lon:"+longi,2)
       else:
           print(filenames[0])
           command = "tail -n 1 "
           cmd = command+filenames[0]
           term_proc = subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)
           stdout_p,sterr_p = term_proc.communicate()
           lines=stdout_p.decode("utf-8").replace("\n","&#13;&#10;")
           print("PRE DATA CHUNK.....")
           print("DATA CHUNK...............")
           print(lines)
           data = lines #str(lines.read().decode("utf-8").replace("\n","&#13;&#10;"))
            #data=data[-80:]
           filenames = os.listdir(source_dir)
    else:
       data=""
    return data



#*************************ADS-B************************************

def init_adbs(path_dump1090, display, proc):
    dump1090 = path_dump1090 + "dump1090 --interactive >> ./log/dump.log"
    os.chdir(path_dump1090)
    args=shlex.split(dump1090)
    print("Moving old logs...")
    source_dir = path_dump1090+"log/"
    target_dir = path_dump1090+"old_log/"
    move_logs(source_dir, target_dir)
    print("Capturando paquetes de ADS-B (Avion)")
    proc = subprocess.Popen(dump1090, shell=True)
    time.sleep(20)
           #llamar a un procedimiento solo para enviar el mensaje a ver si asi va
    data="ADS-B (Avion)...&#13;&#10;"
    return data, proc

def datos_adsb(path_dump1090, display):
    source_dir = path_dump1090+"log/"
    os.chdir(source_dir)
    filenames = os.listdir(source_dir)
    if filenames:
       print(filenames[0])
       command = "tail -n 6 "
       cmd = command+filenames[0]
       term_proc = subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)
       stdout_p,sterr_p = term_proc.communicate()
       lines=stdout_p.decode("utf-8").replace("\n","&#13;&#10;")
       print("PRE DATA CHUNK.....")
       #lines = Tail(logfile)
       print("DATA CHUNK...............")
       print(lines)
       data = lines #str(lines.read().decode("utf-8").replace("\n","&#13;&#10;"))
            #data=data[-80:]
    else:
        data =""

    return data





#***************************SATELITE**********************************************

def datos_satelite(prediccion):
   lineas = prediccion.splitlines()
   linea_inicio = lineas[0]
   linea_final = lineas[-1]
   linea_max_elevacion = lineas[round(len(lineas)/2)]
   el = linea_max_elevacion.split()[4]
   az = linea_max_elevacion.split()[5]
   inicio_pase = linea_inicio.split()[2] + " " + linea_inicio.split()[3]
   fin_pase = linea_final.split()[2] + " " + linea_final.split()[3]
   fin_segundos = linea_final.split()[0]
   return inicio_pase, fin_pase, el, az, fin_segundos


def procesar_satelite(prediccion):
    print(prediccion)
    if prediccion:
        inicio_pase, fin_pase, el, az, fin_segundos = datos_satelite(prediccion)
        inicio = "-> Inicio:" + inicio_pase + " UTC"
        fin = "Fin:" + fin_pase +" UTC"
        if int(el)<10:
            el=" " +el
        max_elevacion = "  Elev:" + el  #tab to align Elev and Az
        max_azimuth = "  Az:" + az
    else:
        inicio = "No hay mas pases hoy."
        fin = ""
        max_elevacion = ""
        max_azimuth = ""
        fin_segundos = ""

    return inicio, fin, max_elevacion, max_azimuth, fin_segundos

def datos_satelite_init(path_satelite, display):
    source_dir = path_satelite+"log/"
    os.chdir(source_dir)
    filenames = os.listdir(source_dir)
    if file_expired(path_satelite, "active.txt", 4): #si el fichero tiene mas de cuatro horas
        print(filenames[0])
        command = path_satelite+"update_tle.sh"
        print(command)
        cmd = command
        print("Retrieving new satellite ephemerides")
        term_proc = subprocess.Popen(shlex.split(cmd), shell=True)
        term_proc.wait()
    else:
        print("Satelite ephemerides are still fresh")

    start=""
    sat_prediction=""
    contador=0
    while contador<3:
        if start:
            command = "/usr/bin/predict -t "+source_dir+'weather.tle -p "NOAA 15" '+ str(int(start)+60)
        else:
            command = "/usr/bin/predict -t "+source_dir+'weather.tle -p "NOAA 15" '
        cmd = command
        term_proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        stdout_p, stderr_p = term_proc.communicate()
        inicio, fin, max_elevacion, max_azimuth, start = procesar_satelite(stdout_p.decode('UTF-8'))
        sat_prediction = sat_prediction + "NOAA-15 " + inicio + " " + fin +  max_elevacion +  max_azimuth + "&#13;&#10;"
        if fin=="":
           contador=3
        else:
           contador=contador+1
    print(sat_prediction)

    start=""
    contador=0
    while contador<3:
        if start:
            command = "/usr/bin/predict -t "+source_dir+'weather.tle -p "NOAA 18" '+ str(int(start)+60)
        else:
            command = "/usr/bin/predict -t "+source_dir+'weather.tle -p "NOAA 18" '
        cmd = command
        print(command)
        term_proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        stdout_p, stderr_p = term_proc.communicate()
        print(stdout_p)
        inicio, fin, max_elevacion, max_azimuth, start = procesar_satelite(stdout_p.decode('UTF-8'))
        sat_prediction = sat_prediction + "NOAA-18 " + inicio + " " + fin +  max_elevacion +  max_azimuth + "&#13;&#10;"
        if fin=="":
           contador=3
        else:
           contador=contador+1

    print(sat_prediction)
    start=""
    contador=0
    while contador<3:
        if start:
            command = "/usr/bin/predict -t "+source_dir+'weather.tle -p "NOAA 19" '+ str(int(start)+60)
        else:
            command = "/usr/bin/predict -t "+source_dir+'weather.tle -p "NOAA 19" '
        cmd = command
        term_proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        stdout_p, stderr_p = term_proc.communicate()
        inicio, fin, max_elevacion, max_azimuth, start = procesar_satelite(stdout_p.decode('UTF-8'))
        sat_prediction = sat_prediction + "NOAA-19 " + inicio + " " + fin +  max_elevacion +  max_azimuth + "&#13;&#10;"
        if fin=="":
           contador=3
        else:
           contador=contador+1

    print(sat_prediction)
    lines="&#13;&#10;Proximos pases de satelites meteorologicos...&#13;&#10;"+sat_prediction #.de>        print("PRE DATA CHUNK.....")
    #lines = Tail(logfile)
    print("DATA CHUNK...............")
    print(lines)
    data = lines  

    return data
