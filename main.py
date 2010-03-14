from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import urlfetch, urlfetch_errors
import model
import re, datetime
import logging



STATUS_COUNT = 100
FLAGS = { 
  'stalkbox': [('foursquare','http://4sq.com/', 'http://foursquare.com/venue/'), 
               ('gowalla', 'http://gowal.la/s/', 'http://gowalla.com/spots/')]
}


class IndexHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('''
		<a href="/update_random_user">Update Random User</a>
		<a href="/get_coordinates">Get Coordinates</a>
		<a href="/add_user?client=stalkbox&username=">Add User</a>''')


class AddUserHandler(webapp.RequestHandler):
  def get(self):
    if not self.request.get('client'): 
      return self.response.out.write('client is required')
    client = self.request.get('client')
    if not self.request.get('username'): 
      return self.response.out.write('username is required')
    username = self.request.get('username')
    user_key_name = model.getUserKeyName(client, username)
    # get user from db 
    saved_user = model.ActivityProfile.get_by_key_name(user_key_name)
    if not saved_user:  
			saved_user = model.ActivityProfile(
			key_name=user_key_name, 
			username = username,
			client = client)
			saved_user.put()
			new_updates = getTwitterUpdates(saved_user)
			getCoordinatesForUpdates(new_updates)
			return self.response.out.write('OK')


class UpdateRandomUser(webapp.RequestHandler):
  def get(self):
		import random
		users = model.ActivityProfile.all().fetch(1000)
		"""
		ranked_users = []
		for user in users:
			# TODO: check to see that user wasn't modified too recently 
			for i in range(user.update_count + 1):
				ranked_users.append(user)
		random_user = random.choice(ranked_users)
		"""
		random_user = random.choice(users)
		new_updates = getTwitterUpdates(random_user)
		getCoordinatesForUpdates(new_updates)
			
class GetCoordinatesHandler(webapp.RequestHandler):
	# this is just for finishing updates that failed earlier 
	def get(self):
		updates = model.StatusUpdate.all().order('-date').fetch(1000)
		getCoordinatesForUpdates(updates)
		

def getCoordinatesForUpdates(updates):
	save = []
	for update in updates:
		g = GetGeoCoordinates(update)
		try:
			update = g.get()
		except:
			logging.critical('unable to get GeoCoordinates for update', exc_info=True)	
			continue		
		save.append(update)
	logging.info('Will callback be called? %s' % save)
	if save:
		db.put(save)
		# should callback only be called when there are saved updates?
		from callback import runCallback
		runCallback()

def getTwitterUpdates(user):
	save = []
	new_updates = []
	from utils import twitter
	twitter_api = twitter.Api('yupgrade','trixie') # login
	statuses = twitter_api.GetUserTimeline(user.username, count=STATUS_COUNT)
	if not statuses: return
	do_save = False
	if getattr(statuses[0].user, 'profile_image_url', None):
		if statuses[0].user.profile_image_url != user.profile_image_url:
			user.profile_image_url = statuses[0].user.profile_image_url
			do_save = True
	if getattr(statuses[0].user, 'name', None):
		if statuses[0].user.name != user.name:
			user.name = statuses[0].user.name
			do_save = True
	for s in statuses:
	   for service, short_f, long_f in FLAGS[user.client]:
	     if short_f in s.text:
				short_url_pattern = re.compile(short_f + r'([\d\w]*)')
				short_url_match = short_url_pattern.search(s.text)
				if not short_url_match:
					logging.critical('Found %s but unable to find regex match in user %s text %s '
					% (f, user.key().name(), s.text))
					continue
				short_url = short_f + short_url_match.groups()[0]
				logging.info('short_url is %s' % short_url)
				status_key_name = model.getStatusKeyName(user.username, user.client, str(s.id))
				# check if there is already a saved update
				saved_update = model.StatusUpdate.get_by_key_name(status_key_name)
				if saved_update:
					continue
				try:
					fetched_page = urlfetch.fetch(short_url, follow_redirects=True, 
					headers = {'User-Agent': "Mozilla/5.0"}, deadline=15)
					"""
					if 299 < fetched_page.status_code < 303:
						logging.info('url %s has a double redirect' % fetched_page.headers.get('location'))
						fetched_page = urlfetch.fetch(fetched_page.headers.get('location'), follow_redirects=False, 
						headers = {'User-Agent': "Mozilla/5.0"}, deadline=15)
					"""
				except:# (urlfetch_errors.InvalidURLError, urlfetch_errors.DownloadError, urlfetch_errors.ResponseTooLargeError, UnicodeEncodeError):
					logging.critical('unable to retrieve url %s' % short_url, exc_info=True)
					continue
				long_url = fetched_page.final_url#headers.get('location')
				logging.info('long_url is %s' % long_url)
				if long_f not in long_url:
					logging.warning('flag %s not found in long_url %s' % (long_f, long_url))
					continue
				location_id = long_url.replace(long_f, '')
				new_update = model.StatusUpdate(
				key_name = status_key_name,
				location_id = location_id,
				user = user,
				date = s.date,
				platform = user.platform,
				location_service = service,
				text = s.text,
				id = str(s.id))
				save.append(new_update)
				new_updates.append(new_update)
				user.update_count += 1
				do_save = True
	if do_save:
	 save.append(user)
	db.put(save)
	return new_updates
	  

class GetGeoCoordinates(object):
	def __init__(self, status_update):
		self.status_update = status_update
	
	def get(self):
		getattr(self, self.status_update.location_service)()
		return self.status_update
	
	def gowalla(self):
		from utils.gowalla import gowalla
		gowalla_api = gowalla.Gowalla(username='jamtoday', password='buttbutt', 
		api_key='9208c499bba1404a8bb150afebd4aece')
		result_dict = gowalla_api.spots(id=self.status_update.location_id)
		self.status_update.lon = result_dict['lng']
		self.status_update.lat = result_dict['lat']
		#import random
		#offset = random.choice(range(100))
		#self.status_update.venue_name = result_dict['name'] + str(offset)
		#self.status_update.lon = float(30.2695755256 + offset)
		#self.status_update.lat = float(-97.7495133877 + offset)

	def foursquare(self):
		from utils.foursquare import foursquare
		fs_api = foursquare.Foursquare()
		result_dict = fs_api.venue(self.status_update.location_id)
		self.status_update.lon = result_dict['venue']['geolong']
		self.status_update.lat = result_dict['venue']['geolat']
		self.status_update.venue_name = result_dict['venue']['name']
		
		
		

	
def main():
  application = webapp.WSGIApplication([
	('/', IndexHandler),
	('/add_user', AddUserHandler),
	('/update_random_user', UpdateRandomUser),
	('/get_coordinates', GetCoordinatesHandler)
	
	], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
