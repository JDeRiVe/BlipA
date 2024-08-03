# BlipA
This is an ongoing project and I am not maintaining the documentation or having the code well commented (use it at your own risk). 
The goal is to use an RTL-SDR (software defined radio) and a raspberry-pi 1B to supercharge it with applications to read different radio-signals and be able to operate it with a cellphone or a tablet. In the future, my idea is that the RPi will also have a Moddle server to provide an interactive learning experience, so at some point it can be used as cheap educational resource to teach radio-stuff, electronics. This little thing can be used to downlink pictures from some NOAA satellites (which for kids is awesome and for remote areas without coverage can be used to understand whether clouds or a hurricane is coming)😊

The Rpi is setup in headless mode and gives a flask front-end to call the different functions. I have also attached a LCD (totally retro!) so I can see whether the communication is going well between the front-end and the Rpi.
Here there are the STL files for the case. There is space for the LCD and another space to get the cables to the GPIO out of the case and keeping the tied to the Rpi.

The (very) messy code for the flask frontend, I implemented a tree class for the menu display in the LCD, so the navigation is simple, where the functions are at the base of the tree.

For the moment, I am using it to find the position of radiosondes and passes of meteorological satellites (NOAA) but there are many other things that can be listened to, such as airplanes, trains, ship positions,..

The way to operate the frontend is easy, up-down to move for the nodes at the same level, left-right to go up and down in the tree, when at the bottom of the tree, enter to execute the command. A button for turning on and off the LCD backlight, another for running a countdown like in the LCD (not really counting seconds) and another one to reboot the Rpi.

Needless to say, you need the RTL-SDR driver for the Rpi.

I did this because I love tinkering with stuff, but if you are interested in amateur radio with a RPi, you will be better off here: [Raspberry Pi for HAM Radio – Projets radio](https://hamprojects.wordpress.com/2020/09/06/raspberry-pi-for-ham-radio/)
