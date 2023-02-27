#!/bin/bash
#
# Real Live Example
#
# The following example shows how to create a simple traffic grapher with a shell
# script for data acquisition, and an rrdcgi script to draw the graphs.
# source: https://tobi.oetiker.ch/ouce2013/handouts.pdf
#
# This little bash script polls the network traffic counter from the linux 
# proc tree and reformats it so that it can be fed to rrdtool.
#
# use from cron (crontab -e):
# * * * * * <path>/eth0_fill.bash

cd `dirname $0`

ETH0=eth0

if [ ! -f $ETH0.rrd ]; then
    rrdtool create $ETH0.rrd \
    --step=60 \
    DS:in:DERIVE:70:0:100000000 \
    DS:out:DERIVE:70:0:100000000 \
    RRA:AVERAGE:0.5:1:1500 \
    RRA:AVERAGE:0.5:60:10000 \
    RRA:MIN:0.5:60:10000 \
    RRA:MAX:0.5:60:10000 \
    RRA:AVERAGE:0.5:1440:1000 \
    RRA:MIN:0.5:1440:1000 \
    RRA:MAX:0.5:1440:1000
fi

rrdtool update $ETH0.rrd \
N:`grep $ETH0: /proc/net/dev | sed 's/.*://' | awk '{print $1":"$9}'`

