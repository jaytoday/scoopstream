from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
import model
import re, datetime

STATUS_COUNT = 100
FLAGS = { 
  'stalkbox': [('foursquare','http://4sq.com/'), 
               ('gowalla', 'http://gowal.la/s/')]
}


class IndexHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('Hello world!')


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
			for update in new_updates:
				GetGeoCoordinates(update)
			return self.response.out.write('OK')


class UpdateRandomUser(webapp.RequestHandler):
  def get(self):
		users = model.ActivityProfile.all().fetch(1000)
		ranked_users = []
		for user in users:
			# TODO: check to see that user wasn't modified too recently 
			for i in range(user.update_count + 1):
				ranked_users.append(user)
			import random
			random_user = random.choice(ranked_users)
			new_updates = getTwitterUpdates(user)
			for update in new_updates:
					GetGeoCoordinates(update)
			
class GetCoordinatesHandler(webapp.RequestHandler):
	# this is just for finishing updates that failed earlier 
	def get(self):
		updates = model.StatusUpdate.order('-date').fetch(1000)
		for update in updates:
			if not update.lat or not update.lon:
				GetGeoCoordinates(update)

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
	   for service, f in FLAGS[user.client]:
	     if f in s.text:
				short_url_pattern = re.compile(f + r'([\d\w]*)')
				short_url_match = short_url_pattern.search(s.text)
				if not short_url_match:
					logging.critical('Found %s but unable to find regex match in user %s text %s '
					% (f, user.key().name(), s.text))
					continue
				location_id = short_url_match.groups()[0]
				status_key_name = model.getStatusKeyName(user.username, user.client, str(s.id))
				saved_update = model.StatusUpdate.get_by_key_name(status_key_name)
				if saved_update:
					continue
				new_update = model.StatusUpdate(
				key_name = status_key_name,
				location_id = location_id,
				user = user,
				date = s.date,
				platform = user.platform,
				service = service,
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
		return getattr(self, status_update.service)()
	
	def gowalla(self):
		from utils.gowalla import gowalla
		gowalla_api = gowalla.Gowalla(username='jamtoday', password='buttbutt', 
		api_key='9208c499bba1404a8bb150afebd4aece')
		get_result = gowalla_api.spots(id=self.status_update.location_id)
		print ""
		print get_result

	def foursquare(self):
		pass
		
		

	
def main():
  application = webapp.WSGIApplication([
	('/', IndexHandler),
	('/add_user', AddUserHandler)
	], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
