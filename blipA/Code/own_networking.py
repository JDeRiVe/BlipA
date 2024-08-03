#! /bin/python3

import subprocess # executes shell commands and allows piping the output
import sys #execute commands and handle paths
import os # execute commands
import time

def get_host_ip():
	result = subprocess.Popen(["ifconfig wlan0 |  grep -o -P '.inet .{0,15}'"], shell=True, stdout=subprocess.PIPE).stdout
	a=result.read().decode()
	host_ip_address =a[6:-1].strip()
	return host_ip_address

def return_ESSID():
	cmd = "iwconfig wlan0|grep ESSID|cut -d ':' -f 2"
	ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	time.sleep(10)
	output = ps.communicate()[0][:-2].decode('utf-8')
	try:
		if output[0]=='"':
			return output[1:-2]
	except:
		print('there has been an issue detecting AP')
	print('System not able to detect WLAN - resorting to AP mode')
	os.system('sudo service wpa_supplicant stop')
	os.system('sudo /home/pi/devs/scripts/APconfig.sh ON')
	return 'resorting to AP'

def check_AP_on():
	p1 = subprocess.Popen(['service','hostapd','status'],stdout=subprocess.PIPE)
	try:
		result_grep = subprocess.check_output(['grep','running'],stdin=p1.stdout)
	except:
		print('AP OFF')
		return False
	else:
		print('AP ON')
		return True

