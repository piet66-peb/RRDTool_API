#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         install_flask_rrdtool.bash
#h Type:         Linux shell script
#h Purpose:      install python and flask for RRDTool_API
#h Project:      
#h Usage:        copy folder to target place
#h               ./install_flask_rrdtool.bash
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Debian Linux (Raspberry Pi OS, Ubuntu)
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-01-01/peb
#v History:      V1.0.0 2022-11-27/peb first version
#h Copyright:    (C) piet66 2022
#h License:      http://opensource.org/licenses/MIT
#h
#h-------------------------------------------------------------------------------

MODULE='install_flask_rrdtool.bash';
VERSION='V1.0.0'
WRITTEN='2023-01-01/peb'

#exit when any command fails
#set -e

#set path constants
. `dirname $(readlink -f $0)`/00_constants

umask 000

# install rrdtool
sudo apt install rrdtool
sudo apt install librrd-dev libpython3-dev

# install python3
sudo apt install python3
python3 -V

#install pip3
sudo apt install -y python3-pip

#create and activate python environment
sudo apt install -y python3-venv
python3 -m venv $VIRTUAL_ENV
source $VIRTUAL_ENV/bin/activate

#newly create requirements.txt
#pip3 install pipreqs
#export PATH=$PATH:~/.local/bin
#pipreqs .

#install necessary packages
pip3 install -r requirements.txt
#python3 -c "import flask; print(flask.__version__)"

#display installed python packages
pip3 freeze

