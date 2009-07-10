
import os
import logging
from google.appengine.ext import db
from google.appengine.api import users
import webapp.template
from webapp import *



ROOT_PATH = os.path.dirname(__file__) + "/.."


def tpl_path(template_file_name):
    return os.path.join(ROOT_PATH,
                        './templates', template_file_name)





def require_login(uri):
  if users.get_current_user():
    LOGINSTATUS = "logged in"
    return LOGINSTATUS
  else:
    redirect(users.create_login_url(uri))




def redirect_to_login(*args, **kwargs):
    return args[0].redirect(users.create_login_url(args[0].request.uri))



def browser_check(wsgi_app):
    def redirect_if_needed(env, start_response):
        if "Mozilla/4.0" in env.get('HTTP_USER_AGENT',()): # MSIE - are there any others we need?
            import webob, urlparse
            request = webob.Request(env)
            if '/js/' in request.url: pass # doesn't apply to script handlers
            scheme, netloc, path, query, fragment = urlparse.urlsplit(request.url)
            error_path = '/error/browser'
            if path == error_path: return wsgi_app(env, start_response) # avoid infinite loops
            url = urlparse.urlunsplit([scheme, netloc,  error_path, query, fragment])
            start_response('301 Moved Permanently', [('Location', url)])
            return
        return wsgi_app(env, start_response)
    return redirect_if_needed

          
# 404
class NotFoundPageHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        path = tpl_path('utils/404.html')
        template_values = {'no_load': True}
        self.response.out.write(template.render(path, template_values))



def GetPathElements():
    '''split PATH_INFO out to a list, filtering blank/empty values'''
    return [ x for x in os.environ['PATH_INFO'].split('/') if x ]

def GetUserAgent():
    '''return the user agent string'''
    return os.environ['HTTP_USER_AGENT']

def Debug():
    '''return True if script is running in the development envionment'''
    return  'Development' in os.environ['SERVER_SOFTWARE']


def hash_pipe(private_object):
    import md5 # TODO use something else
    from google.appengine.api import memcache
    new_hash = md5.md5()
    new_hash.update(str(private_object))
    public_token = new_hash.hexdigest()
    memcache.add(public_token, private_object, 6000) # length?
    return public_token



#### MEMCACHE

def memoize(key, time=1000000):
    """Decorator to memoize functions using memcache."""
    
    def decorator(fxn):
        def wrapper(*args, **kwargs):
            from google.appengine.api import memcache
            data = memcache.get(key)
            if Debug(): return fxn(*args, **kwargs) # not active in dev mode - could this be cause of production expires problem?
            if data is not None:
                return data
            data = fxn(*args, **kwargs)
            memcache.set(key, data, time)
            return data
        return wrapper
    return decorator  


### TASKS

def task(task_type, time=1000000, shuffle=False):
    """Decorator to memoize functions using memcache."""
    
    def decorator(fxn):
        def wrapper(*args, **kwargs):
            from google.appengine.api import memcache
            task_list = memcache.get(task_type) 
            if kwargs.get('run_task') is True: 
               data = fxn(*args, **kwargs)
               return data
            if not task_list: task_list = [ kwargs ]
            elif kwargs in task_list:
                  print "ALREADY EXISTS"
                  return False 
            if kwargs not in task_list: task_list.append(kwargs)                                
            if shuffle: 
                import random
                random.shuffle(task_list)
            memcache.set(task_type, task_list, time)
            return True
        return wrapper
    return decorator  


def run_task(task_type, time=1000000, backup=None):

    from google.appengine.api import memcache
    from methods import Tasks
    task_list = memcache.get(task_type)
    try: kwargs = task_list.pop(0)
    except:
        logging.info("no task items left for task: %s" % task_type)
        if backup:
            print "backup"
            tasks = Tasks()
            bk_fxn = getattr(tasks, backup, None)
            if bk_fxn: bk_fxn() 
            return True     
        return False
    tasks = Tasks()
    fxn = getattr(tasks, task_type, None)
    print ""
    print kwargs
    kwargs['run_task'] = True
    if not fxn: 
        logging.warning("cannot get function for task: %s" % task_type)
        return False    
    data = fxn(**kwargs)
    if not data: 
        logging.warning("cannot get data for task: %s" % task_type)
        return False
    if data == "fail":
        logging.info('what we have here is a failure to communicate %s' % task_type)
        f = memcache.get("fail" + task_type)
        if f is None: f = 0
        else: f += 1
        if f > 2: memcache.set("fail" + task_type, None, time)
        else: 
            memcache.set("fail" + task_type, f, time)
            return False
        logging.info('your failure is complete - %s' % task_type) 
    memcache.set(task_type, task_list, time)
    if data == "rerun":
        logging.info("rerunning task: %s" % task_type)
        return run_task(task_type)
    return data


def entity_set(entity_list):
	set_list = []
	key_list = []
	for entity in entity_list:
	    try:
	      if entity.key() not in key_list:
	        key_list.append( entity.key() )
	        set_list.append( entity )
	    except:
	        logging.warning('unable to access key for entity: %s' % entity.__dict__ )
	        continue
	return set_list
	        
	    

### SESSIONS


def set_flash(msg):
	from appengine_utilities.sessions import Session
	session = Session()
	session['flash_msg'] = msg
	return msg


def get_flash(keep=False):
    from appengine_utilities.sessions import Session
    session = Session()
    msg = session['flash_msg']
    if not keep: session['flash_msg'] = False
    return msg
    


### RANDOM

def sort_by_attr(seq,attr):
    intermed = [ (getattr(seq[i],attr), i, seq[i]) for i in xrange(len(seq)) ]
    intermed.sort()
    intermed.reverse() # ranked from greatest to least
    return [ tup[-1] for tup in intermed ]



def jsonp(callback, html):
    html = html.replace('\r\n','').replace("\n", "").replace("'", "&rsquo;");
    return callback + "('" + html + "');"

def compress(data):
    import gzip 
    import cStringIO
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=2, fileobj=zbuf)
    zfile.write(data)
    zfile.close()
    return zbuf.getvalue()


def minify(js):
		from StringIO import StringIO
		from js.jsmin import JavascriptMinify
		ins = StringIO(js)
		outs = StringIO()
		JavascriptMinify().minify(ins, outs)   
		str = outs.getvalue()
		if len(str) > 0 and str[0] == '\n':
			str = str[1:]
		return str #compress(str)




def css_minify(css):
		return css.replace("\n", "")
		


