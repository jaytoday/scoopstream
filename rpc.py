from utils import webapp
import logging
from google.appengine.ext import db

class RPCHandler(webapp.RequestHandler):
  # AJAX Handler
  def __init__(self):
    webapp.RequestHandler.__init__(self)

 
  def get(self):
    func = None
    action = self.request.get('action')
    if action:
      if action[0] == '_':
        self.error(403) # access denied
        return
      else:
        func = getattr(self, action, None) # get method
   
    if not func:
      self.error(404) # method not found
      return
    self.response.out.write(func())
    





  def add_user(self, *args):
	if not self.request.get('name'): return "name required"
	from datastore import User
	new_user = User(key_name = self.request.get('name'), 
	                twitter_username = self.request.get('name'))
	# call twitter retrieve?
	db.put(new_user)
	return "OK"



  def new_user(self, *args):
  	from datastore import User
  	new_user = User(key_name = self.request.get('name'),
  	                twitter_username=self.request.get('name'))
  	db.put(new_user)
  	print ""
  	print "saved new user: " + str(new_user.__dict__)





  def find_twitter_scoops(self, *args):
  	from datastore import User
  	from methods import Scoops 	
  	scoops = Scoops()
  	us = User.all().fetch(1000)
  	for user in us: scoops.find_scoops(user)

  def delete_scoops(self, *args):
  	from datastore import Scoop	
  	scoops = Scoop.all().fetch(1000)
  	for scoop in scoops: scoop.delete()
  	from datastore import Link
  	links = Link.all().fetch(1000)
  	for link in links:
  		link.been_scooped = 0
  		link.has_scooped = 0
  	db.put(links)
  	return "OK"



  def create_scoop(self, *args):
  	from fixtures import Fixtures
  	f = Fixtures()
  	f.scoop()





  def save_link(self, *args):
  	from utils.utils import run_task
  	data = run_task('save_link')
  	
 
  def analyze_link(self, *args):
  	from utils.utils import run_task
  	data = run_task('analyze_link')
  	
 
  def twitter_test(self, *args):
  	if not self.request.get('name'): return "name required"
  	from datastore import User
  	user = User.gql("WHERE twitter_username = :1", self.request.get('name')).get()
  	if not user: return "no test user found"
  	from methods import Links
  	link_methods = Links()
  	link_methods.twitter_retrieve(user, test=user.twitter_username)

  def twitter_user_refresh(self, *args):
  	from utils.utils import run_task
  	data = run_task('twitter_user_refresh', backup='twitter_user_backup')


  def wipe(self, *args):
  	from fixtures import Fixtures
  	f = Fixtures()
  	f.wipe(users=self.request.get('users'))
  	self.flush_memcache()

  	
  def flush_memcache(self, *args):
  	from google.appengine.api import memcache
  	print ""
  	print "before flush:", memcache.get_stats()
  	memcache.flush_all()
  	print "after flush:", memcache.get_stats()
  		
  def flag_scoop(self, *args):
  	from methods import Scoops
  	scoop_methods = Scoops()
  	scoop_methods.flag(self.request.get('scoop_key'))
  	return "OK"


  def set_scoop_flags(self, *args):
  	from datastore import Scoop
  	scoops = Scoop.all().fetch(1000)
  	for scoop in scoops:
  		scoop.flagged = 0
  	db.put(scoops)
  	return "OK"


