#!/usr/bin/env python3
#pylint: disable=invalid-name
'''
#h-------------------------------------------------------------------------------
#h
#h Name:         RRDTool_API.py
#h Type:         python program
#h Purpose:      HTTP API for RRDTool
#h Project:
#h Usage:        Start API:
#h                  cd ...
#h                  source rest_api/bin/activate
#h                  export FLASK_APP=RRDTool_API
#h                  flask run --host=0.0.0.0        #for remote access, port=5001
#h               Call via URL:
#h                  http://nnn.nnn.nnn.nn:5001/...
#h               Display API interface:
#h                  http://nnn.nnn.nnn.nn:5001/
#h Result:
#h Examples:
#h Outline:
#h Resources:    python3, flask, RRDTool
#h Manuals:      https://palletsprojects.com/p/flask/
#h               https://www.python.org/
#h               https://www.w3schools.com/python/default.asp
#h               https://oss.oetiker.ch/rrdtool
#h               https://pythonhosted.org/rrdtool/index.html
#h Platforms:    Linux
#h Authors:      peb piet66
#h Version:      V1.3.0 2023-03-15/peb
#v History:      V1.0.0 2022-11-23/peb first version
#v               V1.2.0 2023-02-24/peb [+]cgi-bin
#v               V1.2.1 2023-03-03/peb [+]parameter 'back' for automatic generated
#v                                        graph
#v                                     [+]change texts for automatic generated graph
#v                                        in settings.py
#v               V1.3.0 2023-03-06/peb [+]function midnight()
#v                                     [+]function midnightUTC()
#v                                     [+]updatev
#v                                     [+]&title=<html title>
#h Copyright:    (C) piet66 2022
#h License:      http://opensource.org/licenses/MIT
#h
#h-------------------------------------------------------------------------------
'''

#pylint: disable=too-many-lines
#pylint: disable=inconsistent-return-statements, too-many-return-statements
#pylint: disable=too-many-branches, too-many-locals, too-many-statements

import os
import subprocess
import traceback
import platform
import glob
from datetime import datetime, timedelta
import re
from functools import wraps     #only for correct module documentation
import locale
import random
import urllib.parse
import time
import json
from ast import literal_eval as make_tuple
from markupsafe import escape
#pylint: disable=import-error
from flask import __version__
from flask import Flask, request, jsonify, redirect
from flask import make_response
from flask_cors import CORS
import rrdtool

import settings

os.environ.pop('TZ', None)
locale.setlocale(locale.LC_ALL, '')  # this will use the locale as set in the environment variables

MODULE = 'RRDTool_API.py'
VERSION = 'V1.3.0'
WRITTEN = '2023-03-15/peb'
PYTHON = platform.python_version()
PYTHON_RRDTOOL = rrdtool.__version__
RRDTOOL = rrdtool.lib_version()
FLASK_VERSION = __version__

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
#pylint: enable=invalid-name

#----------------------------------------------------------------------------

# constants

# http status codes
OK = 200
CREATED = 201
NO_CONTENT = 204
NOT_MODIFIED = 304
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
DB_ERROR = 900
REDIRECTED = 302
UNAUTHORIZED = 401
NOT_ALLOWED = 405
INTERNAL_ERROR = 500

# hello
app.logger.setLevel(20)
app.logger.info('------------ '+MODULE+' '+VERSION+' '+WRITTEN+' '+
                FLASK_VERSION+' '+
                PYTHON_RRDTOOL+' '+RRDTOOL+' started')
STARTED = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#----- get and process settings --------------------------------------------

def read_setting(setting_name, default_setting=None, is_path=False):
    '''read setting from settings.py'''
    if not hasattr(settings, setting_name):
        return default_setting
    if not is_path:
        return getattr(settings, setting_name)
    value = str(getattr(settings, setting_name))
    if value[-1] == '/' or  value[-1] == '\\':
        return value
    return value+'/'

LOGLEVEL = read_setting('LOGLEVEL', 20)
app.logger.setLevel(LOGLEVEL)

GRAPHS_IMG = read_setting('GRAPHS_IMG', './graphs_img/', True)
GRAPHS_DEF = read_setting('GRAPHS_DEF', './graphs_def/', True)
HTML_PATH = read_setting('HTML_PATH', './html/', True)
RRD_PATH = read_setting('RRD_PATH', './rrd/', True)
DEFAULTS_PATH = read_setting('DEFAULTS_PATH', './defaults/', True)
TMP_PATH = read_setting('TMP_PATH', './tmp/', True)
CGI_PATH = read_setting('CGI_PATH', './html/cgi-bin/', True)
RUN_CGI = read_setting('RUN_CGI', CGI_PATH+'run_cgi.bash')
CREATE_BASH = read_setting('CREATE_BASH', 'no')
UTC_FOR_GRAPHS = read_setting('UTC_FOR_GRAPHS', 'no')

WIDTH = str(read_setting('WIDTH', 1200))
HEIGHT = str(read_setting('HEIGHT', 200))

UPDATE_TEXT = str(read_setting('UPDATE_TEXT', 'Update'))
BACK_TEXT = str(read_setting('BACK_TEXT', 'Back'))
GRAPHS_TITLE = str(read_setting('GRAPHS_TITLE', 'RRDTool Graphs'))

ENABLE_MD_BLOCK = read_setting('ENABLE_MD_BLOCK', False)

DISABLE_AUTHENTICATION = read_setting('DISABLE_AUTHENTICATION', False)
ALLOW_WRITE_WITH_GET = read_setting('ALLOW_WRITE_WITH_GET', False)
WHITELIST_GET = read_setting('WHITELIST_GET', [])
WHITELIST_POST = read_setting('WHITELIST_POST', [])
CORS_HOST = read_setting('CORS_HOST')

USERNAME = read_setting('USERNAME')
if USERNAME is None:
    raise RuntimeError('no USERNAME defined in settings.py!')
PASSWORD = read_setting('PASSWORD')
if PASSWORD is None:
    raise RuntimeError('no PASSWORD defined in settings.py!')

if CORS_HOST is None:
    app.logger.warning('no CORS_HOST defined in settings.py!')
if DISABLE_AUTHENTICATION:
    app.logger.warning('authentication for write access is disabled for everybody')
if ALLOW_WRITE_WITH_GET:
    app.logger.warning('write acces via GET method is enabled for everybody')

# allow CORS for GET access for all hosts:
CORS(app, methods={"GET": {"origins": "*"}})

# set CORS for POST access:
if not CORS_HOST is None:
    # allow POST access for ZWay MxChartDB Admin clients:
    CORS(app, origins=CORS_HOST)
    app.logger.info('POST method is enabled for: '+''.join(CORS_HOST))

#----- authetication functions ----------------------------------------------

# filter whitelists
@app.before_request
def before_request():
    '''decorator: check whitelist before every request'''
    app.logger.info('')
    app.logger.info('==================== @app.before_request')
    app.logger.info(request)
    app.logger.info('requesting host: '+''.join(request.remote_addr))
    app.logger.info('requesting method: '+request.method)
    app.logger.info('requested host: '+request.host)
    app.logger.info('requested path: '+request.path)
    app.logger.info('requested query_string: '+str(request.query_string))
    #app.logger.info('requested query_string (utf-6): '+str(request.query_string, "utf-8"))
    #app.logger.info('requested query_string_unquote: '+
    #   urllib.parse.unquote(str(request.query_string, "utf-8")))
    #app.logger.info('requested query_string_unquote_plus: '+
    #   urllib.parse.unquote_plus(str(request.query_string, "utf-8")))

    host = ''.join(request.remote_addr)
    if request.method == 'GET':
        if not wild_search(WHITELIST_GET, host):
            return response_text_err('GET not allowed for '+host), FORBIDDEN
    if request.method == 'POST':
        if not wild_search(WHITELIST_POST, host):
            return response_text_err('POST not allowed for '+host), FORBIDDEN
    if request.path != escape(request.path):
        return response_text_err('invalid character'), BAD_REQUEST

