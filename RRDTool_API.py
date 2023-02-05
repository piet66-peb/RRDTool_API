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
#h Version:      V1.0.0 2023-02-05/peb
#v History:      V1.0.0 2022-11-23/peb first version
#h Copyright:    (C) piet66 2022
#h License:      http://opensource.org/licenses/MIT
#h
#h-------------------------------------------------------------------------------
'''

#pylint: disable=too-many-lines
#pylint: disable=inconsistent-return-statements, too-many-return-statements
#pylint: disable=too-many-branches, too-many-locals, too-many-statements

import os
import traceback
import platform
import glob
from datetime import datetime
import re
from functools import wraps     #only for correct module documentation
import locale
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

locale.setlocale(locale.LC_ALL, '')  # this will use the locale as set in the environment variables

MODULE = 'RRDTool_API.py'
VERSION = 'V1.0.0'
WRITTEN = '2023-02-05/peb'
PYTHON = platform.python_version()
PYTHON_RRDTOOL = rrdtool.__version__
RRDTOOL = rrdtool.lib_version()
FLASK_VERSION = __version__

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
#pylint: enable=invalid-name

#----------------------------------------------------------------------------

# constants
GRAPHS_IMG = './graphs_img/'
GRAPHS_DEF = './graphs_def/'
HTML_PATH = './html/'
RRD_PATH = './rrd/'
if hasattr(settings, 'RRD_PATH'):
    RRD_PATH = settings.RRD_PATH
    if RRD_PATH[-1] != '/':
        RRD_PATH += '/'
ENABLE_MD_BLOCK = False
if hasattr(settings, 'ENABLE_MD_BLOCK'):
    ENABLE_MD_BLOCK = settings.ENABLE_MD_BLOCK
    if ENABLE_MD_BLOCK is not True:
        ENABLE_MD_BLOCK = False

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

#pylint: disable=no-member
if hasattr(settings, 'LOGLEVEL'):
    LOGLEVEL = settings.LOGLEVEL
else:
    LOGLEVEL = 20
app.logger.setLevel(LOGLEVEL)
if hasattr(settings, 'DISABLE_AUTHENTICATION'):
    DISABLE_AUTHENTICATION = settings.DISABLE_AUTHENTICATION
else:
    DISABLE_AUTHENTICATION = False
if hasattr(settings, 'USERNAME'):
    USERNAME = settings.USERNAME
else:
    raise RuntimeError('no USERNAME defined in settings.py!')
if hasattr(settings, 'PASSWORD'):
    PASSWORD = settings.PASSWORD
else:
    raise RuntimeError('no PASSWORD defined in settings.py!')
if hasattr(settings, 'ALLOW_WRITE_WITH_GET'):
    ALLOW_WRITE_WITH_GET = settings.ALLOW_WRITE_WITH_GET
else:
    ALLOW_WRITE_WITH_GET = False
if hasattr(settings, 'CORS_HOST'):
    CORS_HOST = settings.CORS_HOST
else:
    CORS_HOST = None
    app.logger.warning('no CORS_HOST defined in settings.py!')
if hasattr(settings, 'WHITELIST_GET'):
    WHITELIST_GET = settings.WHITELIST_GET
else:
    WHITELIST_GET = []
if hasattr(settings, 'WHITELIST_POST'):
    WHITELIST_POST = settings.WHITELIST_POST
else:
    WHITELIST_POST = []
#pylint: enable=no-member

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

def replace_times_first_last(start, end, rrd_file_list):
    '''replaces first and last in time argument by the timstamp'''
    first = 'first'
    last = 'last'
    combi = start + ' ' +end
    ret = (start, end)
    if first not in combi and last not in combi:
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
    response = make_response('<font color=red size=+2>'+text+'</font>')
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
def get_database_list(remove_ext):
    '''auxiliary function: get database list'''
    files = glob.glob(RRD_PATH+'*.rrd')
    dbs = []
    for file_i in files:
        if remove_ext:
            dbs.append(os.path.splitext(file_i)[0])
        else:
            dbs.append(file_i)
    dbs.sort()
    return dbs

# get graph list
def get_graph_list(remove_ext):
    '''auxiliary function: get graph list'''
    files = glob.glob(GRAPHS_IMG+'*.*')
    graphs = []
    for file_i in files:
        if remove_ext:
            graphs.append(os.path.splitext(os.path.basename(file_i))[0])
        else:
            graphs.append(os.path.basename(file_i))
    graphs.sort()
    return graphs

# get graph definition list
def get_graph_def_list(remove_ext):
    '''auxiliary function: get graph definition list'''
    files = glob.glob(GRAPHS_DEF+'*.def')
    graphs = []
    for file_i in files:
        if remove_ext:
            graphs.append(os.path.splitext(os.path.basename(file_i))[0])
        else:
            graphs.append(os.path.basename(file_i))
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
    try:
        info = {"MODULE": MODULE,
                "VERSION": VERSION,
                "WRITTEN": WRITTEN,
                "PYTHON": PYTHON,
                "FLASK": FLASK_VERSION,
                "RRDTOOL": RRDTOOL,
                "PYTHON_RRDTOOL": PYTHON_RRDTOOL,
                "STARTED": STARTED
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
    try:
        if not os.path.isfile(RRD_PATH+dbase+'.rrd'):
            return response_text_err('database '+dbase+' not found'), NOT_FOUND

        cif = request.args.get('cf', 'LAST')
#pylint: disable=unused-variable
        start, end, length = request_times_args()

        start, end = replace_times_first_last(start, end, [dbase+'.rrd'])
        start, end = convert_date_format(start, end)

        times = request.args.get('times', 'yes')

        params = (RRD_PATH+dbase+'.rrd', cif, '-s', start, '-e', end, '-a')
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

def convert_string_to_tuple(inputstring):
    '''route: response graph definition(s)s'''
    #inputstring = inputstring.replace('(', '').replace(')', '').replace('"', '').replace("'", '')
    xxxx = inputstring.split('\n')
    #x = list(x)
    return xxxx

@app.route('/print_graph_definition', methods=["GET"])
def print_graph_definition():
    '''route: response graph definition(s)s'''
    try:
        recgraphs = request.args.get('g')
        if recgraphs:
            all_graphsdefs = get_graph_def_list(True)
            for recgraphs_i in recgraphs.split(':'):
                if not recgraphs_i in all_graphsdefs:
                    return response_text_err(
                        'no definition file found for graph ' + recgraphs_i), DB_ERROR

        graph_list = get_graph_def_list(True)
        if graph_list == []:
            return response_text_err('no graph definition found'), NOT_FOUND
        graph_def_array = []
        for graph in graph_list:
            if not recgraphs or graph in recgraphs:
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

# build images webpage
def build_all_images_html(recgraphs):
    '''auxiliary function: builds a html page with all images'''
    html = '''
