import os
import logging
from google.appengine.ext import db


from memoize import memoize, NoneVal

ROOT_PATH = os.path.dirname(__file__) + "/.."


def redirect_to_login(*args, **kwargs):
    from google.appengine.api import users
    return args[0].redirect(users.create_login_url(args[0].request.uri))

def admin_only(handler):
    def wrapped_handler(*args, **kwargs):    
        # allow cron jobs (TODO: make sure tasks also work!)
        for gae_header in ['X-AppEngine-TaskName', 'X-AppEngine-Cron']:
          if args[0].request.headers.get(gae_header, None):
            logging.info("giving script permission for header %s" % gae_header)
            return handler(args[0])
        from google.appengine.api import users
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                return handler(args[0])
            else:
                logging.warning('An unauthorized user has attempted\
 to use admin_only method %s' % str(args[0]))
                return redirect_to_login(*args, **kwargs)
        else:
            logging.warning('unknown user attempting to access admin only\
 method %s. redirecting to login.' % str(args[0]))
            return redirect_to_login(*args, **kwargs)

    return wrapped_handler


def is_admin():
  # check if user is admin
  is_admin = False	
  from google.appengine.api import users
  user = users.get_current_user()
  if user:
    if users.is_current_user_admin():
      is_admin = True
  return is_admin



def http_host():
  host = os.environ['HTTP_HOST']
  # Only because we have yupgrade domain
  if 'yupgrade.appspot.com' in host:
    host = host.split('.appspot.com')[0] + ".com"
  if 'latest.' in host:
    host = host.split('latest.')[1] 
  if Production() and len( host.split('.') ) < 3:
    host = 'www.' + host
  return "http://" + host

def GetPathElements():
    '''split PATH_INFO out to a list, filtering blank/empty values'''
    return [ x for x in os.environ['PATH_INFO'].split('/') if x ]

def GetUserAgent():
    '''return the user agent string'''
    return os.environ['HTTP_USER_AGENT']

def Debug():
    '''return True if script is running in the development envionment'''
    return 'Development' in os.environ['SERVER_SOFTWARE']

def Production():
  import app_settings, os
  return ('Development' not in os.environ['SERVER_SOFTWARE']
  ) and os.environ['APPLICATION_ID'] == app_settings.PRODUCTION_APP_ID


def hash_pipe(private_object):
    import md5 # TODO use something else
    from google.appengine.api import memcache
    new_hash = md5.md5()
    new_hash.update(str(private_object))
    public_token = new_hash.hexdigest()
    memcache.add(public_token, private_object, 6000) # length?
    return public_token


def randomInt(digits=5):
  max = int(''.join('9' for d in range(digits)))
  import random
  return int(str(random.randint(0,max)).zfill(digits))
  
def entity_set(entity_list):
	from google.appengine.ext.db import NotSavedError
	set_list = []
	key_list = []
	for entity in entity_list:
	    try:
	      if entity.key() not in key_list:
	        key_list.append( entity.key() )
	        set_list.append( entity )
	    except NotSavedError: 
	        # NOTE: make sure new items can't be added twice!
	        logging.info(
	        'unable to access key for entity %s' % entity.__dict__ )
	        set_list.append( entity )
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

def sort_by_attr(seq,attr, reverse=True):
    intermed = [ (getattr(seq[i],attr), i, seq[i]) for i in xrange(len(seq)) ]
    intermed.sort()
    if reverse: 
      intermed.reverse() # ranked from greatest to least
    return [ tup[-1] for tup in intermed ]

def sort_by_key(seq,attr, reverse=True):
    intermed = [ (seq[i][attr], i, seq[i]) for i in xrange(len(seq)) ]
    intermed.sort()
    if reverse: 
      intermed.reverse() # ranked from greatest to least
    return [ tup[-1] for tup in intermed ]
       
       
# set descriptor
def setdesc(x, name, desc):
  t = type(x)
  if not issubclass(t, wrapper):
    class awrap(Wrapper, t): pass
    x.__class__ = awrap
  setattr(x.__class__, name, desc)

def jsonp(callback, html):
    html = html.replace('\r\n','').replace("\n", "").replace("'", "&rsquo;");
    return callback + "('" + html + "');"


def compress(data, compresslevel=9):
    """
    gzips - might be WSGI issue?
    if you can get this to work, patch minify and cssmin
    """
    import cStringIO
    import gzip
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=compresslevel, fileobj=zbuf)
    try: zfile.write(data)
    except UnicodeEncodeError:
      logging.error('error gzipping content %s' % data[:20])
      return data
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
		return str


