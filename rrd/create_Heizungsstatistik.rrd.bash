#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         create_Heizungsstatistik.rrd.bash
#h Type:         Linux shell script
#h Purpose:      (re-)creates the RRDTool database Heizungsstatistik.rrd
#h Project:      
#h Usage:        ./create_Heizungsstatistik.rrd.bash
#h Result:       
#h Outline:      
#h Resources:    rrdtool
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-02-21/peb
#v History:      V1.0.0 2023-02-10/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='create_Heizungsstatistik.rrd.bash';
VERSION='V1.0.0'
WRITTEN='2023-02-21/peb'

LOG="$0".log

RRD_FILE=Heizungsstatistik.rrd
WRITE_CYCLE=1h   # step parameter

rm -f $RRD_FILE

C="rrdtool create $RRD_FILE  \
   --no-overwrite \
   --step $WRITE_CYCLE \

   DS:Brennerstarts:GAUGE:1d:U:U \
   DS:Brennerlaufzeit:GAUGE:1d:U:U \

   DS:Brennerstarts_Std:DERIVE:1d:0:U \
   DS:Brennerlaufzeit_Std:DDERIVE:1d:0:1 \

   RRA:LAST:0.5:1d:3M \
   RRA:AVERAGE:0.5:1d:3M \
   RRA:MIN:0.5:1d:3M \
   RRA:MAX:0.5:1d:3M \

   RRA:LAST:0.5:1d:3y \
   RRA:AVERAGE:0.5:1d:3y \
   RRA:MIN:0.5:1d:3y \
   RRA:MAX:0.5:1d:3y
  "
#echo $C
$C
chmod a+w $RRD_FILE

