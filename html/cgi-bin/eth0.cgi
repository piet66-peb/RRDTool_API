#!/usr/bin/env rrdcgi
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
   <head>
      <meta charset="utf-8">
      <title>Traffic Statistics for eth0</title>
   </head>

   <body>
      <table>
         <tr>
            <td> <a href='/html/'> <p style="color:blue;"><u>Index</u></p> </a> </td>
            <td> <a  id ="e1" href="http//jjjj"> <p style="color:blue;"><u>Refresh</u></p> </a> </td>
         </tr>
      </table>
      <script>
          document.getElementById("e1").setAttribute("href", window.location);
      </script>
      <h1>Traffic Statistics for eth0</h1>
      <a href='https://tobi.oetiker.ch/ouce2013/'>
         <p style="color:blue; font-size: 100%;">
            <u>Source: https://tobi.oetiker.ch/ouce2013/handouts.pdf</u></p></a>
      It's an example for the use of rrdcgi. Use script rrd/eth0_fill.bash to fill
      the database eth0.rrd with traffic data.

      <h2>The Bytes</h2>
      <table border="1" cellspacing="0" cellpadding="2">
         <tr>
            <td>Period</td>
            <td>Incoming</td>
            <td>Outgoing</td>
            <td>Total</td>
         </tr>
         <!--
            <RRD::GRAPH -
            --start="midnight"
            --end="start+24h"
            DEF:in=../../rrd/eth0.rrd:in:AVERAGE:step=1800
            DEF:out=../../rrd/eth0.rrd:out:AVERAGE:step=1800
            VDEF:is=in,TOTAL
            PRINT:is:"%0.2lf %s"
            VDEF:os=out,TOTAL
            PRINT:os:"%0.2lf %S"
            CDEF:sum=in,out,+
            VDEF:ss=sum,TOTAL
            PRINT:ss:"%0.2lf %S"
            >
            -->
         <tr>
            <td><RRD::TIME::NOW %Y-%m-%d></td>
            <td align="right">
               <RRD::PRINT 0>
            </td>
            <td align="right">
               <RRD::PRINT 1>
            </td>
            <td align="right">
               <RRD::PRINT 2>
            </td>
         </tr>
         <!--
            <RRD::GRAPH -
            --start="<RRD::TIME::NOW %Y%m01>"
            --end="now"
            DEF:in=../../rrd/eth0.rrd:in:AVERAGE:step=1800
            DEF:out=../../rrd/eth0.rrd:out:AVERAGE:step=1800
            VDEF:is=in,TOTAL
            PRINT:is:"%0.2lf %s"
            VDEF:os=out,TOTAL
            PRINT:os:"%0.2lf %S"
            CDEF:sum=in,out,+
            VDEF:ss=sum,TOTAL
            PRINT:ss:"%0.2lf %S"
            >
            -->
         <tr>
            <td>
               <RRD::TIME::NOW %Y-%m>
            </td>
            <td align="right">
               <RRD::PRINT 0>
            </td>
            <td align="right">
               <RRD::PRINT 1>
            </td>
            <td align="right">
               <RRD::PRINT 2>
            </td>
         </tr>
         <!--
            <RRD::GRAPH -
            --start="<RRD::TIME::NOW %Y0101>"
            --end="now"
            DEF:in=../../rrd/eth0.rrd:in:AVERAGE:step=1800
            DEF:out=../../rrd/eth0.rrd:out:AVERAGE:step=1800
            VDEF:is=in,TOTAL
            PRINT:is:"%0.2lf %s"
            VDEF:os=out,TOTAL
            PRINT:os:"%0.2lf %S"
            CDEF:sum=in,out,+
            VDEF:ss=sum,TOTAL
            PRINT:ss:"%0.2lf %S"
            >
            -->
         <tr>
            <td>
               <RRD::TIME::NOW %Y>
            </td>
            <td align="right">
               <RRD::PRINT 0>
            </td>
            <td align="right">
               <RRD::PRINT 1>
            </td>
            <td align="right">
               <RRD::PRINT 2>
            </td>
         </tr>
      </table>
      <h2>Current</h2>
      <RRD::SETVAR start -2h>
      <RRD::SETVAR end now>
      <RRD::INCLUDE eth0.inc>
      <h2>Day</h2>
      <RRD::SETVAR start -24h>
      <RRD::SETVAR end now>
      <RRD::INCLUDE eth0.inc>
      <h2>7 Days</h2>
      <RRD::SETVAR start -7d>
      <RRD::SETVAR end now>
      <RRD::INCLUDE eth0.inc>
      <h2>Month</h2>
      <RRD::SETVAR start -30d>
      <RRD::SETVAR end now>
      <RRD::INCLUDE eth0.inc>
      <h2>This Year</h2>
      <RRD::SETVAR start "Jan1">
      <RRD::SETVAR end "Dec31">
      <RRD::INCLUDE eth0.inc>
      <h2>Last Year</h2>
      <RRD::SETVAR start "Jan1-365d">
      <RRD::SETVAR end "Dec31-365d">
      <RRD::INCLUDE eth0.inc>
   </body>
</html>

