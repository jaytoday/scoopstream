from google.appengine.ext import db
#import properties



class ActivityProfile(db.Model): 
		#key_name - app_username
		client = db.StringProperty(default="twitter")
		platform = db.StringProperty(default="twitter")
		profile_image_url = db.StringProperty(required=False)
		username = db.StringProperty(required=False)
		date = db.DateTimeProperty(auto_now_add=True)
		modified = db.DateTimeProperty(auto_now=True)
		#activity = properties.PickledProperty(required=False)


class StatusUpdate(db.Model):
	#key_name - user.key().name()_update-id
	user = db.ReferenceProperty(ActivityProfile)
	date = db.DateTimeProperty(auto_now_add=True)
	text = db.StringProperty() # update text
	id = db.StringProperty()
	saved = db.DateTimeProperty(auto_now_add=True)
	
	
	
def getUserKeyName(client, username):
	return client + "_" + username

def getStatusKeyName(client, username, update_id):
	return client + "_" + username	+ "_" + update_id