def frequency_rank(l):
	# Relevency Tally for Semantic Tags
	from collections import defaultdict
	import operator 
	# tag ranking helper function
	# take a list of tags ['tag1', 'tag2', 'tag2', tag3'....]
	# sort set of tags by order of frequency, top down
	tally = defaultdict(int)
	for x in l:
		tally[x] += 1
	sorted_tags = sorted(tally.items(), key=operator.itemgetter(1))
	tags = []
	for tag in sorted_tags:
		tags.append(tag[0]) 
	tags.reverse()
	return tags
		  

# only for debugging
def set_trace():
    import sys
    import pdb
    for attr in ('stdin', 'stdout', 'stderr'):
        setattr(sys, attr, getattr(sys, '__%s__' % attr))
    return pdb.set_trace # needs to be activated in local scope!

#@memoize() - not worth the memcache hit
def domain_from_url(url):
    import urlparse
    domain = urlparse.urlparse(url)[1]
    # remove subdomain
    split_domain = domain.split('.')
    if len( split_domain ) > 2: # subdomain
      # find the last token longer than 2 chars
      after_frag = ''
      for i, s in enumerate(split_domain[::-1]):
        # this helps us avoid returning 'co.uk'
        # or any other two-part domain extensions
        if after_frag not in ['', 'uk']:
          return ".".join(split_domain[-(i + 1 ):])
        else:
          after_frag = s
    return domain



def defer(method, *args, **kwargs):
  # A payload can also be sent
  from google.appengine.ext.deferred import deferred
  from google.appengine.api.labs import taskqueue
  # _queue, _countdown, name
  kwargs['_name'] = task_name( str(method.__name__) + str(args) + str(kwargs.values()) )
  try:
   deferred.defer(method, *args, **kwargs)
   logging.info('deferred method %s with args %s and kwargs %s' % (method.__name__, args, kwargs))
  except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
    logging.warning('unable to create task with name %s' %
    kwargs['_name'], exc_info=True)
  
def add_task(queue_name='default',payload=None,**kwargs):
  # A payload can also be sent
  if kwargs.get('params', None):
    for json_type in ['kwargs', 'entities']: #
       if kwargs['params'].get(json_type, None):
         from django.utils import simplejson
         kwargs['params'][json_type] = simplejson.dumps(
         kwargs['params'][json_type])
       
  from google.appengine.api.labs import taskqueue
  queue = taskqueue.Queue(name=queue_name)
  try:
    task = taskqueue.Task(payload=payload, **kwargs)
    logging.info('adding task: %s' % kwargs)
    queue.add(task)
  # TODO: Why don't these exceptions work? 
  except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
    logging.warning('unable to create task with name %s' %
    kwargs.get('name','(no name provided)'), exc_info=True)


def task_name(string, timestamp=True, version=True):
  from encoding import utf_to_ascii
  string = utf_to_ascii(string)
  # add timestamp if this task may be repeated
  if timestamp: 
    # always going to be unique
    import time
    full_string= "%s-%s" % (string,
    str(time.time()) + str(time.clock())) # see if this gets rid of errors
  elif version:
    # add version name, so version can be changed to override
    full_string = "%s-%s" % (string, os.environ['CURRENT_VERSION_ID'])
  # remove non alphanumeric chars
  import re
  pattern = re.compile('[^A-Za-z0-9-]')
  safe_string = re.sub(pattern, '', full_string)
  MAX_STR_LENGTH = 100
  return safe_string[:MAX_STR_LENGTH] + str(randomInt(digits=20))


class TaskFailError(Exception):
  """ Tasks fail all the time, but 
  they shouldn't be clogging the error logs. """
  def __init__(self, error_msg):
    logging.warning(error_msg)
    



 
def parseDateTime(s):
	"""Create datetime object representing date/time
	   expressed in a string
 
	Takes a string in the format produced by calling str()
	on a python datetime object and returns a datetime
	instance that would produce that string.
 
	Acceptable formats are: "YYYY-MM-DD HH:MM:SS.ssssss+HH:MM",
							"YYYY-MM-DD HH:MM:SS.ssssss",
							"YYYY-MM-DD HH:MM:SS+HH:MM",
							"YYYY-MM-DD HH:MM:SS"
	Where ssssss represents fractional seconds.	 The timezone
	is optional and may be either positive or negative
	hours/minutes east of UTC.
	"""
	import re
	from datetime import datetime
	if s is None:
		return None
	# Split string in the form 2007-06-18 19:39:25.3300-07:00
	# into its constituent date/time, microseconds, and
	# timezone fields where microseconds and timezone are
	# optional.
	m = re.match(r'(.*?)(?:\.(\d+))?(([-+]\d{1,2}):(\d{2}))?$',
				 str(s))
	datestr, fractional, tzname, tzhour, tzmin = m.groups()
 
	# Create tzinfo object representing the timezone
	# expressed in the input string.  The names we give
	# for the timezones are lame: they are just the offset
	# from UTC (as it appeared in the input string).  We
	# handle UTC specially since it is a very common case
	# and we know its name.
	if tzname is None:
		tz = None
	else:
		tzhour, tzmin = int(tzhour), int(tzmin)
		if tzhour == tzmin == 0:
			tzname = 'UTC'
		tz = FixedOffset(timedelta(hours=tzhour,
								   minutes=tzmin), tzname)
 
	# Convert the date/time field into a python datetime
	# object.
	x = datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")
 
	# Convert the fractional second portion into a count
	# of microseconds.
	if fractional is None:
		fractional = '0'
	fracpower = 6 - len(fractional)
	fractional = float(fractional) * (10 ** fracpower)
 
	# Return updated datetime object with microseconds and
	# timezone information.
	return x.replace(microsecond=int(fractional), tzinfo=tz)
 
 
