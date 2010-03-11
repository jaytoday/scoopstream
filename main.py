from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
import models
import re

STATUS_COUNT = 100
FLAGS = { 
  'stalkbox': ['http://4sq.com/', 'http://gowal.la/s/'] 
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
    user_key_name = models.getUserKeyName(client, username)
    # get user from db 
    saved_user = models.ActivityProfile.get_by_key_name(user_key_name)
    if not saved_user:  
      saved_user = models.ActivityProfile(
      key_name=user_key_name, 
      username = username,
      client = client)
      saved_user.put()
    return self.response.out.write(getTwitterUpdates(saved_user))

"""
    if getattr(self.user_object, 'profile_image_url', None): 
        activity_profile.profile_image_url = self.user_object.profile_image_url
"""

def getTwitterUpdates(user):
	save = []
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
	if do_save:
	 save.append(user)
	for s in statuses:
	   for f in FLAGS[user.client]:
	     if f in s.text:
				short_url_pattern = re.compile(f + r'([\d\w]*)')
				short_url_match = short_url_pattern.search(s.text)
				if not short_url_match:
					logging.critical('Found %s but unable to find regex match in user %s text %s '
					% (f, user.key().name(), s.text))
					continue
				short_url = f + short_url_match.groups()[0]
				status_key_name = models.getStatusKeyName(user.username, user.client, str(s.id))
				new_update = models.StatusUpdate(
				key_name = status_key_name,
				short_url = short_url,
				user = user,
				date = s.created_at,
				platform = user.platform,
				text = s.text,
				id = str(s.id))
				save.append(s)
	   db.put(save)
	return save_statuses
	  



	
def main():
  application = webapp.WSGIApplication([
	('/', IndexHandler),
	('/add_user', AddUserHandler)
	], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
