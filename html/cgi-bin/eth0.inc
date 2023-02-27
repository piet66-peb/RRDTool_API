<p>
<RRD::GRAPH ../../graphs_img/eth0<RRD::GETVAR start>.png
    --title="eth0 network traffic"
    --vertical-label=Bytes/s
    --start="<RRD::GETVAR start>"
    --end="<RRD::GETVAR end>"
    --width=900
    --height=200
    --imginfo '<IMG SRC=/graphs_img/%s WIDTH=%lu HEIGHT=%lu >'

    DEF:in=../../rrd/eth0.rrd:in:AVERAGE
    CDEF:nin=in,-1,*
    LINE1.5:nin#00d000
    AREA:nin#90ff90:Incoming

    DEF:out=../../rrd/eth0.rrd:out:AVERAGE
    LINE1.5:out#2020ff
    AREA:out#9090ff:Outgoing
    LINE0.5:0#000

    COMMENT:"<RRD::TIME::NOW '%Y-%m-%d %H\:%M\:%S'>\j"
 >
 </p>