def wild_search(list_in, string_in):
    '''auxiliary function: search with wildcards'''
    app.logger.info('wild_search: '+string_in)
    try:
        in_list = list_in.index(string_in)
        if in_list >= 0:
            app.logger.info(string_in+' found')
            return True
#pylint: disable=bare-except
    except:
        for string_i in list_in:
            pattern = string_i.replace(".", r"\.").replace("*", ".*")
            app.logger.info('check '+pattern+' for '+string_in)
            regex = re.compile("^"+pattern+"$")
            if bool(regex.match(string_in)):
                return True
    return False

# Basic Authentication
def auth_required(func):
    '''decorator to check authentication'''
    app.logger.info('*** auth_required')
    @wraps(func)
    def decorator(*args, **kwargs):
        #skip authorization for /SQL/ GET selects
        if request.endpoint == 'route_sql_get':
            app.logger.info('checking for SELECT...')
            sql = request.args.get('command')
            if sql is None:
                return func(*args, **kwargs)
            app.logger.info(sql)
            pos = sql.upper().lstrip().find('SELECT ')
            if pos == 0:
                app.logger.info('SELECT: skipping authorization')
                return func(*args, **kwargs)

        if DISABLE_AUTHENTICATION:
            app.logger.info('authorization switched off')
            return func(*args, **kwargs)
        if request.method == 'GET' and not ALLOW_WRITE_WITH_GET:
            error_text = 'method GET not allowed for this command per default, '
            error_text += 'for change set ALLOW_WRITE_WITH_GET = True'
            response = response_text_err(error_text)
            header = response.headers
            header['Access-Control-Allow-Methods'] = 'POST'
            return response, NOT_ALLOWED
        auth = request.authorization
        #auth = {'username': 'username', 'password': 'secret'}
        error_text = None
        if auth is None:
            if request.method == 'GET':
                error_text = "requesting authentication..."
            else:
                error_text = "Authentication missing"
        elif 'username' not in auth:
            error_text = "Authentication: username missing"
        elif auth.username is None:
            error_text = "Authentication: username missing"
        elif 'password' not in auth:
            error_text = "Authentication: password missing"
        elif auth.password is None:
            error_text = "Authentication: password missing"
        elif auth.username != USERNAME:
            error_text = "Authentication: username/password wrong"
        elif auth.password != PASSWORD:
            error_text = "Authentication: username/password wrong"
        if error_text is not None:
            response = response_text_err(error_text)
            header = response.headers
            header['WWW-Authenticate'] = 'Basic realm="RRDTool_API.py", charset="UTF-8"'
            return response, UNAUTHORIZED
        app.logger.info('user authenticated')
        return func(*args, **kwargs)
    return decorator

#----- auxiliary functions --------------------------------------------------

def change_loglevel(new_loglevel):
    '''dynamically change the loglevel'''
    if new_loglevel is None:
        return
    if new_loglevel not in ('10', '20', '30', '40', '50'):
        return
    new_loglevel = int(new_loglevel)
#pylint: disable=global-statement
    global LOGLEVEL
    if new_loglevel != LOGLEVEL:
        LOGLEVEL = new_loglevel
        app.logger.setLevel(LOGLEVEL)
        app.logger.warn('new loglevel='+str(LOGLEVEL))

def request_correct_arg(arg, arg2, default=None):
    '''request.args.get manually'''
    querystring = urllib.parse.unquote(str(request.query_string, "utf-8"))
    app.logger.info('querystring='+querystring)
    querystring2 = urllib.parse.unquote_plus(str(request.query_string, "utf-8"))
    app.logger.info('querystring2='+querystring2)

    if arg2 and arg+'=' not in querystring:
        arg = arg2
    if arg+'=' not in querystring:
        return request.args.get(arg, default)

    if querystring2 == querystring:
        return request.args.get(arg, default)

    querysplit = querystring.split('&')
    for arg_i in querysplit:
        if arg_i.find(arg+'=') == 0:
            return arg_i[len(arg+'='):]
    return request.args.get(arg, default)

def convert_length(length):
    '''converts +/- into -/+'''
    if length is None:
        return length
    if '-' not in length and '+' not in length:
        return length
    length = re.sub(r'^\s*\+\s*', '', length)
    length = re.sub(r'\+', '§', length)
    length = re.sub(r'-', '+', length)
    length = re.sub(r'§', '-', length)
    return length

def request_times_args(set_defaults=True):
    '''request.args.get of time arguments, correct and set defaults'''
    start = request_correct_arg('s', 'start')
    end = request_correct_arg('e', 'end')
    length = request_correct_arg('l', 'length')
    length = convert_length(length)
    if set_defaults:
        if not end:
            end = 'now'
        if not length:
            length = '1d'
        if not start:
            start = 'end-'+length

    if start:
        app.logger.info('start: '+start)
    if end:
        app.logger.info('end: '+end)
    if length:
        app.logger.info('length: '+length)
    return start, end, length

