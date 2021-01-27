#!/bin/bash
# Source: http://alexba.in/blog/2015/01/14/automatically-reconnecting-wifi-on-a-raspberrypi/

# The IP for the server you wish to ping (8.8.8.8 is a public Google DNS server)
SERVER=8.8.8.8

# Only send three pings, sending output to /dev/null
ping -c3 ${SERVER} > /dev/null

# If the return code from ping ($?) is not 0 (meaning there was an error)
if [ $? != 0 ]
then
    # Restart the wireless interface
    ifdown --force wlan0
    ifup wlan0
fi
