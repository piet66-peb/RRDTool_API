#!/bin/bash
#h-------------------------------------------------------------------------------
#h
#h Name:         run_cgi.bash
#h Type:         Linux shell script
#h Purpose:      creates a webpage using rrdtool rrdcgi
#h Project:      
#h Usage:        run_cgi.bash <cgi-file> [TZ='..'] 
#h Result:       
#h Examples:     
#h Outline:      
#h Resources:    
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.0.0 2023-04-04/peb
#v History:      V1.0.0 2023-02-25/peb first version
#h Copyright:    (C) piet66 2023
#h License:      http://opensource.org/licenses/MIT
#h
#h-------------------------------------------------------------------------------

MODULE='run_cgi.bash';
VERSION='V1.0.0'
WRITTEN='2023-04-04/peb'

cd `dirname $0`
CGI_FIL=`basename $1`

#run as cgi:
[ "$2" != "" ] && export $2
rrdcgi -f $CGI_FIL

#run manually:
#HTML_FIL=$CGI_FIL.html
#echo -ne '\x04' | rrdcgi -f $CGI_FIL >>$HTML_FIL


