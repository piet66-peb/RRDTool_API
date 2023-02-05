'''
####
#### Parametrization for RRDTool_API.py
#### restart API after every change !
####
'''

####
#### loglevel:
#### 20 = INFO, 30 = ERROR + WARNING
####
LOGLEVEL = 30

####
#### path to rrd databases:
####
RRD_PATH = './rrd'

####
#### enable external Markdown viewer libraries md-block
#### if disabled you will need a Markdown viewer plugin for the browser
#### to display md files
####
#ENABLE_MD_BLOCK = True
ENABLE_MD_BLOCK = False

####
#### defaults:
####
WIDTH = 1200
HEIGHT = 200

####
#### authentication for write accesses
#### (read accesses don't need any authentication)
#### recommendation: don't disable authentication
####
#DISABLE_AUTHENTICATION = True   #default: False
USERNAME = 'username'
PASSWORD = 'secret'

####
#### accept GET method for write accesses
#### (per default only POST method has write access)
#### recommendation: only for testing purpose
####     only enable temporarily if really necessary
####     all remote client hosts in whitelist can use that
####
#ALLOW_WRITE_WITH_GET = True     #default: False

####
#### allow Cross-Origin Resource Sharing for clients writing to database
#### this line enables indirect write access for remote clients
####
#CORS_HOST = ["http://192.168.178.22:8083"]

####
#### define whitlists for HTTP API clients
#### a server not in the whitelist has not the appropriate rights
#### WHITELIST_GET: whitelist for all client hosts (read access)
#### WHITELIST_POST: whitelist for all client hosts (write access)
#### only ip addresses are allowed, maybe with wildcards
#### recommendation: restrict WHITELIST_POST to trustworthy hosts
####
WHITELIST_GET = ["127.0.0.1", "192.168.178.*"]
WHITELIST_POST = ["127.0.0.1", "192.168.178.22", "192.168.178.28", "192.168.178.42"]
