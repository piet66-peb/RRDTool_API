#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         get_procid.bash
#h Type:         Linux shell script
#h Purpose:      reads the process id of daylight_status function
#h Project:      
#h Usage:        ./get_procid.bash
#h               kill process with:
#h                 kill <procid>
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-05/peb
#v History:      V1.0.0 2022-12-11/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='get_procid.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-05/peb'

. `dirname $(readlink -f $0)`/00_constants >/dev/null

PROC=$PACKET_NAME
ret=`ps -efj | egrep "$PROC" | grep -v grep | grep -v PGID`

echo ''
if [ "$ret" == "" ]
then    
    echo process $PROC is not started
else
    sudo systemctl status $PROC | cat
    echo ''
    echo stop processes $PROC with:
    echo "sudo systemctl stop $PROC"
fi

echo ''
echo '(re)start process with:'
echo "sudo systemctl start $PROC"
echo ''

