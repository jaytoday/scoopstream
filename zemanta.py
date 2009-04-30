import logging
import utils.simplejson as simplejson
from google.appengine.api import urlfetch
import urllib


GATEWAY = 'http://api.zemanta.com/services/rest/0.0/'
API_KEY = 'n5wfc2kjavepgz32qpmjp35d'


def analyze(link_text):
	link_text = link_text
	args = {'method': 'zemanta.suggest',
			'api_key': API_KEY,
			'text': link_text,
			'return_categories': 'dmoz',
			'format': 'json'}            

	args_enc = urllib.urlencode(args)
	try: fetch_page = urlfetch.fetch(GATEWAY, payload=args_enc, method="POST")
	except: 
	    print "dude i think zemanta is out" 
	    return False
	output = simplejson.loads(fetch_page.content)
	return output