#pylint: disable=invalid-name
def midnight(start, end):
    '''computes midnight localtime midnight'''
    ret = (start, end)
    for timetype_i in (start, end):
        if 'midnight' in timetype_i:
            for match in re.findall(r"midnight\s*\([^)]*\)", timetype_i):
                params_string = re.sub(r"^.*\(\s*", "", match)
                params_string = re.sub(r"\s*\)", "", params_string)
                params_split = re.split(r"\s*,\s*", params_string)
                if len(params_split) < 2:
                    return ret

                if params_split[1] == 'now':
                    params_split[1] = int(time.time())
                else:
                    if not params_split[1].isdigit():
                        return ret
                    params_split[1] = int(params_split[1])
                    if params_split[1] < 1000000000 or params_split[1] > 9999999999:
                        return ret

                #set date object for new local time:
                date_in = datetime.fromtimestamp(params_split[1])
                if params_split[0] == 'D':
                    date_new = date_in.replace(
                        hour=0, minute=0, second=0, microsecond=0)
                elif params_split[0] == 'M':
                    date_new = date_in.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0)
                elif params_split[0] == 'Y':
                    date_new = date_in.replace(
                        month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                elif params_split[0] == 'W':
                    curr_weekday = date_in.isoweekday()
                    if curr_weekday == 1:   #Monday
                        date_new = date_in.replace(
                            hour=0, minute=0, second=0, microsecond=0)
                    else:
                        date_new1 = date_in - timedelta(curr_weekday - 1)
                        date_new = date_new1.replace(
                            hour=0, minute=0, second=0, microsecond=0)
                else:
                    return ret
                #convert to timestamp:
                ts_new = str(int(date_new.timestamp()))
                #replace match in input:
                if match in start:
                    start = start.replace(match, ts_new)
                if match in end:
                    end = end.replace(match, ts_new)
                ret = (start, end)
    app.logger.info(ret)
    return ret
###midnight

#pylint: disable=invalid-name
def midnightUTC(start, end):
    '''computes midnight utc midnightUTC'''
    ret = (start, end)
    for timetype_i in (start, end):
        if 'midnightUTC' in timetype_i:
            for match in re.findall(r"midnightUTC\s*\([^)]*\)", timetype_i):
                params_string = re.sub(r"^.*\(\s*", "", match)
                params_string = re.sub(r"\s*\)", "", params_string)
                params_split = re.split(r"\s*,\s*", params_string)
                if len(params_split) < 2:
                    return ret

                if params_split[1] == 'now':
                    params_split[1] = int(time.time())
                else:
                    if not params_split[1].isdigit():
                        return ret
                    params_split[1] = int(params_split[1])
                    if params_split[1] < 1000000000 or params_split[1] > 9999999999:
                        return ret

                #set date object for new local time:
                date_in = datetime.fromtimestamp(params_split[1])
                if params_split[0] == 'D':
                    date_new = date_in.replace(
                        hour=0, minute=0, second=0, microsecond=0)
                elif params_split[0] == 'M':
                    date_new = date_in.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0)
                elif params_split[0] == 'Y':
                    date_new = date_in.replace(
                        month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                elif params_split[0] == 'W':
                    curr_weekday = date_in.isoweekday()
                    if curr_weekday == 4:   #Thursday
                        date_new = date_in.replace(
                            hour=0, minute=0, second=0, microsecond=0)
                    if curr_weekday < 4:
                        date_new1 = date_in - timedelta(7 + curr_weekday - 1)
                        date_new = date_new1.replace(
                            hour=0, minute=0, second=0, microsecond=0)
                    else:
                        date_new1 = date_in - timedelta(curr_weekday - 1)
                        date_new = date_new1.replace(
                            hour=0, minute=0, second=0, microsecond=0)
                else:
                    return ret
                #convert to local timestamp:
                ts_loc = int(date_new.timestamp())
                #convert to utc timestamp:
                ts_utc = (ts_loc // 86400 + 1) * 86400
                ts_new = str(ts_utc)
                #replace match in input:
                if match in start:
                    start = start.replace(match, ts_new)
                if match in end:
                    end = end.replace(match, ts_new)
                ret = (start, end)
    app.logger.info(ret)
    return ret
###midnightUTC

def replace_times_first_last(start, end, rrd_file_list):
    '''replaces first and last in time argument by the timstamp'''
    first = 'first'
    last = 'last'
    combi = start + ' ' +end
    ret = (start, end)
    if first not in combi and last not in combi:
        if 'midnight' in combi:
            ret = midnight(ret[0], ret[1])
        if 'midnightUTC' in combi:
            ret = midnightUTC(ret[0], ret[1])
        return ret

    app.logger.info(ret)
    if first in combi:
        first_min = 999999999999
        for rrd_file in rrd_file_list:
            first_min = min(first_min, rrdtool.first(RRD_PATH+rrd_file))
        if first in end:
            end = end.replace(first, str(first_min))
        if first in start:
            start = start.replace(first, str(first_min))
    if last in combi:
        last_max = 0
        for rrd_file in rrd_file_list:
            last_max = max(last_max, rrdtool.last(RRD_PATH+rrd_file))
        if last in end:
            end = end.replace('last', str(last_max))
        if last in start:
            start = start.replace('last', str(last_max))
    ret = (start, end)
    app.logger.info(ret)
    if 'midnight' in combi:
        ret = midnight(ret[0], ret[1])
    if 'midnightUTC' in combi:
        ret = midnightUTC(ret[0], ret[1])
    return ret
###replace_times_first_last

def convert_min_mon(inp):
    '''trplaces m with minute and M with Month'''
    app.logger.info(inp)
    inp = re.sub(r'\b(M)\b', "Month", inp)
    inp = re.sub(r'(\d)(M)\b', r"\1\2onth", inp)
    inp = re.sub(r'\b(m)\b', "minute", inp)
    inp = re.sub(r'(\d)(m)\b', r"\1\2inute", inp)
    app.logger.info(inp)
    return inp

def convert_date_format(start, end):
    '''replaces YYYY-MM-YY with MM/DD/YYYY,
       m with minute and M with Month'''

    start = convert_min_mon(start)
    end = convert_min_mon(end)

#pylint: disable=anomalous-backslash-in-string
    pattern = '\d{4}-\d{2}-\d{2}'
    dates = re.findall(pattern, start)
    if dates:
        for dt_i in dates:
            dt_is = dt_i.split('-')
            dt_j = dt_is[1]+'/'+dt_is[2]+'/'+dt_is[0]
            print(dt_j)
            start = start.replace(dt_i, dt_j)

    dates = re.findall(pattern, end)
    if dates:
        for dt_i in dates:
            dt_is = dt_i.split('-')
            dt_j = dt_is[1]+'/'+dt_is[2]+'/'+dt_is[0]
            print(dt_j)
            end = end.replace(dt_i, dt_j)
    ret = (start, end)
    return ret

def buildusertime(epochtime):
    '''converts epoch time to user readable time string'''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epochtime))

def build_except_err_string(error, graph):
    '''auxiliary function: build error text at exeption'''
    ret = ''
    ret += 'Request: '+request.path
    if request.query_string:
        ret += '?'+urllib.parse.unquote(str(request.query_string, "utf-8"))
    errortype = str(type(error)).split("'")[1]
    ret += '<br>'+errortype
    if graph:
        ret += '<br>at graph '+graph+':'

    ret += '<br>'+str(error)
    #for line in error.args:
    #    app.logger.info(type(line))
    #    if isinstance(line, str):
    #        ret += '<br>'+line[0:30]

    if 'rpn' in ret:
        ret += '<br>(rpn = formula in reverse polish notation)'

    ret += '<br>'
    tback = traceback.format_exc().split('\n')
    tback1 = tback[len(tback)-4]
    tback2 = tback[len(tback)-3]
    line_start = tback1.find("line ")
    line_end = tback1.find(",", line_start)
    subtext = tback1[line_start:line_end]
    ret += '<br>'+subtext+': '+tback2

    return ret

# build error text response
def response_text_err(text):
    '''auxiliary function: build error text as formatted html'''
    #response = make_response('<font color=red size=+2>'+text+'</font>')
    response = make_response('<br><font color=red>'+text+'</font>')
    response.mimetype = 'text/html'
    app.logger.error(text)
    return response

def response_text(text, mimetype):
    '''auxiliary function: log info text + set mimetype'''
    if mimetype == '':
        app.logger.info(text)
        return jsonify(text)
    if mimetype == 'application/json':
        return jsonify(text)
    #app.logger.info(text, mimetype)
    response = make_response(text, 200)
    response.mimetype = mimetype
    return response

# get database list
def get_database_list(remove_extension):
    '''auxiliary function: get database list'''
    files = glob.glob(RRD_PATH+'*.rrd')
    dbs = []
    for file_i in files:
        if remove_extension:
            dbs.append(os.path.splitext(file_i)[0])
        else:
            dbs.append(file_i)
    dbs.sort()
    return dbs

# get graph list
def get_graph_list(remove_extension):
    '''auxiliary function: get graph list'''
    files = glob.glob(GRAPHS_IMG+'*.*')
    graphs = []
    for file_i in files:
        if remove_extension:
            graphs.append(os.path.splitext(os.path.basename(file_i))[0])
        else:
            graphs.append(os.path.basename(file_i))
    graphs.sort()
    return graphs

