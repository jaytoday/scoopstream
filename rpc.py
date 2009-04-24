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
    





  def add_autotip(self, *args):
	if not self.request.get('user'): return "user required"
	if not self.request.get('pledge'): return "pledge required"
	from datastore import TwitterUser
	new_user = TwitterUser(id = self.request.get('user'), pledge = int(self.request.get('pledge')))
	db.put(new_user)
	return "OK"


  def add_source(self, *args):
  	if not self.request.get('name'): return "name required"
  	from datastore import NewsSource
  	new_source = NewsSource(key_name = self.request.get('name'), name = self.request.get('name'), 
  	twitter_username = self.request.get('name'))
  	db.put(new_source)
	return "OK"

  def add_user(self, *args):
	if not self.request.get('name'): return "name required"
	from datastore import User
	new_user = User(key_name = self.request.get('name'), name = self.request.get('name'), 
	twitter_username = self.request.get('name'))
	db.put(new_user)
	return "OK"



  def twitter_news_refresh(self, *args):
    	from datastore import NewsSource
    	from methods import Links
    	ns = NewsSource.all().fetch(1000)
    	for source in ns:
    	    links = Links(source, news_source=True)
    	    links.twitter_retrieve()
    	    continue 



  def new_user(self, *args):
  	from datastore import User
  	new_user = User(key_name = self.request.get('name'),
  	                name = self.request.get('name'),
  	                twitter_username=self.request.get('name'))
  	db.put(new_user)
  	print ""
  	print "saved new user: " + str(new_user.__dict__)



  def twitter_user_refresh(self, *args):
  	from datastore import User
  	from methods import Links  	
  	us = User.all().fetch(1000)
  	for user in us:
  	    links = Links(user, news_source=False)
  	    links.twitter_retrieve()
  	    continue 



  def find_twitter_scoops(self, *args):
  	from datastore import User
  	from methods import Links  	
  	us = User.all().fetch(1000)
  	for user in us:
  	    links = Links(user, news_source=False)
  	    links.find_scoops()
  	    continue 








