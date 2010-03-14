from django.utils import simplejson
import utils.utils 
from google.appengine.api import urlfetch
import logging
import urllib
import model
if utils.utils.Debug():
	rails_server = 'localhost:3000'
else:
	rails_server = 'www.stalkbox.com'





def runCallback():
	utils.utils.defer(_runCallback)
	
	

def _runCallback():
	import datetime
	checkins = []
	recent_updates = model.StatusUpdate.all().order('-date').fetch(100)
	these_users = {}
	for update in recent_updates:
		this_user = these_users.get(model.StatusUpdate.user.get_value_for_datastore(update))
		if not this_user:
			this_user = update.user
			these_users[model.StatusUpdate.user.get_value_for_datastore(update)] = this_user
		checkins.append(
		{
		'status_id': update.id,
		'status_update': update.text,
		'location_service': update.location_service,
		'location_id': update.location_id,
		'platform': update.platform,
		'venue_name': update.venue_name,
		'geolat': update.lat,
		'geolon': update.lon,
		'published_at': str(update.date.strftime('%Y/%m/%d %H:%M:%S')),
		'uid': this_user.username,
		'name': this_user.name,
		'profile_image_url': this_user.profile_image_url
		})

	args = {
	'checkins': simplejson.dumps(checkins)
	}            
	args_enc = urllib.urlencode(args)
	logging.info('args for callback: %s' % args_enc)
	urlfetch.fetch('http://' + rails_server + "/checkins/create?checkins", payload=args_enc, method="POST")
	return True
