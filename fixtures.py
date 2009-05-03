
import logging
from google.appengine.api import urlfetch
from google.appengine.ext import db
from utils.utils import memoize

from datastore import Link, RelatedArticle, User,  Scoop




class Fixtures():


	def wipe(self, users=False):
		links = Link.all().fetch(500)
		db.delete(links)
		articles = RelatedArticle.all().fetch(500)
		db.delete(articles)
		if users: 
		    users = User.all().fetch(500)
		    db.delete(users)
		
		scoops = Scoop.all().fetch(500)
		db.delete(scoops)
		
				
	def load(self):
		pass
		
		
		


	def scoop(self):
		random_user = User.all().get()
		for link in random_user.links[:1]:
			print ""
			print link
			link.singles_night()

		
		
		
