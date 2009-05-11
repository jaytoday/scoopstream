import logging
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
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
		scoops = db.Query(Scoop).filter('flagged =', 0).filter('matched_count >', 1).order('-matched_count').order('-date') #.order(-matched_count')
		return scoops.fetch(50)
		

class Zemanta(webapp.RequestHandler):

	def get(self):	
		from zemanta import request
		request()
		return
		
		template_values = {'scoops': self.get_scoops()}
		self.response.out.write(template.render('templates/teaser.html', template_values))

class Twitter(webapp.RequestHandler):

	def get(self):
		user_name = "jamtoday"	
		template_values = {'user_name': user_name}
		self.response.out.write(template.render('templates/twitter.html', template_values))


	def get_twitter(self):	
		TWITTER_URL = "http://www.twitter.com/" 
		
		import urllib
		#self.request_args = {}
		#self.formatted_args = urllib.urlencode(self.request_args)
		from google.appengine.api import urlfetch
		fetch_page = urlfetch.fetch(  url = TWITTER_URL,
									method = urlfetch.GET) 
		self.response.out.write(fetch_page.content)
		      
      
