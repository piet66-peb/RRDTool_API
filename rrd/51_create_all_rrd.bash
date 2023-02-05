#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         create_all_rrd.bash
#h Type:         Linux shell script
#h Purpose:      creates all rrd database files in current folder
#h Project:      
#h Usage:        ./create_all_rrd.bash
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-01/peb
#v History:      V1.0.0 2022-11-20/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='create_all_rrd.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-01/peb'

for f in create_*.rrd.bash
do
 echo "running $f..."
 "./$f"
done