# get graph definition list
def get_graph_def_list(remove_extension=True):
    '''auxiliary function: get graph definition list'''
    files = glob.glob(GRAPHS_DEF+'*.def')
    graphs = []
    for file_i in files:
        basename = os.path.basename(file_i)
        if remove_extension:
            graphs.append(os.path.splitext(basename)[0])
        else:
            graphs.append(basename)
    graphs.sort()
    return graphs

# get openmode and mimetype
def get_mimetype_by_suffix(path):
    '''auxiliary function: returnes openmode + mimetype for suffix'''

    file_extension = os.path.splitext(path)[1]
    #[-a PNG|SVG|EPS|PDF|XML|XMLENUM|JSON|JSONTIME|CSV|TSV|SSV]
    #The <img> tag may support (depending on the browser) the following
    #image formats: jpeg, gif, png, apng, svg, bmp, bmp ico

    mimetypes = {'.def': ('r', 'text/plain'),
                 '.html': ('r', 'text/html'),
                 '.htm': ('r', 'text/html'),
                 '.xml': ('r', 'text/xml'),
                 '.xmlenum': ('r', 'text/xml'),
                 '.png': ('rb', 'image/png'),
                 '.gif': ('rb', 'image/gif'),
                 '.jpeg': ('rb', 'image/jpeg'),
                 '.jpg': ('rb', 'image/jpeg'),
                 '.svg': ('r', 'image/svg+xml'),
                 '.webp': ('rb', 'image/webp'),
                 '.avif': ('rb', 'image/avif'),
                 '.apng': ('rb', 'image/apng'),
                 '.eps': ('r', 'application/postscript'),
                 '.csv': ('r', 'text/csv'),
                 '.json': ('r', 'application/json'),
                 '.jsontime': ('r', 'application/json'),
                 '.pdf': ('rb', 'application/pdf'),
                 '.ssv': ('r', 'text/plain'),
                 #'.tsv': ('r', 'text/plain'),
                 '.tsv': ('r', 'text/tab-separated-values'),
                 '.bmp': ('rb', 'image/bmp'),
                 '.ico': ('rb', 'image/x-icon'),
                 #'.md': ('r', 'text/markdown'),    !!!
                 '.md': ('r', 'text/plain'),
                 '.js': ('r', 'text/javascript'),
                 '.css': ('r', 'text/css')
                 }

    if file_extension in mimetypes:
        app.logger.info(mimetypes[file_extension])
        return mimetypes[file_extension]
    return ('', '')

# read file contents
def read_file(path):
    '''auxiliary function: read file contents'''
    if not os.path.isfile(path):
        return path+' not found', NOT_FOUND

    openmode, mimetype = get_mimetype_by_suffix(path)
    if openmode == '':
        return "filetype for "+path+' not supported by API', BAD_REQUEST

    app.logger.info(path+', openmode='+openmode+', mimetype='+mimetype)
    fil_object = open(path, openmode)
    contents = fil_object.read()
    fil_object.close()
    return contents, OK, mimetype

#----- API survey -----------------------------------------------------------

@app.route('/')
def route_api_commands():
    '''route: show api commands in a html page'''
    try:
        ret = read_file('index.html')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/README')
def route_api_readme_html():
    '''route: show README.html'''
    try:
        if not ENABLE_MD_BLOCK:
            return redirect('/README.md', code=REDIRECTED)

        ret = read_file('README.html')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/README.md')
def route_api_readme_md():
    '''route: show README.md'''
    try:
        app.logger.info('route_api_readme_md')
        ret = read_file('README.md')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/TIME_FORMATS')
def route_api_times_html():
    '''route: show TIMES.html'''
    try:
        if not ENABLE_MD_BLOCK:
            return redirect('/TIME_FORMATS.md', code=REDIRECTED)

        ret = read_file('TIME_FORMATS.html')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/TIME_FORMATS.md')
def route_api_times_md():
    '''route: show TIMES.md'''
    try:
        app.logger.info('route_api_times_md')
        ret = read_file('TIME_FORMATS.md')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/icon.png')
def route_api_icon_png():
    '''route: show icon.png'''
    try:
        app.logger.info('route_api_icon_png')
        ret = read_file('icon.png')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''


#----- API ------------------------------------------------------------------

@app.route('/version', methods=["GET"])
def route_api_version():
    '''route: response version information'''
    change_loglevel(request.args.get('loglevel'))
    try:
        info = {"MODULE": MODULE,
                "VERSION": VERSION,
                "WRITTEN": WRITTEN,
                "PYTHON": PYTHON,
                "FLASK": FLASK_VERSION,
                "RRDTOOL": RRDTOOL,
                "PYTHON_RRDTOOL": PYTHON_RRDTOOL,
                "STARTED": STARTED,
                "LOGLEVEL": LOGLEVEL
                }
        return response_text(info, '')
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/list_databases', methods=["GET"])
def route_api_list_databases():
    '''route: response database list'''
    try:
        dbs = get_database_list(False)
        if dbs == []:
            return response_text_err('no databases found'), NOT_FOUND
        return response_text(dbs, '')
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/<dbase>/update', methods=["POST", "GET"], endpoint='route_api_update')
@app.route('/<dbase>/updatev', methods=["POST", "GET"], endpoint='route_api_update')
@auth_required
def route_api_update(dbase):
    '''route: update database'''
    try:
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        ts_new = request.args.get('ts', 'N')
        values_new = request.args.get('values')
        if not values_new:
            return response_text_err('database '+dbase+' no values specified'), NOT_FOUND

        if '/updatev' in request.path:
            info = rrdtool.updatev(RRD_PATH+dbase+'.rrd', ts_new+':'+values_new)
            return response_text(info, ''), OK

        rrdtool.update(RRD_PATH+dbase+'.rrd', ts_new+':'+values_new)
        return response_text('database '+dbase+' updated', ''), OK
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/<dbase>/info', methods=["GET"], endpoint='route_api_info')
def route_api_info(dbase):
    '''route: info database'''
    try:
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        info = rrdtool.info(RRD_PATH+dbase+'.rrd')
        return response_text(info, ''), OK
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/<dbase>/first', methods=["GET"], endpoint='route_api_first')
def route_api_first(dbase):
    '''route: first database'''
    try:
        rraindex = request_correct_arg('rra', 'index', '0')
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        params = (RRD_PATH+dbase+'.rrd', '--rraindex', rraindex)
        first = rrdtool.first(*params)
        ret = {"usertime": buildusertime(first),
               "ts": first
               }
        return response_text(ret, ''), OK
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/<dbase>/last', methods=["GET"], endpoint='route_api_lastupdate')
@app.route('/<dbase>/lastupdate', methods=["GET"], endpoint='route_api_lastupdate')
def route_api_lastupdate(dbase):
    '''route: lastupdate database'''
    try:
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        lastupdate = rrdtool.lastupdate(RRD_PATH+dbase+'.rrd')
        last = rrdtool.last(RRD_PATH+dbase+'.rrd')
        ret = {"usertime": buildusertime(last),
               "ts": last,
               "date": lastupdate["date"],
               "ds": lastupdate["ds"]
               }
        return response_text(ret, ''), OK
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/<dbase>/fetch', methods=["GET"], endpoint='route_api_fetch')
def route_api_fetch(dbase):
    '''route: fetch database'''
    params = None
    try:
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        cif = request.args.get('cf', 'LAST')
#pylint: disable=unused-variable
        start, end, length = request_times_args()

        start, end = replace_times_first_last(start, end, [dbase+'.rrd'])
        start, end = convert_date_format(start, end)

        resolution = request.args.get('r')
        times = request.args.get('times', 'yes')

        params = (RRD_PATH+dbase+'.rrd', cif, '-s', start, '-e', end, '-a')
        if resolution:
            params += ('--resolution', resolution)
        app.logger.info(params)
        fetch = rrdtool.fetch(*params)
        #start, end, step = fetch[0]
        #ds = fetch[1]
        #rows = fetch[2]

        if times in ('yes', 'y'):
            fetch = json.loads(json.dumps(fetch))
            fstart = fetch[0][0]
            fend = fetch[0][1]
            fstep = fetch[0][2]
            fetch[0].insert(1, buildusertime(fend))
            fetch[0].insert(0, buildusertime(fstart))

            fetch[1].insert(0, "ts")
            fetch[1].insert(0, "usertime")

            frows = fetch[2]
            for i in range(0, len(frows), 1):
                timestamp = fstart + (i+1) * fstep
                usertime = buildusertime(timestamp)
                fetch[2][i].insert(0, timestamp)
                fetch[2][i].insert(0, usertime)

        return response_text(fetch, ''), OK
