#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         install_RRDTool_API.bash
#h Type:         Linux shell script
#h Purpose:      installs RRDTool_API parts
#h               starts API
#h Project:      
#h Usage:        copy folder to target place
#h               ./install_RRDTool_API.bash
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Debian Linux (Raspberry Pi OS, Ubuntu)
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-22/peb
#v History:      V1.0.0 2022-11-27/peb first version
#h Copyright:    (C) piet66 2022
#h License:      http://opensource.org/licenses/MIT
#h
#h-------------------------------------------------------------------------------

MODULE='install_RRDTool_API.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-22/peb'

# exit when any command fails
set -e

#set path constants
. `dirname $(readlink -f $0)`/00_constants

umask 000

#change logrotate config
file=$PACKET_NAME
sudo chmod a+w $file
sudo sed -i "s|^.* {|$LOG_PATH/$PACKET_NAME.log {|" $file

#copy config for logrotate
TARGET=/etc/logrotate.d
echo sudo rm -f "$TARGET/$file"
sudo rm -f "$TARGET/$file"
echo sudo cp $PACKET_PATH/$file "$TARGET/$file"
sudo cp $PACKET_PATH/$file "$TARGET/$file"
sudo chown root $LOG_PATH
sudo chgrp root $LOG_PATH
sudo chmod 644 "$TARGET/$file"

#change systemd config
file=$PACKET_NAME.service
sudo chmod a+w $file
sudo sed -i "s|WorkingDirectory=.*$|WorkingDirectory=$PACKET_PATH|" $file
sudo sed -i "s|ExecStart=.*$|ExecStart=$PACKET_PATH/$PACKET_NAME.bash|" $file

#service definition for systemd
TARGET=/etc/systemd/system
echo sudo rm -f "$TARGET/$file"
sudo rm -f "$TARGET/$file"
echo sudo cp $PACKET_PATH/$file "$TARGET/$file"
sudo cp $PACKET_PATH/$file "$TARGET/$file"
sudo chmod 644 "$TARGET/$file"

#start API
echo sudo systemctl daemon-reload
sudo systemctl daemon-reload
echo sudo systemctl reset-failed
sudo systemctl reset-failed

echo sudo systemctl enable $PACKET_NAME
sudo systemctl enable $PACKET_NAME
echo sudo systemctl start $PACKET_NAME
sudo systemctl start $PACKET_NAME
echo ''
sudo systemctl status $PACKET_NAME

