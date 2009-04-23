

from StringIO import StringIO
import os

import re
from google.appengine.ext import webapp
from google.appengine.api import memcache
from utils.js.jsmin import JavascriptMinify
import wsgiref.handlers



memCacheExpire = 100000

debugExpire = 10


def debug_mode():
	if os.environ.get('SERVER_SOFTWARE','').startswith('Devel'):
	  HOST='local'
	  debug = True
	elif os.environ.get('SERVER_SOFTWARE','').startswith('Goog'):
	  HOST='google'
	  debug = False
	return debug
  
  
def jsmin(js):
    ins = StringIO(js)
    outs = StringIO()
    JavascriptMinify().minify(ins, outs)
    str = outs.getvalue()
    if len(str) > 0 and str[0] == '\n':
        str = str[1:]
    return str








jsm = JavascriptMinify()


def getFileName(path):
  return os.path.join(os.path.dirname(__file__) + '/../..' + path)

def getFileContent(filename):  
  ospath = os.path.join(os.path.dirname(__file__), filename)
  input = open(ospath, 'r')
  return input.read()

def minify(filename):    
  path = os.path.join(os.path.dirname(__file__), filename)        
  input = open(path, 'r')
  output = StringIO.StringIO()
  jsm.minify(input, output)
  return output.getvalue()  

def console_safe(js):
    #js = js.replace(r'console.(.*);', '')
    return js
    
class Minify(webapp.RequestHandler):
  def get(self):
    data = memcache.get(self.request.path)    
    if data is None:
      filename = getFileName(self.request.path)
      dm = debug_mode()
      if dm: # debug mode - don't minify. may want to make non-mozilla console-safe
        data = getFileContent(filename)
        expire = debugExpire
      else: 
        data = minify(filename)
        #data = console_safe(data)
        expire = memCacheExpire
      memcache.add(self.request.path, data, expire)      
    self.response.headers['Content-Type'] = 'text/javascript'
    self.response.out.write(data)


class JsMinify_(webapp.RequestHandler):
  def get(self):
    filename = getFileName(self.request.path)
    data = minify(filename)              

    self.response.headers['Content-Type'] = 'text/javascript'
    self.response.out.write(data)


class JsNormal(webapp.RequestHandler):
  def get(self):      

    data = memcache.get(self.request.path)

    if data is None:
      filename = getFileName(self.request.path)
      data = getFileContent(filename)
      memcache.add(self.request.path, data, memCacheExpire)   

    self.response.headers['Content-Type'] = 'text/javascript'
    self.response.out.write(data)

class JsNormal_(webapp.RequestHandler):
  def get(self):      
    filename = getFileName(self.request.path)
    data = getFileContent(filename)

    self.response.headers['Content-Type'] = 'text/javascript'
    self.response.out.write(data)


apps_binding = []

apps_binding.append(('/static/.*', Minify))
"""
# serving normal javascript file directly from disk
apps_binding.append(('/static/scripts_/.*', JsNormal_))

# serving normal javascript file from mem cache
apps_binding.append(('/static/scripts/.*', JsNormal))

# serving minified javascript file directly from disk
apps_binding.append(('/static/scripts/.*', JsMinify_))
"""

# DON'T IMPORT THIS FILE FROM A VIEW REQUEST - IT WILL REINIT THE APP    
application = webapp.WSGIApplication(apps_binding, debug=True)
wsgiref.handlers.CGIHandler().run(application)