#pylint: disable=broad-except
    except Exception as error:
        if params:
            app.logger.error('params='+str(params))
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''
###route_api_fetch

@app.route('/<dbase>/dump', methods=["GET"], endpoint='route_api_dump')
def route_api_dump(dbase):
    '''route: dump database'''
    try:
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        rrdtool.dump(RRD_PATH+dbase+'.rrd', dbase+'.xml')
        ret = read_file(dbase+'.xml')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        os.remove(dbase+'.xml')
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

#----- Graphs ---------------------------------------------------------------

@app.route('/list_graphs', methods=["GET"])
def route_api_list_graphs():
    '''route: response graph list'''
    try:
        graphs = get_graph_list(False)
        if graphs == []:
            return response_text_err('no graph image found'), NOT_FOUND
        return response_text(graphs, '')
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/list_graph_definitions', methods=["GET"])
def list_graph_definitions():
    '''route: response graph definition list'''
    try:
        graphs = get_graph_def_list(False)
        if graphs == []:
            return response_text_err('no graph definition found'), NOT_FOUND
        return response_text(graphs, '')
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

def get_graph_definition_list():
    '''returns list of graph definitions'''
    graph_list = get_graph_def_list()
    recgraphs = request.args.get('g')
    app.logger.info('recgraphs='+str(recgraphs))
    if not recgraphs or recgraphs == '*':
        return graph_list

    recgraphs_list = recgraphs.split(':')
    graph_list_build = []
    for recgraphs_i in recgraphs_list:
        app.logger.info('recgraphs_i='+recgraphs_i)
        if recgraphs_i == '*':
            return graph_list
        if recgraphs_i in graph_list:
            graph_list_build.append(recgraphs_i)
            continue
        if not '*' in recgraphs_i:
            continue
        recs_regex = "^"+recgraphs_i.replace("*", ".*").replace("$", r"\$")+"$"
        for graph_i in graph_list:
            if re.search(recs_regex, graph_i):
                graph_list_build.append(graph_i)
    graph_list_build = list(dict.fromkeys(graph_list_build))
    app.logger.info(graph_list_build)
    return graph_list_build

@app.route('/print_graph_definition', methods=["GET"])
def print_graph_definition():
    '''route: response graph definition(s)'''
    try:
        graph_list_build = get_graph_definition_list()
        if graph_list_build == []:
            recgraphs = request.args.get('g')
            if recgraphs:
                return response_text_err('no graph definition file found for '+recgraphs), NOT_FOUND
            return response_text_err('no graph definition file found'), NOT_FOUND

        graph_def_array = []
        for graph in graph_list_build:
            ret = read_file(GRAPHS_DEF+graph+'.def')
            if ret[1] != OK:
                return response_text_err(ret[0]), ret[1]
            graph_def = make_tuple(ret[0])
            graph_def_array.append({graph+'.def': list(graph_def)})

        return response_text(graph_def_array, ''), OK
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, graph)
        return response_text_err(ret), BAD_REQUEST, ''
###print_graph_definition

def random_color():
    '''returns a random color'''
    r_rgb = format(random.randint(0, 255), '02x')
    g_rgb = format(random.randint(0, 255), '02x')
    b_rgb = format(random.randint(0, 255), '02x')
    return '#'+r_rgb+g_rgb+b_rgb

@app.route('/new_graph_definition', methods=["GET"])
def new_graph_definition():
    '''route: create a new graph definition from default'''
    try:
        graph = None
        dbase = request.args.get('db')
        if not dbase:
            return response_text_err('db missing'), BAD_REQUEST
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        #read default file:
        ret = read_file(DEFAULTS_PATH+'default.def')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        default_def = make_tuple(ret[0])

        #get list of ds sources from rrd:
        info_dict = rrdtool.info(RRD_PATH+dbase+'.rrd')
        rrd_step = str(info_dict['step'])
        app.logger.warn('rrd_step='+rrd_step)
        ds_sources = {}
        for key in info_dict:
            if 'ds[' in key:
                ds_name = key.split(']', 1)[0].split('[', 1)[1]
                if ds_name and ds_name not in ds_sources:
                    index = info_dict['ds['+ds_name+'].index']
                    ds_sources[ds_name] = {
                        'index': index,
                        'type' : info_dict['ds['+ds_name+'].type'],
                        'cf': info_dict['rra[0].cf'],
                        'min': info_dict['ds['+ds_name+'].min'],
                        'max': info_dict['ds['+ds_name+'].max']}
            elif len(ds_sources) > 0:
                break
        if len(ds_sources) == 0:
            return response_text_err('no ds source found in database '+dbase), NOT_FOUND
        app.logger.warn(ds_sources)

        ds_source = request.args.get('ds')
        if ds_source:
            if ds_source not in ds_sources:
                return response_text_err(
                    'ds source '+ds_source+' not found in database '+dbase), NOT_FOUND

        #enum all ds sources
        files_created = []
        for ds_i in ds_sources:
            if ds_source and ds_i != ds_source:
                continue
            color = random_color()
            graph = dbase+'-'+ds_i
            index = ds_sources[ds_i]['index']
            ds_type = ds_sources[ds_i]['type']
            cf_value = ds_sources[ds_i]['cf']
            min_value = ds_sources[ds_i]['min']
            max_value = ds_sources[ds_i]['max']

            cf_set = None
            if ds_type in ('DERIVE', 'DDERIVE', 'COUNTER', 'DCOUNTER'):
                cf_set = 'AVERAGE'

            file_def_new = '('

            #add comments to output buffer;
            file_def_new += '\n####'
            file_def_new += '\n#### generated graph definition'
            file_def_new += '\n#### '+graph+'.def'
            file_def_new += '\n####'
            file_def_new += '\n#### database = '+dbase
            file_def_new += '\n#### data source = '+ds_i
            file_def_new += '\n#### index = '+str(index)
            file_def_new += '\n#### type = '+ds_type
            file_def_new += '\n#### rra[0].cf = '+cf_value
            if cf_set:
                file_def_new += '\n#### set to '+cf_set+' for DERIVE, DDERIVE, COUNTER, DCOUNTER'
            file_def_new += '\n#### rrd_step = '+rrd_step
            file_def_new += '\n#### min = '+str(min_value)
            file_def_new += '\n#### max = '+str(max_value)
            file_def_new += '\n#### random color = '+color
            file_def_new += '\n####'

            for line in default_def:
                line = line.replace('%DS_SOURCE', ds_i)
                line = line.replace('%DB_NAME', dbase)
                line = line.replace('%COLOR', color)
                line = line.replace('%TYPE', ds_type)
                if cf_set:
                    line = line.replace('%CF', cf_set)
                else:
                    line = line.replace('%CF', cf_value)

                if '%SECONDS' in line:
                    if ds_type in ('DERIVE', 'DDERIVE', 'COUNTER', 'DCOUNTER'):
                        file_def_new += '\n\n# summing up for DERIVE, DDERIVE, COUNTER, DCOUNTER:'
                        file_def_new += '\n# sum = average * interval'
                        line = line.replace('%SECONDS', 'STEPWIDTH')
                    else:
                        line = line.replace('%SECONDS', '1')
                file_def_new += "\n'"+line+"',"

            if min_value is not None:
                min_str = "\n'-l', '"+str(min_value)+"',  # lower limit"
                file_def_new += "\n"+min_str
            if max_value is not None:
                max_str = "\n'-u', '"+str(max_value)+"',  # upper limit"
                file_def_new += "\n"+max_str

            file_def_new += '\n)'
            fil = open(GRAPHS_DEF+graph+'.def', "w")
            fil.write(file_def_new)
            fil.close()

            files_created.append(graph+'.def')
        return response_text({'graph definitions created': files_created}, ''), OK