def topic_methods():
  import topic.methods
  return topic.methods

def student_methods():
  import student.methods
  return student.methods

def sponsor_methods():
  import sponsor.methods
  return sponsor.methods

def izip_longest(*args, **kwds):
    import itertools
    # izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    fillvalue = kwds.get('fillvalue')
    def sentinel(counter = ([fillvalue]*(len(args)-1)).pop):
        yield counter()         # yields the fillvalue, or raises IndexError
    fillers = itertools.repeat(fillvalue)
    iters = [itertools.chain(it, sentinel(), fillers) for it in args]
    try:
        for tup in itertools.izip(*iters):
            yield tup
    except IndexError:
        pass

def slice_up_list(list, max_list_len=30): # 30 is subquery limit
  """ slice up a list by a maximium length.
  """
  list_groups = []
  for i in xrange(0, len(list), max_list_len):
    list_groups.append(list[i: i+max_list_len])
  return list_groups
    

def print_page(url):
  """ fetches and renders a page """
  print ""
  from google.appengine.api import urlfetch
  fetched_page = urlfetch.fetch(url)
  print "PAGE: \n "
  print fetched_page.content





def delete_entities(entities, group=500):
  from itertools import islice 
  entity_groups = iter(lambda x=iter(entities): list(islice(x,group)), []) 
  for items in list(entity_groups):
    db.delete(items)


def save_entities(entities, group=500):
  from itertools import islice 
  entity_groups = iter(lambda x=iter(entities): list(islice(x,group)), []) 
  for items in list(entity_groups):
    db.put(items)


"""

Apparently it is really really bad to parse html with regex.

How about using a library??

"""

# this is just used for mail
def html_to_plaintext(string, trim=True):
  import re
  from encoding import htmldecode
  tag_token = re.compile('<(.*?)>')
  # two lines could be used for closing tag, etc. 
  plaintext_string = re.sub(tag_token,'\
  \
  ',string)
  doc = htmldecode(plaintext_string)
  split_doc = doc.split("\n")
  trimdoc = []
  for i, line in enumerate(split_doc):
    if len(line.replace(" ","")) == 0:
      try:
        if len(split_doc[i+1].replace(" ","")) == 0:
          continue
      except IndexError: pass
    trimdoc.append(line)
  doc = "\n".join(trimdoc)
  return doc


def strip_html(string):
 import re
 tag_token = re.compile('<(.*?)>')
 # two lines could be used for closing tag, etc. 
 plaintext_string = re.sub(tag_token,'',string)
 return plaintext_string




def epoch(value):
  import time
  return int(time.mktime(value.timetuple())  *1000)



def transactionize(fun):
  def decorate(*args, **kwargs):
    return db.run_in_transaction(fun, *args, **kwargs)
  return decorate


def validateZip(*args):
  sizes = []
  for arg in args:
   sizes.append(len(arg))
  for s in sizes:
    differences = [ (-1 < (s - i) < 1) for i in sizes]
    if False in differences:
      logging.error('LIST INEQUALITY! %s' % sizes)
  return zip(*args)


def context_to_string(context):
 response = ''
 for key, value in context.items():
   response += "__"
   response += str(key)
   response += "--"
   if isinstance(value, db.Model):
     response += str(value.key())
   else:
     response += str(value)
 return response
   

"""

Interesting example of decorator

def arg_sayer(what):
    def what_sayer(meth):
        def new(self, *args, **kws):
            print what
            return meth(self, *args, **kws)
        return new
    return what_sayer

def FooMaker(word):
    class Foo(object):
        @arg_sayer(word)
        def say(self): pass
    return Foo()

foo1 = FooMaker('this')
foo2 = FooMaker('that')
print type(foo1),; foo1.say()  # prints: <class '__main__.Foo'> this
print type(foo2),; foo2.say()  # prints: <class '__main__.Foo'> that

"""