<!DOCTYPE html>
<html>
<head>
   <link rel="shortcut icon" href="icon.png" />
   <title>RRDTool Graphs</title>
</head>
<body>
'''
    if not recgraphs:
        #get all graph files in local folder
        files = glob.glob(GRAPHS_IMG+'*.*')
        files.sort()
        for file_i in files:
            mimetype = get_mimetype_by_suffix(file_i)[1]
            if mimetype == ():
                app.logger.info("mimetype for "+file_i+' not detected')
                continue
            if 'image' in mimetype:
                full_file_i = GRAPHS_IMG+os.path.basename(file_i)
                html += '   <img src="'+full_file_i+'"'
                html += ' alt="actually the image '+full_file_i
                html += ' should have been displayed here"><br><br>\n'
            else:
                html += '   <a href="'+file_i+'">'+file_i+'</a> <br><br>\n'

    else:
        for recgraphs_i in recgraphs.split(':'):
            files = glob.glob(GRAPHS_IMG+recgraphs_i+'.*')
            files.sort()
            for file_i in files:
                mimetype = get_mimetype_by_suffix(file_i)[1]
                if mimetype == ():
                    app.logger.info("mimetype for "+file_i+' not detected')
                    continue
                if 'image' in mimetype:
                    full_file_i = GRAPHS_IMG+os.path.basename(file_i)
                    html += '   <img src="'+full_file_i+'"'
                    html += ' alt="actually the image '+full_file_i
                    html += ' should have been displayed here"><br><br>\n'
                else:
                    html += '   <a href="'+file_i+'">'+file_i+'</a> <br><br>\n'
    html += '</body>\n</html>'
    return html

@app.route('/display_graph', methods=["GET"], endpoint='route_api_display_graph')
def route_api_display_graph():
    '''route: call graphs html'''
    try:
        recgraphs = request.args.get('g')
        if recgraphs:
            all_graphsdefs = get_graph_def_list(True)
            for recgraphs_i in recgraphs.split(':'):
                if not recgraphs_i in all_graphsdefs:
#pylint: disable=line-too-long
                    return response_text_err('no image file found for graph ' + recgraphs_i), DB_ERROR

        return build_all_images_html(recgraphs)
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
    '''auxiliary function: execute rrdtool graph'''
    app.logger.info('get_defs_option '+graph+' '+(opt2 or opt1))

    ret = '?', BAD_REQUEST
    sindex = -99
    for opt in (opt1, opt2):
        if contains(graph_def, opt):
            try:
                sindex = graph_def.index(opt)
                if sindex >= len(graph_def) + 1:
                    ret = 'graph '+graph+': wrong option "'+opt, BAD_REQUEST
                else:
                    value = graph_def[sindex+1]     #take value
                    if opt in ('-length', '--length'):
                        value = convert_length(value)
                    ret = value, OK
            except ValueError as error:
                app.logger.info(error)
                ret = 'graph '+graph+': wrong option "'+opt, BAD_REQUEST
    if input_value is not None:
        ret = input_value, OK       #input overwrites rrd value
    elif ret[1] != OK:
        ret = default, OK           #set default if nothing else is set

    if ret[1] != OK:
        ret = 'graph '+graph+': programming error at"'+opt, BAD_REQUEST
    else:
        ret = str(ret[0]).strip(), ret[1], sindex
        #app.logger.info(opt1+' argument='+retstr[0])
    return ret

def build_this_graph(graph, start, end, length, width, height):
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

    ret = get_defs_option(graph, graph_def, '-w', '--width', settings.WIDTH, width)
    if ret[1] != OK:
        return ret[0], ret[1]
    common_def += ('-w', ret[0])
    if ret[2] >= 0:
        sindexlist.append(ret[2])
        #app.logger.info('sindex='+str(ret[2]))

    ret = get_defs_option(graph, graph_def, '-h', '--height', settings.HEIGHT, height)
    if ret[1] != OK:
        return ret[0], ret[1]
    common_def += ('-h', ret[0])
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
        title = ret[0].replace('%E', end_orig).replace('%S', start_orig).replace('%G', graph)
        currtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = title.replace('%T', currtime)
        common_def += ('-t', title)
        if ret[2] >= 0:
            sindexlist.append(ret[2])
            app.logger.info('sindex='+str(ret[2]))

    definition = (GRAPHS_IMG + graph + suffix,) + common_def

    #app.logger.info(sindexlist)
#pylint: disable=consider-using-enumerate
    for indx in range(len(graph_def)):
        #app.logger.info(graph_def[indx])
        if indx not in sindexlist and indx-1 not in sindexlist:
            line = graph_def[indx]
            if '.rrd' in line:
                line = line.replace('=', '='+RRD_PATH)
            definition += (line,)
            #app.logger.info('taken')

    app.logger.info(definition)
    result = rrdtool.graph(*definition)
    app.logger.info(result)
    return 'new version of graph '+graph+' stored', OK
###build_this_graph

@app.route('/build_graph', methods=["GET"], endpoint='route_api_build_graph')
def route_api_build_graph():
    '''route: generate graphs from rrd'''

    try:
        recgraphs = request.args.get('g')
        if recgraphs:
            all_graphsdefs = get_graph_def_list(True)
            for recgraphs_i in recgraphs.split(':'):
                if not recgraphs_i in all_graphsdefs:
                    return response_text_err(
                        'no definition file found for graph ' + recgraphs_i), DB_ERROR

        start, end, length = request_times_args(False)

        width = request.args.get('w')
        height = request.args.get('h')

        graph_list = get_graph_def_list(True)
        if graph_list == []:
            return response_text_err('no graph definition found'), NOT_FOUND

        if recgraphs:
            for graph in recgraphs.split(':'):
                if graph in graph_list:
                    ret = build_this_graph(graph, start, end, length, width, height)
                    if ret[1] != OK:
                        return response_text_err(ret[0]), ret[1]
        else:
            if width is None:
                width = settings.WIDTH
            if height is None:
                height = settings.HEIGHT
            for graph in graph_list:
                ret = build_this_graph(graph, start, end, length, width, height)
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
        return build_all_images_html(recgraphs)
#pylint: disable=broad-except
    except Exception as error:
        ret = build_except_err_string(error, graph)
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
            fil = './'+folder+'/'+filename
        elif folder == 'html':
            fil = './html/'+filename
        else:
            fil = './html/'+folder+'/'+filename
        app.logger.info(fil)

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
        app.logger.info('000')
        app.logger.info(command)
        if ' cf = ' in command:
            app.logger.info('111')
            cifindex = commandlist.index('cf')+2
            app.logger.info(str(cifindex))
            if cifindex < commandlength:
                app.logger.info('222')
                cif = commandlist[cifindex].upper()
                if not cif in ('LAST', 'AVERAGE', 'MIN', 'MAX'):
                    app.logger.info('333')
                    return response_text_err('cf value '+cif+' not allowed'), BAD_REQUEST

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