#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, graph)
        return response_text_err(ret), BAD_REQUEST, ''
###new_graph_definition

# build images webpage
def build_all_images_html(graph_list):
    '''auxiliary function: builds a html page with all images'''
    BACK_PATH = request.args.get('back', '/html/')
    HEADING = request.args.get('heading', '')
    html = '''
<!DOCTYPE html>
<html>
<head>
   <link rel="shortcut icon" href="icon.png" />
   <title>'''+GRAPHS_TITLE+'''</title>
   <style> img{
      white-space:pre;
      max-width: 95%;
      button {font-size: 16px;}
   </style></head>
<body>
   <h2>'''+HEADING+'''</h2>
   <table>
      <tr>
         <td> <a href="'''+BACK_PATH+'''">
            <p style="color:blue;"><u>'''+BACK_TEXT+'''</u></p> </a> </td>
         <td> <a  id ="update" href=""> 
            <p style="color:blue;"><u>'''+UPDATE_TEXT+'''</u></p> </a> </td>
      </tr>
   </table>
   <script>
       document.getElementById("update").setAttribute("href", window.location);
   </script>
'''

    for recgraphs_i in graph_list:
        files = glob.glob(GRAPHS_IMG+recgraphs_i+'.*')
        files.sort()
        for file_i in files:
            mimetype = get_mimetype_by_suffix(file_i)[1]
            if mimetype == ():
                app.logger.info("mimetype for "+file_i+' not detected')
                continue
            if 'image' in mimetype:
                full_file_i = GRAPHS_IMG+os.path.basename(file_i)
                html += '   <img src="'+full_file_i+'" alt="'+full_file_i+'">\n'
            else:
                html += '   <a href="'+file_i+'">'+file_i+'</a>\n'
            html += '   <br><br>\n'
    html += '</body>\n</html>'
    return html

@app.route('/display_graph', methods=["GET"], endpoint='route_api_display_graph')
def route_api_display_graph():
    '''route: call graphs html'''
    try:
        graph_list_build = get_graph_definition_list()
        if graph_list_build == []:
            recgraphs = request.args.get('g')
            if recgraphs:
                return response_text_err('no graph definition file found for '+recgraphs), NOT_FOUND
            return response_text_err('no graph definition file found'), NOT_FOUND

        return build_all_images_html(graph_list_build)
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/graphs_img/<imagefile>', methods=["GET"], endpoint='route_api_img')
def route_api_img(imagefile):
    '''route: call img'''
    try:
        app.logger.info('route_api_img')
        app.logger.info(imagefile)
        app.logger.info(GRAPHS_IMG+imagefile)

        ret = read_file(GRAPHS_IMG+imagefile)
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

def contains(given_tuple, given_string):
    '''auxiliary function: check if a tuple item starts with given string'''
    for tuple_i in given_tuple:
        if tuple_i.startswith(given_string):
            return True
    return False

#pylint: disable=too-many-arguments
def get_defs_option(graph, graph_def, opt1, opt2, default, input_value):
    '''auxiliary function: execute rrdtool graph
       argument hierarchy:
       1. input value
       2. value in def file
       3. default
    '''
    app.logger.info('get_defs_option '+graph+' '+(opt2 or opt1))

#pylint: disable=too-many-nested-blocks
    sindex = -1
    ret = None, None, None
    while True:
        # 1. check for value in def file:
        for opt in (opt1, opt2):
            if contains(graph_def, opt):
                try:
                    sindex = graph_def.index(opt)
                    if sindex >= len(graph_def) + 1:
                        ret = 'graph '+graph+': wrong option "'+opt, BAD_REQUEST
                        break
                    value = graph_def[sindex+1]     #take value
                    if opt in ('-length', '--length'):
                        value = convert_length(value)
                    ret = value.strip(), OK, sindex
                    if input_value is None:
                        break
                except ValueError as error:
                    app.logger.error(error)
                    ret = 'graph '+graph+': wrong option "'+opt, BAD_REQUEST
                    break
        if ret[1] == BAD_REQUEST:
            break
        if ret[1] == OK and input_value is None:
            break

        # 2. return if input value:
        if input_value is not None:
            ret = input_value, OK, sindex
            break

        # 3. take default value:
        ret = default, OK, -1
        break
    app.logger.info(ret)
    return ret
###get_defs_option

def build_this_graph(graph, start, end, length, width, height, resolution, create_bash=None):
    '''auxiliary function: execute rrdtool graph'''

    ret = read_file(GRAPHS_DEF+graph+'.def')
    if ret[1] != OK:
        return ret[0], ret[1]
    graph_def = make_tuple(ret[0])

    common_def = ()
    sindexlist = []

    ret = get_defs_option(graph, graph_def, '-length', '--length', '1d', length)
    if ret[1] != OK:
        return ret[0], ret[1]
    length = ret[0]
    if ret[2] >= 0:
        sindexlist.append(ret[2])

    start_default = 'end-'+length
    if length and not start:
        start_default = 'end -'+length
    ret = get_defs_option(graph, graph_def, '-s', '--start', start_default, start)
    if ret[1] != OK:
        return ret[0], ret[1]
    start = ret[0]
    if ret[2] >= 0:
        sindexlist.append(ret[2])
        #app.logger.info('sindex='+str(ret[2]))
    #app.logger.info('start='+start)

    ret = get_defs_option(graph, graph_def, '-e', '--end', 'now', end)
    if ret[1] != OK:
        return ret[0], ret[1]
    end = ret[0]
    if ret[2] >= 0:
        sindexlist.append(ret[2])
        #app.logger.info('sindex='+str(ret[2]))
    #app.logger.info('end='+end)

    start_orig = start
    end_orig = end

    if UTC_FOR_GRAPHS == 'yes':
        os.environ["TZ"] = "UTC"

    #check if first or last given:
    get_first = False
    if end and 'first' in end or start and 'first' in start:
        get_first = True
    get_last = False
    if end and 'last' in end or start and 'last' in start:
        get_last = True

    #get all rrd files in graph definition:
    rrd_files = []
    if get_first or get_last:
        for line in graph_def:
            if '.rrd' in line:
                rrd_file = line.replace('=', ':').split(':')[2]
                if not rrd_file in rrd_files:
                    rrd_files.append(rrd_file)

    #get first or last time of all files:
    start, end = replace_times_first_last(start, end, rrd_files)
    start, end = convert_date_format(start, end)

    #app.logger.info('start='+start)
    #app.logger.info('end='+end)

    common_def += ('-s', start)
    common_def += ('-e', end)

    ret = get_defs_option(graph, graph_def, '-w', '--width', WIDTH, width)
    if ret[1] != OK:
        return ret[0], ret[1]
    common_def += ('-w', ret[0])
    if ret[2] >= 0:
        sindexlist.append(ret[2])
        #app.logger.info('sindex='+str(ret[2]))

    ret = get_defs_option(graph, graph_def, '-h', '--height', HEIGHT, height)
    if ret[1] != OK:
        return ret[0], ret[1]
    common_def += ('-h', ret[0])
    if ret[2] >= 0:
        sindexlist.append(ret[2])
        #app.logger.info('sindex='+str(ret[2]))

    ret = get_defs_option(graph, graph_def, '-S', '--step', None, resolution)
    if ret[1] != OK:
        return ret[0], ret[1]
    if ret[0] is not None:
        if not ret[0].isdigit():
