#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         create_test.rrd.bash
#h Type:         Linux shell script
#h Purpose:      (re-)creates the RRDTool database test.rrd
#h Project:      
#h Usage:        ./create_test.rrd.bash
#h Result:       
#h Examples:     https://www.kompf.de/cplus/emeocv.html
#h Outline:      
#h Resources:    rrdtool
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2022-12-13/peb
#v History:      V1.0.0 2022-11-20/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='create_test.rrd.bash';
VERSION='V1.0.0'
WRITTEN='2022-12-13/peb'

LOG="$0".log

PULL_CYCLE=45m
RRD_FILE=test.rrd

if [ -e ./$RRD_FILE ]
then
    rm $RRD_FILE
fi

C="rrdtool create $RRD_FILE \
   --no-overwrite \
   --step $PULL_CYCLE \
   DS:test:GAUGE:$PULL_CYCLE:U:U \
   RRA:LAST:0.5:1:1M"
echo $C
$C
chmod a+w $RRD_FILE

