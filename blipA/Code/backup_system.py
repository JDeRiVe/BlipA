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
from own_tree import tree_node, find_children, get_parent, create_node_dict, find_active_node, find_siblings, find_next_sibling
from own_networking import get_host_ip, return_ESSID, check_AP_on

lcd_display = drivers.Lcd()



def load_menu_tree():
	file = open('/home/pi/devs/sigint/lcd_menu.csv')
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

	node_list.append(tree_node(ID='-1',parentID='root',node_string=get_host_ip(),
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
	buttons_input = read_buttons_input()
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

	return 0



#This the main body

menu = system_init()
app = Flask(__name__, static_folder='templates')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/Backlight_OFF')
def backlight_off():
	lcd_display.lcd_backlight(0)
	return render_template('webpage.html')

@app.route('/Backlight_ON')
def backlight_on():
	lcd_display.lcd_backlight(1)
	return render_template('webpage.html')

@app.route('/B')
def led2on():
	buttons_input(menu,'derecha')
	return render_template('webpage.html')

@app.route('/b')
def led2off():
	buttons_input(menu,'izquierda')
	return render_template('webpage.html')

@app.route('/C')
def led3on():
	buttons_input(menu,'arriba')
	return render_template('webpage.html')

@app.route('/c')
def led3off():
	buttons_input(menu,'abajo')
	return render_template('webpage.html')



if __name__=="__main__":
	print("Start")
	app.run(debug=True, host=get_host_ip())



#while True:
#	buttons_input(menu)