#pylint: disable=line-too-long
            return 'graph '+graph+': resolution (--start) must be numeric (number of seconds)', BAD_REQUEST
        resolution = ret[0]
        common_def += ('-S', ret[0])
        if ret[2] >= 0:
            sindexlist.append(ret[2])
            #app.logger.info('sindex='+str(ret[2]))

    ret = get_defs_option(graph, graph_def, '-a', '--imgformats', 'PNG', None)
    if ret[1] != OK:
        return ret[0], ret[1]
    common_def += ('-a', ret[0])
    if ret[2] >= 0:
        sindexlist.append(ret[2])
        #app.logger.info('sindex='+str(ret[2]))
    suffix = '.'+ret[0].lower()
    app.logger.info('suffix='+suffix)
    #app.logger.info('sindex='+str(ret[2]))

    ret = get_defs_option(graph, graph_def, '-t', '--title', None, None)
    if ret[1] != OK:
        return ret[0], ret[1]
    if ret[0]:
        currtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = ret[0].replace('%END', end_orig) .replace('%START', start_orig)
        title = title.replace('%GRAPH', graph) .replace('%CURRTIME', currtime)
        title = title.replace('%RESOL', str(resolution))
        common_def += ('-t', title)
        if ret[2] >= 0:
            sindexlist.append(ret[2])
            app.logger.info('sindex='+str(ret[2]))

    definition = (GRAPHS_IMG + graph + suffix,) + common_def

    #app.logger.info(sindexlist)
#pylint: disable=consider-using-enumerate
    for indx in range(len(graph_def)):
        #app.logger.info(graph_def[indx])
        #skip arguments in def file (already stored):
        if indx not in sindexlist and indx-1 not in sindexlist:
            line = graph_def[indx]
            if '.rrd' in line:
                line = line.replace('=', '='+RRD_PATH, 1)
            if '%RESOL' in line:
                if resolution:
                    line = line.replace('%RESOL,', str(resolution)+',')
                    line = re.sub('%RESOL=[^,]*', str(resolution), line)
                else:
                    line = re.sub('%RESOL=?', '', line)
            definition += (line,)
            #app.logger.info('taken')

    app.logger.info(definition)

    if create_bash is None and CREATE_BASH == 'yes':
        create_bash = 'yes'
    if create_bash == 'yes':
    #create a bash script for this rrdgraph:
        xxx = str(definition).replace("', '", "' \\\n   '")
        xxx = re.sub(r"^\('", "   '", xxx, 1)
        xxx = re.sub(r"'\)$", "'", xxx, 1)
        fil = open(TMP_PATH+graph+'.def.bash', "w")
        bash = 'pushd `dirname "$0"`/..>/dev/null\n'
        if UTC_FOR_GRAPHS == 'yes':
            bash += 'TZ=UTC '
        bash += 'rrdtool graphv \\\n'+xxx+'\n'
        bash += 'popd >/dev/null'
        fil.write(bash)
        fil.close()

    result = rrdtool.graph(*definition)
    app.logger.info(result)
    return 'new version of graph '+graph+' stored', OK
###build_this_graph

@app.route('/build_graph', methods=["GET"], endpoint='route_api_build_graph')
def route_api_build_graph():
    '''route: generate graphs from rrd'''

    try:
        graph_list_build = get_graph_definition_list()
        if graph_list_build == []:
            recgraphs = request.args.get('g')
            if recgraphs:
                return response_text_err('no graph definition file found for '+recgraphs), NOT_FOUND
            return response_text_err('no graph definition file found'), NOT_FOUND

        start, end, length = request_times_args(False)
        width = request.args.get('w')
        height = request.args.get('h')
        resolution = request.args.get('r')
        create_bash = request.args.get('create_bash')

        recgraphs = request.args.get('g')
        if recgraphs is None or '*' in recgraphs:
            if width is None:
                width = WIDTH
            if height is None:
                height = HEIGHT

        for graph in graph_list_build:
            ret = build_this_graph(
                graph, start, end, length, width, height, resolution, create_bash)
            os.environ.pop('TZ', None)
            if ret[1] != OK:
                return response_text_err(ret[0]), ret[1]

        #return response_text('new graphs build', ''), OK
        html = request.args.get('html')
        if html:
            if html == '-':
                return response_text('new graphs build', ''), OK
            ret = read_file(HTML_PATH+html)
            if ret[1] != OK:
                return response_text_err(ret[0]), ret[1]
            return response_text(ret[0], ret[2]), ret[1]
        return build_all_images_html(graph_list_build)
#pylint: disable=broad-except
    except Exception as error:
        os.environ.pop('TZ', None)
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''
###route_api_build_graph

#----- User Web pages -------------------------------------------------------

@app.route('/htm', methods=["GET"], endpoint='route_api_html')
@app.route('/htm/', methods=["GET"], endpoint='route_api_html')
@app.route('/html', methods=["GET"], endpoint='route_api_html')
@app.route('/html/', methods=["GET"], endpoint='route_api_html')
def route_api_html():
    '''route: call html index'''
    app.logger.info('route_api_html')
    try:
        ret = read_file(HTML_PATH+'index.html')
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/html/<filename>', methods=["GET"], endpoint='route_api_html_filename')
def route_api_html_filename(filename):
    '''route: call html'''
    app.logger.info('route_api_html_filename')
    try:
        app.logger.info(filename)
        ret = read_file(HTML_PATH+filename)
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

@app.route('/html/<folder>/<filename>', methods=["GET"], endpoint='route_api_html_folder_filename')
def route_api_html_folder_filename(folder, filename):
    '''route: call html folder'''
    app.logger.info('route_api_html_folder_filename')
    try:
        if folder == 'graphs_img':
            fil = GRAPHS_IMG+filename
        elif folder == 'html':
            fil = HTML_PATH+filename
        else:
            fil = HTML_PATH+folder+'/'+filename
        app.logger.info(fil)

        file_extension = os.path.splitext(fil)[1]
        if folder == 'cgi-bin' and file_extension == '.cgi':
            ret = subprocess.check_output([RUN_CGI, fil]).decode("utf-8")
            return response_text(ret, 'text/html'), OK

        ret = read_file(fil)
        if ret[1] != OK:
            return response_text_err(ret[0]), ret[1]
        return response_text(ret[0], ret[2]), ret[1]
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

