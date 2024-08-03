#! /bin/python3

import subprocess # executes shell commands and allows piping the output
import csv # read the file describing the menu for the LCD
import sys #execute commands and handle paths
import os # execute commands
sys.path.append("/home/pi/devs/misc/lcd") #Path of the LCD drivers
import drivers #drivers of the 16x2 LCD display
import RPi.GPIO as GPIO
import time
from flask import Flask
from flask import render_template

lcd_display = drivers.Lcd()
global path_menu

path_menu = '/home/pi/devs/sigint/lcd_menu.csv'


class tree_node:
	def __init__(self, parentID='',ID='root',node_string='root',node_call='empty',node_children=[],active=False):
		self.parentID = parentID
		self.ID = ID
		self.node_string = node_string
		self.node_call = node_call
		self.active = active
		self.node_children = node_children



def find_char(str,ch):
	pos_char = []
	k = -1
	for i in str:
		k = k + 1
		if i==ch:
			pos_char.append(k)
	return pos_char



def get_parent(str):
	pos_dot = find_char(str,'.')

	if len(pos_dot)==0:
		return 'root'
	else:
		return str[:pos_dot[-1]]


def find_children(csv_rows_list,ID):
	candidates = []
	children = []

	for i in range(len(csv_rows_list)):
		if len(csv_rows_list[i][0])>len(ID):
			candidates.append(i)

	for i in candidates:
		if get_parent(csv_rows_list[i][0])==ID:
			children.append(csv_rows_list[i][0])

	return children


def create_node_dict(node_list):
	node_dict={}
	k = 0
	for i in range(len(node_list)):
		node_dict[node_list[i].ID]=k
		k = k+1

	return node_dict


def load_menu_tree():
	file = open(path_menu)
	csvreader = csv.reader(file)
	rows = []
	node_list = []
	root_node = tree_node()
	node_list.append(root_node)
	if check_AP_on():
		AP_str='AP ON'
	else:
		output=return_ESSID()
		if not (output=='resorting to AP'):
			AP_str=output
		else:
			AP_str='AP ON'

	node_list.append(tree_node(ID='0',parentID='root',node_string="C:"+AP_str,
                                node_call='empty',node_children=[],
                                active=False))

	for row in csvreader:
        	rows.append(row)

	for i in range(len(rows)):
		nd_ID = rows[i][0]
		nd_str = rows[i][1]
		nd_call = rows[i][2]
		node_list.append(tree_node(ID=nd_ID,parentID=get_parent(nd_ID),node_string=nd_str,
				node_call=nd_call,node_children=find_children(rows,nd_ID),
				active=False))

	node_dict = create_node_dict(node_list)
	node_list[node_dict['0']].active = True

	root_node_children=[]
	for i in range(len(node_list)):
		if node_list[i].parentID=='root':
			root_node_children.append(node_list[i].ID)

	node_list[0].node_children=root_node_children
	menu = [node_list,node_dict]
	return menu

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


def get_lcd_string(node):
	lcd_string = []
	for i in range(16):
		if (i==15):
			if len(node.node_children)>0:
				lcd_string.append('>')
				return lcd_string

			if (len(node.node_string)==16):
				lcd_string.append(node_string[-1])
				return lcd_string
			else:
				lcd_string.append(' ')
				return lcd_string
		else:
			if (i+1)>len(node.node_string):
				lcd_string.append(' ')
			else:
				lcd_string.append(node.node_string[i])


def find_next_sibling(siblings,active):
	next_sibling=[]
	flag = 0
	for i in range(len(siblings)):
		if flag == 1:
			return siblings[i]

		if siblings[i].ID==active.ID:
			flag = 1
			if i==(len(siblings)-1):
				return siblings[0]


def find_previous_sibling(siblings,active):
	next_sibling=[]
	flag = 0
	for i in range(len(siblings)-1,-1,-1):
		if flag == 1:
			return siblings[i]
		if siblings[i].ID==active.ID:
			flag = 1
			if i==0:
				return siblings[-1]


def find_active_node(menu):
	for i in range(len(menu[0])):
		if menu[0][i].active:
			return menu[0][i]

def find_siblings(menu, active):
	siblingsIDs = menu[0][menu[1][active.parentID]].node_children
	siblings = []
	for i in range(len(siblingsIDs)):
		siblings.append(menu[0][menu[1][siblingsIDs[i]]])

	return siblings



def write_lcd_menu(menu):
	active_node = find_active_node(menu)
	lcd_string = get_lcd_string(active_node)
	lcd_display.lcd_display_string(lcd_string, 1)
	siblings = find_siblings(menu,active_node)
	if len(siblings)==1:
		lcd_display.lcd_display_string('   ***VACIO***  ', 2)
	else:
		next_sibling = find_next_sibling(siblings,active_node)
		lcd_string = get_lcd_string(next_sibling)
		lcd_display.lcd_display_string(lcd_string, 2)


def system_init():
	menu = load_menu_tree()
	write_lcd_menu(menu)

	return menu

def buttons_input(menu,buttons_input):
	active_node = find_active_node(menu)
	if buttons_input=='derecha':
		if len(active_node.node_children)>0:
			menu[0][menu[1][active_node.ID]].active = False
			childrenIDs = active_node.node_children
			menu[0][menu[1][childrenIDs[0]]].active = True
		write_lcd_menu(menu)

	elif buttons_input=='izquierda':
		if not (active_node.parentID=='root'):
			menu[0][menu[1][active_node.ID]].active = False
			parentID = active_node.parentID
			menu[0][menu[1][parentID]].active = True
		write_lcd_menu(menu)
	elif buttons_input=='abajo':
		siblings = find_siblings(menu,active_node)
		next_sibling = find_next_sibling(siblings,active_node)
		menu[0][menu[1][active_node.ID]].active = False
		menu[0][menu[1][next_sibling.ID]].active = True
		write_lcd_menu(menu)
	elif buttons_input=='arriba':
		siblings = find_siblings(menu,active_node)
		previous_sibling = find_previous_sibling(siblings,active_node)
		menu[0][menu[1][active_node.ID]].active = False
		menu[0][menu[1][previous_sibling.ID]].active = True
		write_lcd_menu(menu)
	elif buttons_input=='accion':
		print('Accion!!!!')

	return menu


