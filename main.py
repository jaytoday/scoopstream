from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import models

STATUS_COUNT = 100
FLAGS = { 
  'stalkbox': ['4sq.com', 'gowal.la'] 
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
  from utils import twitter
  twitter_api = twitter.Api('yupgrade','trixie')
  statuses = twitter_api.GetUserTimeline(user.username, count=STATUS_COUNT)
  save_statuses = []
  for s in statuses:
    print ""
    print s.__dict__
    for f in FLAGS[user.client]:
      if f in s.text:
        save_statuses.append(s)
  #status_key_name = models.getStatusKeyName(user.username, user.client, s.id)
  
  return save_statuses
  	  



	
def main():
  application = webapp.WSGIApplication([
	('/', IndexHandler),
	('/add_user', AddUserHandler)
	], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