#----- SQL like commands ----------------------------------------------------

@app.route('/sql', methods=["GET"], endpoint='route_api_sql')
@app.route('/sql/json', methods=["GET"], endpoint='route_api_sql')
def route_api_sql():
    '''route: invoke a sql command
       select usertime, ts, aaa, bbb, ccc
       from db
       where ts > start and ts <= end;
    '''
#pylint: disable=too-many-nested-blocks
    try:
        command = request_correct_arg('c', 'command')
        if command is None:
            command = urllib.parse.unquote(str(request.query_string, "utf-8"))
        app.logger.info(command)

        if not command:
            return response_text_err('command missing'), BAD_REQUEST

        command = re.sub(r'\s*;', ';', command)
        command = re.sub(r'\s*,\s*', ' , ', command)
        command = re.sub(r'\s*=\s*', ' = ', command)
        command = re.sub(r'\s*>\s*', ' > ', command)
        command = re.sub(r'\s*>\s*=\s*', ' >= ', command)
        command = re.sub(r'\s*<\s*', ' < ', command)
        command = re.sub(r'\s*<\s*=\s*', ' <= ', command)

        app.logger.info('command='+command)
        commandlist = command.split()
        app.logger.info(commandlist)
        command += ' '

        #check command:
        commandlength = len(commandlist)
        if commandlength < 3:
            return response_text_err('statement incomplete'), BAD_REQUEST
        if commandlist[0] != 'select':
            return response_text_err('select keyword missing'), BAD_REQUEST
        if not ' from ' in command:
            return response_text_err('from keyword missing'), BAD_REQUEST
        fromindex = commandlist.index('from')
        if not ' where ' in command:
            wherecondition = False
        else:
            wherecondition = True
            whereindex = commandlist.index('where')
            if whereindex == fromindex+1:
                return response_text_err('database missing'), BAD_REQUEST
            if whereindex >= commandlength:
                wherecondition = False

        #get cf:
        cif = 'LAST'
        app.logger.info(command)
        if ' cf = ' in command:
            cifindex = commandlist.index('cf')+2
            #app.logger.info(str(cifindex))
            if cifindex < commandlength:
                cif = commandlist[cifindex].upper()
                if not cif in ('LAST', 'AVERAGE', 'MIN', 'MAX'):
                    return response_text_err('cf value '+cif+' not allowed'), BAD_REQUEST
        app.logger.info('cif='+str(cif))

        #get resolution:
        resolution = None
        if ' r = ' in command:
            resindex = commandlist.index('r')+2
            #app.logger.info(str(resindex))
            if resindex < commandlength:
                resolution = commandlist[resindex]
        app.logger.info('r='+str(resolution))

        #get dbase name:
        dbase = commandlist[fromindex+1]
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND
        app.logger.info(dbase)

        #get columns from database:
        lastupdate = rrdtool.lastupdate(RRD_PATH+dbase+'.rrd')
        app.logger.info(lastupdate)

        #get columns for return from command:
        columnlist = []
        headline = False
        if fromindex == 1:
            columnlist.append('*')
            headline = True
        elif commandlist[1] == '*':
            columnlist.append('*')
        else:
            for i in range(1, fromindex, 1):
                if commandlist[i] == '*':
                    columnlist = ['*']
                    break
                if commandlist[i] != ',':
                    col = commandlist[i]
                    columnlist.append(col)
                    if col not in ('ts', 'usertime'):
                        if not col in lastupdate['ds']:
                            return response_text_err('wrong column '+col), BAD_REQUEST
            if len(columnlist) == 0:
                return response_text_err('columns missing'), BAD_REQUEST
        if columnlist == ['*']:
            columnlist = list(lastupdate['ds'].keys())
            columnlist.insert(0, "ts")
            columnlist.insert(0, "usertime")
        app.logger.info(columnlist)

        #get time conditions from command:
        start = ''
        end = ''
        msecs = False
        if wherecondition:
            for i in range(whereindex+1, commandlength, 1):
                if commandlist[i] == 'ts':
                    if i > commandlength-2:
                        return response_text_err('last time condition incomplete'), BAD_REQUEST
                    if not commandlist[i+1] in ('>=', '<=', '>', '<'):
                        app.logger.info(commandlist[i])
                        app.logger.info(commandlist[i+1])
                        app.logger.info(commandlist[i+2])
                        return response_text_err('time condition incomplete/ wrong'), BAD_REQUEST
                    if commandlist[i+1] in ('<=', '<'):
                        for j in range(i+2, commandlength, 1):
                            if commandlist[j] in ('and', 'ts', 'cf'):
                                break
                            if end != '':
                                end += ' '
                            end += commandlist[j]
                    elif commandlist[i+1] in ('>=', '>'):
                        for j in range(i+2, commandlength, 1):
                            if commandlist[j] in ('and', 'ts', 'cf'):
                                break
                            if start != '':
                                start += ' '
                            start += commandlist[j]
            if start.isdigit():
                if int(start) >= 1000000000000:
                    start = start[0:10]
                    msecs = True
            if end.isdigit():
                if int(end) >= 1000000000000:
                    end = end[0:10]
                    msecs = True
        if start == '':
            start = 'end-1d'
        if end == '':
            end = 'now'

        start, end = replace_times_first_last(start, end, [dbase+'.rrd'])
        start, end = convert_date_format(start, end)

        #fetch
        params = (RRD_PATH+dbase+'.rrd', cif, '-s', start, '-e', end, '-a')
        if resolution:
            params += ('--resolution', resolution)
        app.logger.info(params)
        fetch = rrdtool.fetch(*params)
        fstart = fetch[0][0]
        fstep = fetch[0][2]
        fds = fetch[1]
        frows = fetch[2]

        #map result:
        res = ''
        ret_type = 'string'
        if '/json' in request.path:
            res = []
            ret_type = 'json'

        if headline:
            line = []
            line_string = ''
            for j in range(0, len(columnlist), 1):
                if j > 0:
                    line_string += ', '
                line.append(columnlist[j])
                line_string += columnlist[j]
            if ret_type == 'string':
                res = line_string+'\n'
            else:
                res.append(line)

        for i in range(0, len(frows)-1, 1):
            line = []
            line_string = ''
            currts = fstart + (i+1) * fstep
            for j in range(0, len(columnlist), 1):
                if j > 0:
                    line_string += ', '
                if columnlist[j] == 'ts':
                    if msecs:
                        line.append(currts*1000)
                        line_string += str(currts*1000)
                    else:
                        line.append(currts)
                        line_string += str(currts)
                elif columnlist[j] == 'usertime':
                    utime = buildusertime(currts)
                    line.append(utime)
                    line_string += utime
                else:
                    val = frows[i][fds.index(columnlist[j])]
                    line.append(val)
                    line_string += str(val)
            if ret_type == 'string':
                if res == '':
                    res = line_string+'\n'
                else:
                    res += line_string+'\n'
            else:
                res.append(line)

        if ret_type == 'string':
            return response_text(res, 'text/plain'), OK
        return response_text(res, 'application/json'), OK
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, None)
        return response_text_err(ret), BAD_REQUEST, ''

#select ts,zaehler,verbrauch from strom where cf=LAST and ts > 1669503600 and ts <= 1669736328

#----------------------------------------------------------------------------
