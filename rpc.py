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
        func = getattr(self, action, None)
   
    if not func:
      self.error(404) # file not found
      return
    self.response.out.write(func())
    





  def add_autotip(self, *args):
	if not self.request.get('user'): return "user required"
	if not self.request.get('pledge'): return "pledge required"
	from datastore import TwitterUser
	new_user = TwitterUser(id = self.request.get('user'), pledge = int(self.request.get('pledge')))
	db.put(new_user)
	return "OK"
