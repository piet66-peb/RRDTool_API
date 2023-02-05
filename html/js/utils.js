
//h-------------------------------------------------------------------------------
//h
//h Name:         utils.js
//h Type:         Javascript module
//h Purpose:      Javascript utilities
//h Project:      RRDTool_API
//h Usage:
//h Remark:
//h Result:
//h Examples:
//h Outline:
//h Resources:
//h Platforms:    independent
//h Authors:      peb piet66
//h Version:      V1.0.1 2023-02-05/peb
//v History:      V1.0.0 2022-01-02/peb first version
//h Copyright:    (C) piet66 2022
//h License:      http://opensource.org/licenses/MIT
//h
//h-------------------------------------------------------------------------------

/*globals document, XMLHttpRequest, console */

//-----------
//b Constants
//-----------
var MODULE='utils.js';
var VERSION='V1.0.1';
var WRITTEN='2023-02-05/peb';

//-----------
//b Functions
//-----------
var utils = {
    rrd_name: null,
    autoupdate_timer: null,
    autoupdate_delay: null,

    get_rrd_params: function (rrd, format) {
        //
        // reads and displays next and step from rrd
        // stores next, step and rrd name
        //
        //console.log('get_rrd_params('+rrd+')');
        if (rrd) {
            utils.get_rrd_params_in = {rrd: rrd,
                                       format: format};
        }
        if (!rrd && !utils.get_rrd_params_in) {
            return;
        }
        rrd = utils.get_rrd_params_in.rrd;
        format = utils.get_rrd_params_in.format;
        var el = document.getElementById("interval");
        if (!el) {
            return;
        }
        var url = '/'+rrd+'/fetch?l=0h&times=no';
        var xhttp = new XMLHttpRequest();
        xhttp.onload = function(){
            if (xhttp.status === 200) {
                var data = JSON.parse(xhttp.responseText);
                var next = data[0][1];
                var step = data[0][2];
                utils.get_rrd_params_in.next = next;
                utils.get_rrd_params_in.step = step;
                if (format) {
                    var diff = new Date().getTimezoneOffset()*60;
                    var d = new Date((next-diff)*1000).toISOString().replace('T',' ').replace(/\..*$/, '');
                    var text = format.replace('%RRD', rrd)
                                     .replace('%STEP', step)
                                     .replace('%NEXT', d);
                    var el = document.getElementById("interval");
                    if (el) {
                        el.textContent = text;
                    }
                }
                utils.autoupdate();
            }
        };
        xhttp.open('GET', url);
        xhttp.send();
    },  //get_rrd_params

    update: function () {
        //
        // udpates all images
        // reads nd displays next and step from rrd  (>get_rrd_params())
        // checks for automatic update  (>autoupdate())
        //
        //console.log('update');
        function img_find() {
            var imgs = document.getElementsByTagName("img");
            var imags = [];
            for (var i = 0; i < imgs.length; i++) {
                imags.push(imgs[i]);
            }
            return imags;
        }

        //console.log(window.location);
        var query = window.location.search.substring(1);

        //build url for all images
        var images = img_find();
        if (images.length === 0) {
            console.log('no image found, break.');
            return;
        }
        var url = location.origin+'/build_graph?g=';
        images.forEach(function(img, ix) {
            image = img.src;
            var img_def = image.replace(/^.*\//, '').replace(/\.[^\.]*$/, '');
            if (ix === 0) {
                url += img_def;
            } else {
                url += ':'+img_def;
            }
        });
        query += '&html=-';
        if (query) {
            url += '&'+query;
        }
        //console.log(url);

        //rebuild graphs:
        var xhttp = new XMLHttpRequest();
        xhttp.onload = function(response) {
            if (xhttp.status === 200) {
                var timestamp = new Date().getTime();   
                var images = img_find();
                images.forEach(function(img, ix) {
                    var img_src_old = img.src;
                    var img_src_new =  img_src_old.replace(/\?timestamp=.*$/, '')
                                                  .replace(/&timestamp=.*$/, '');
                    if (img_src_new.indexOf('?') > 0) {
                        img_src_new += '&timestamp=' + timestamp;
                    } else {
                        img_src_new += '?timestamp=' + timestamp;
                    }
                    img.src = img_src_new;
                });
                utils.get_rrd_params();
            } else
            if (xhttp.status === 400) {
                console.log(response);
                alert(response.currentTarget.responseText.replace(/<br>/g, '\n')
                                                         .replace(/<[^<]*>/g, ''));
            }
        };
        xhttp.open('GET', url);
        xhttp.send();
    },  //update

    autoupdate: function (delay) {
        //
        // checks if auto update required
        // sets/ resets timer
        //
        //console.log('autoupdate('+delay+')');
        var el = document.getElementById("autoupdate");
        if (!el) {return;}
        if (!el.checked) {
            //console.log('unchecked');
            if (utils.autoupdate_timer) {
                clearTimeout(utils.autoupdate_timer);
                utils.autoupdate_timer = null;
            }
            return;
        }

        //console.log('checked');
        if (utils.autoupdate_timer) {return;}

        var clicked;
        if (delay) {
            utils.autoupdate_delay = delay;
            clicked = true;
        } else {
            delay = utils.autoupdate_delay;
        }
        if (!delay) {return;}

        var rrd = utils.get_rrd_params_in.rrd;
        if (!rrd) {return;}

        var next = utils.get_rrd_params_in.next;
        if (!next) {return;}

        var now = Math.floor(Date.now()/1000);
        var diff = next + delay - now;
        //console.log('now='+now+', next='+next+', diff='+diff);
        if (clicked) {
            //console.log('updating at once');
            utils.update();
            return;
        }
        if (diff > 0) {
            //console.log('waiting '+diff+' seconds');
            utils.autoupdate_timer = setTimeout(
                function() {
                    utils.autoupdate_timer = null;
                    //console.log('timeout');
                    utils.update();
                }, diff*1000);
        }
    },  //autoupdate
    
};
