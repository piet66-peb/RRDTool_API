#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         get_procid.bash
#h Type:         Linux shell script
#h Purpose:      gets the process, displays start/ stop command
#h Project:      
#h Usage:        ./get_procid.bash
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-02-23/peb
#v History:      V1.0.0 2022-12-11/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='get_procid.bash';
VERSION='V1.0.0'
WRITTEN='2023-02-23/peb'

. `dirname $(readlink -f $0)`/00_constants >/dev/null

PROC=$PACKET_NAME
systemctl is-active --quiet "$PROC"

if [ $? -ne 0 ]
then    
    user=`systemctl show -pUser $PROC`
    echo ''
    echo process $PROC, $user is not started
else
    echo ''
    systemctl status $PROC | cat
    systemctl show -pUser $PROC
    echo ''
    echo stop process with:
    echo "sudo systemctl stop $PROC"
fi

echo ''
echo 'start process with:'
echo "sudo systemctl start $PROC"
echo ''

