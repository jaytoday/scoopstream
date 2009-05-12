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

class TwitterFront(webapp.RequestHandler):

	def get(self):
		print "twitter front"
		return
		path_arg = self.request.path.split('/twitter/')
		if len(path_arg) < 2: return self.twitter_front()
		twitter_user = path_arg[1]
		twitter_info = self.get_twitter_info(twitter_user)	
		template_values = {'user_name': twitter_user, 'twitter_info': twitter_info }
		self.response.out.write(template.render('templates/twitter.html', template_values))


class Twitter(webapp.RequestHandler):

	def get(self):
		path_arg = self.request.path.split('/twitter/')
		if len(path_arg) < 2: return self.twitter_front()
		twitter_user = path_arg[1]
		this_user = self.get_user_from_twitter_name(twitter_user)
		if not this_user: 
		    print "user not in system! We should ajax this shit. "
		    return False
		twitter_info = self.get_twitter_info(this_user)	
		template_values = {'this_user': this_user, 'twitter_info': twitter_info }
		self.response.out.write(template.render('templates/twitter.html', template_values))

	def twitter_front(self):	
		print "Put twitter dashboard here"
		return
		
	def get_twitter_info(self, this_user):
		from datastore import Scoop
		scoops = this_user.scoops.filter('flagged =', 0).filter('matched_count >', 1).order('-matched_count').order('-date')
		topics = []
		for link in this_user.links: topics.extend( link.keywords ) # rank and order by frequency?
		return { "scoops": scoops, "topics": set(topics) }

	def get_user_from_twitter_name(self, twitter_user):	
		from datastore import User
		this_user = User.gql("WHERE twitter_username = :1", twitter_user).get()
		return this_user 


	def get_twitter_page(self):	
		TWITTER_URL = "http://www.twitter.com/" 
		import urllib
		#self.request_args = {}
		#self.formatted_args = urllib.urlencode(self.request_args)
		from google.appengine.api import urlfetch
		fetch_page = urlfetch.fetch(  url = TWITTER_URL,
									method = urlfetch.GET) 
		self.response.out.write(fetch_page.content)


	def get_facebook_page(self, user_id):	
		FACEBOOK_URL = "http://www.facebook.com/profile.php?id=" 
		import urllib
		#self.request_args = {}
		#self.formatted_args = urllib.urlencode(self.request_args)
		from google.appengine.api import urlfetch
		fetch_page = urlfetch.fetch( url = FACEBOOK_URL + user_id,
									method = urlfetch.GET,
									headers = {'User-Agent': "Mozilla/5.0"} ) 
		self.response.out.write(fetch_page.content)		      
      

