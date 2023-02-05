#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         stp_API.bash
#h Type:         Linux shell script
#h Purpose:      stops API
#h Project:      
#h Usage:        ./stp_API.bash
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

MODULE='stp_API.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-01/peb'

. `dirname $(readlink -f $0)`/00_constants >/dev/null

echo stopping packet $PACKET_NAME...
echo ''
sudo systemctl stop  $PACKET_NAME
sudo systemctl status $PACKET_NAME | cat

