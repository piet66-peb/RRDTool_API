#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         RRDTool_API.bash
#h Type:         Linux shell script
#h Purpose:      start flask/ rest_api for RRDTool database
#h Project:      
#h Usage:        ./RRDTool_API.bash
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-04/peb
#v History:      V1.0.0 2022-03-14/peb first version
#h Copyright:    (C) piet66 2022
#h License:      http://opensource.org/licenses/MIT
#h
#h-------------------------------------------------------------------------------

MODULE='RRDTool_API.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-04/peb'

# exit when any command fails
set -e

#set path constants
. `dirname $(readlink -f $0)`/00_constants >/dev/null

### uncomment this line for debug messages (single threaded)
#export FLASK_ENV=development

### define application
export FLASK_APP=$PACKET_NAME.py

### for change the default port 5000
export FLASK_RUN_PORT=$PORT

### listen for remote packets
export FLASK_RUN_HOST=0.0.0.0   # ipv4
#export FLASK_RUN_HOST=::        # ipv6

### run
LOG=$LOG_PATH/${PACKET_NAME}.log
flask run >>$LOG 2>&1

