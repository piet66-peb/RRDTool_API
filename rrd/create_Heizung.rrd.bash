#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         create_Heizung.rrd.bash
#h Type:         Linux shell script
#h Purpose:      (re-)creates the RRDTool database Heizung.rrd
#h Project:      
#h Usage:        ./create_Heizung.rrd.bash
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

MODULE='create_Heizung.rrd.bash';
VERSION='V1.0.0'
WRITTEN='2023-02-21/peb'

LOG="$0".log

RRD_FILE=Heizung.rrd
WRITE_CYCLE=10m   # step parameter

rm -f $RRD_FILE

C="rrdtool create $RRD_FILE  \
   --no-overwrite \
   --step $WRITE_CYCLE \
   DS:Aussentemperatur:GAUGE:1d:U:U \
   DS:Waermebedarf:GAUGE:1d:U:U \
   DS:Offene_Ventile:GAUGE:1d:0:U \

   DS:Betriebsprogramm:GAUGE:1d:0:1 \
   DS:Niveau:GAUGE:1d:0:U \
   DS:Neigung:GAUGE:1d:0:U \
   DS:Raumsolltemperatur:GAUGE:1d:0:U \

   DS:Vorlauf_Soll:GAUGE:1d:0:U \
   DS:Vorlauf_Ist:GAUGE:1d:0:U \
   DS:Kesseltemperatur:GAUGE:1d:0:U \

   DS:Pumpe:GAUGE:1d:0:1 \
   DS:Brenner:GAUGE:1d:0:1 \

   RRA:LAST:0.5:1:1M \
   RRA:AVERAGE:0.5:1:1M \
   RRA:MIN:0.5:1:1M \
   RRA:MAX:0.5:1:1M \

   RRA:LAST:0.5:1h:3M \
   RRA:AVERAGE:0.5:1h:3M \
   RRA:MIN:0.5:1h:3M \
   RRA:MAX:0.5:1h:3M \

   RRA:LAST:0.5:1d:3y \
   RRA:AVERAGE:0.5:1d:3y \
   RRA:MIN:0.5:1d:3y \
   RRA:MAX:0.5:1d:3y
  "
#echo $C
$C
chmod a+w $RRD_FILE

