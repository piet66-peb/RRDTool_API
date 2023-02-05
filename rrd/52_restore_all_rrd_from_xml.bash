#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         restore_all_rrd.bash
#h Type:         Linux shell script
#h Purpose:      restores rrd database files from all existing xml files in
#h               current folder
#h               if rrd file is already existing, it is overwritten
#h Project:      
#h Usage:        ./restore_all_rrd.bash [<xml-file>]
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-24/peb
#v History:      V1.0.0 2022-11-20/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='restore_all_rrd.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-24/peb'

f=$1

if [ "$f" != "" ]
then
    echo "restoring $f..."
    echo rrdtool restore "$f" "${f%.*}.rrd"  -f
    rrdtool restore "$f" "${f%.*}.rrd"  -f
else
    for f in *.xml
    do
        echo "restoring $f..."
        echo rrdtool restore "$f" "${f%.*}.rrd"  -f
        rrdtool restore "$f" "${f%.*}.rrd"  -f
    done
fi

