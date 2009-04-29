
import logging
from google.appengine.api import urlfetch
from google.appengine.ext import db
from utils.utils import memoize

from datastore import Link, RelatedArticle, User, NewsSource, Scoop




class Fixtures():


	def wipe(self):
		links = Link.all().fetch(1000)
		db.delete(links)
		articles = RelatedArticle.all().fetch(1000)
		db.delete(articles)
		users = User.all().fetch(1000)
		db.delete(users)
		sources = NewsSource.all().fetch(1000)
		db.delete(sources)
		scoops = Scoop.all().fetch(1000)
		db.delete(scoops)
		
				
	def load(self):
		pass
		
		
		


	def scoop(self):
		random_user = User.all().get()
		for link in random_user.links[:1]:
			print ""
			print link
			link.singles_night()

		
		
		
