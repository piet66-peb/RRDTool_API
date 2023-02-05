#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         sql_with_curl.bash
#h Type:         Linux shell script
#h Purpose:      
#h Project:      
#h Usage:        ./sql_with_curl.bash
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    RRDTool_API
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-24/peb
#v History:      V1.0.0 2022-12-09/peb first version
#h Copyright:    (C) piet66 2022
#h License:      MIT
#h
#h-------------------------------------------------------------------------------

MODULE='sql_with_curl.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-24/peb'

##parameters for rrdtool:
export RRD_NAME=daylight

##remote database:
export IP=192.168.178.22
export PORT=5001
export USER_PW=username:secret

#send data to RRDTool_API:
function sql_with_curl() {
    RRD_NAME=daylight
    FIRST="first + 1day - 0h"
    LAST="start + 1h"

    echo ''
    #encoding with curl:
    curl -sSN -o - -u  ${USER_PW} \
        http://$IP:$PORT/sql  \
        --get --data-urlencode "=select * from $RRD_NAME where ts > $FIRST and ts <= $LAST"
}

clear
sql_with_curl
echo ''

