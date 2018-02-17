#!/usr/bin/env python


# This Nagios plugin reads temperature data from a DS18b20 temperature sensor
# connected to a Raspberry Pi and sends Nagios state and performance data. I
# assembled this plugin for use with the waterproof version of the DS18b20, as
# a compost pile monitor. The hotter the pile runs, the faster it is making
# dirt. Nagios alerts me when pile temperature falls below thresholds, so I
# know when to turn the pile.



# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.




import os
import glob
import time
import sys
import argparse


# This section allows the input of command line parameters from Nagios like -w
# and -c. For this plugin values are floats.

parser = argparse.ArgumentParser(description='A compost-optimized Nagios plugin for the DS18b20 waterproof termperature sensor.')
parser.add_argument('-w', '--warning', type=float, required=True, help='temperature below which you want a warning alert')
parser.add_argument('-c', '--critical', type=float, required=True, help='temperature below which you want a critical alert')
parser.add_argument('--version', action='version', version='version 0.1')


# This is the exception handler for the argument parser. It works pretty well if
# all you care about is how the output looks in the Nagios interface.
# The only downside, besides having to listen to people tell you that you
# shouldn't use a blank except, is that it prints "Unexpected command line input"
# after it prints --help, and after it prints --version. But I don't super care
# about that because it works as far as I need for a compost monitor.

try:
    args = parser.parse_args()
except:
    print 'Unexpected command line input'
    sys.exit(3)


# This section is a check that the critical threshold is less than the warning
# threshold. Since the best state for making fast compost is hot, I want to be
# notified when the temperature falls below thresholds. The OK state is for the
# hottest pile temp, warning is middle temp, critical is coldest.

if (args.critical) > (args.warning):
    print 'Error: warning value must be greater than critical value'
    sys.exit(3)


# let the operating system know we are going to gpio

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


# the next three sections are based on code from this adafruit article
# https://cdn-learn.adafruit.com/downloads/pdf/adafruits-raspberry-pi-lesson-
# 11-ds18b20-temperature-sensing.pdf
#
# find the driver command that fetches the temp

therm_dir = '/sys/bus/w1/devices/'

try:
    unit_dir = glob.glob(therm_dir + '28*')[0]
except:
    print 'No device detected.'
    sys.exit(3)

unit_file = unit_dir + '/w1_slave'


# ask the device to read the temperature and return the data

def read_temp_hex():
    f = open(unit_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


# parse the data

def read_temp():
    lines = read_temp_hex()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_hex()

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f


# We're back to code I wrote.
# Here we compare the temp data to our thresholds, and return state info and
# perf data, with the appropriate exit code

if read_temp() < args.critical:
    print 'Critical Temp ',(read_temp()),' F |',(read_temp())
    sys.exit(2)
elif read_temp() < args.warning:
    print 'Warning Temp ',(read_temp()),' F |',(read_temp())
    sys.exit(1)
else:
    print 'OK Temp ',(read_temp()),' F |',(read_temp())
