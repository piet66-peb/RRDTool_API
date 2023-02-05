#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         create_electric_meter.rrd.bash
#h Type:         Linux shell script
#h Purpose:      (re-)creates the RRDTool database electric_meter.rrd
#h Project:      
#h Usage:        ./create_electric_meter.rrd.bash
#h Result:       
#h Examples:     https://www.kompf.de/cplus/emeocv.html
#h Outline:      
#h Resources:    rrdtool
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-05/peb
#v History:      V1.0.0 2022-11-20/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='create_electric_meter.rrd.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-05/peb'

LOG="$0".log

PULL_CYCLE=10m   # 10 minutes (see sleep --help)
RRD_FILE=electric_meter.rrd

if [ -e ./$RRD_FILE ]
then
    rm $RRD_FILE
fi

C="rrdtool create $RRD_FILE \
   --no-overwrite \
   --step $PULL_CYCLE \
   DS:reading:GAUGE:1d:0:U \
   DS:consumption:DERIVE:1d:0:U \
   RRA:LAST:0.5:1:1M \
   RRA:AVERAGE:0.5:1:1M \
   RRA:LAST:0.5:1h:3M \
   RRA:AVERAGE:0.5:1h:3M \
   RRA:LAST:0.5:1d:3y \
   RRA:AVERAGE:0.5:1d:3y"
echo $C
$C
chmod a+w $RRD_FILE

