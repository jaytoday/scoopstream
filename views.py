import logging
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import urlfetch



## User name constants
_TWITTERBOT_USER = "mytwitterbot" # The username you use in twitter to login to http://twitter.com/mytwitterbot
_TWITTERBOTDEV_USER = "autotip" # # The username you use in twitter to login to your "dev" twitter account http://twitter.com/mydevtwitterbot
_TWITTERBOT_PWD = "buttbutt" # I'm lazy, I use the same password for both accounts, you probably shouldn't do this!

## URLS used for Twitter API calls - stored as constants for easy update later.
_TWIT_UPDATE = "https://twitter.com/statuses/update.json"


class ViewScoops(webapp.RequestHandler):

	def get(self):	
		scoops = self.get_scoops()
		template_values = {'scoops': scoops}
		self.response.out.write(template.render('templates/scoops.html', template_values))


	def get_scoops(self):	
		from datastore import Scoop
		scoops = Scoop.gql("WHERE flagged = :1", 0)
		return scoops.fetch(1000)
		

class Zemanta(webapp.RequestHandler):

	def get(self):	
		from zemanta import request
		request()
		return
		
		template_values = {'scoops': self.get_scoops()}
		self.response.out.write(template.render('templates/teaser.html', template_values))



      
      
