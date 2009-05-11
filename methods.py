"""

API Methods

As of March 17 2009, the two implemented API methods are a fuzzy
legislator name search and zip by zip code.

Please register an API key and replace the API_KEY with your new key value. 
Register at http://services.sunlightlabs.com/api/register/

You can get more info about the API methods at 
http://wiki.sunlightlabs.com/Sunlight_API_Documentation


"""
import logging
from google.appengine.api import urlfetch
from google.appengine.ext import db
from utils.utils import memoize, task, entity_set, Debug

from datastore import User, Link, RelatedArticle, Scoop

STATUS_COUNT = '30'
DELTA_SECONDS_LIMIT = -20000
MIN_TEXT_LENGTH = 50
FETCH_CACHETIME = 0#2000
CACHETIME = 0#1000
CONTENT_LIMIT = 800


class Tasks():

	def __init__(self): 
	    self.save = []
		
	@task('save_link', shuffle=True)
	def save_link(self, **kwargs): 
	#def save_link(self, this_user, used_url, text, publish_date, *args):
		  # temporarily have to do this
		  if not Debug():
			import sys
			reload(sys)
			sys.setdefaultencoding("utf-8")
		  logging.info('saving link: %s ' % str(kwargs) )
		  this_user = db.get( kwargs.get('this_user') )
		  used_url = kwargs.get('used_url')
		  text = kwargs.get('text')
		  publish_date = kwargs.get('publish_date')
		  platform = kwargs.get('platform')
		  id = kwargs.get('id')

		  link_methods = Links()
		  from google.appengine.api import memcache
		  save_link_list = memcache.get('save_links')
		  # Save Link
		  # Create the link entity, then get the page content and related links
		  link_key_name = link_methods.get_link_key_name(this_user, used_url, platform)
		  # check if link is already saved
		  existing_link = Link.get_by_key_name(link_key_name)
		  if existing_link: 
			  logging.warning('save_link already saved with key_name %s. Going to attempt rerun.' % link_key_name)
			  print "link already exists: ", link_key_name
			  return "rerun"
		  this_page = link_methods.get_page(used_url)
		  if this_page == "fail": 
			  print "unable to fetch and save page: ", used_url
			  logging.warning("unable to fetch and save page: %s" % used_url)
			  return "fail"
		  if this_page == "pass": return True 
		  text = db.Text(text)
		  new_link = Link(key_name = link_key_name,
						  used_url = used_url,
						  url = this_page['location'],
						  content = db.Text(this_page['content']),
						  user = this_user,
						  text = text,
						  id=str(id),
						  publish_date = publish_date)

		  if this_page.get('title', None): new_link.title = this_page['title']
		  else: 
		      new_link.title = this_page['location'][:30]
		      if len(this_page['location']) > 30: new_link.title += "..."
		  self.analyze_link(link=new_link.key())    
		  # or we can put new_link in rotating memcache queue
		  self.save.append(new_link)		  
		  db.put(self.save)
		  logging.info('saved new link: %s' % str(new_link.url) )
		  return self.save
		  


		

	@task('analyze_link')
	def analyze_link(self, **kwargs ): # link object
		link = db.get( kwargs.get('link') )
		import zemanta
		logging.info('analyzing link: %s' % str(link.url) )
		analysis = zemanta.analyze( link.content )
		if not analysis or analysis['status'] == 'fail': 
		    logging.error('unable to get zemanta analysis for link %s' % str(link.url) )
		    return "fail"
		    # THERE HAS TO BE A BETTER WAY - 3 Strike Rule? Differentiate Somehow??? # true or false?
		article_urls = [ db.Link(article['url']) for article in analysis['articles'] ]
		link.related_articles.extend(article_urls)
		for article in analysis['articles']:	    
			this_article = RelatedArticle.get_by_key_name(article['url'])
			if not this_article: # if it doesn't exist, make it
				this_article = RelatedArticle(key_name = article['url'], 
											  url = article['url'],
											  title = article['title']) 
			new_articles = [ db.Link(article['url']) for article in analysis['articles'] ]
			this_article.related_to.append(link.url)
			link.related_articles.append(this_article.url)
			this_article.also_related.extend([ article for article in article_urls if article != this_article.url ] ) # each article should be included once	    
			if analysis.get('title', None): 
			    link.title = analysis.get('title')
			if len(this_article.related_to) > 1 : 
				link_methods = Links()
				self.save.extend( link_methods.add_link_relationships(this_article, link ) )	    
			self.save.append(this_article.clean())
		self.save.append(link.clean())	
		self.save = entity_set(self.save)
		db.put( self.save)		
		logging.info('saved analyzed link: %s' % str(link.__dict__) )
		return self.save	
		
		# What about analysis['keywords'], etc?
		

	@task('twitter_user_refresh')
	def twitter_user_refresh(self, **kwargs ): # link object
		this_user = db.get( kwargs['user'] )
		links = Links()
		print links.twitter_retrieve(this_user)
		return True


	def twitter_user_backup(self): # link object
		users = User.all().fetch(1000)
		for this_user in users:
			self.twitter_user_refresh(user=this_user.key())
		from utils.utils import run_task
		return run_task('twitter_user_refresh')

"""
	@task('twitter_news_refresh')
	def twitter_news_refresh(self, **kwargs ): # link object
		this_news_source = db.get( kwargs['news_source'] )
		links = Links()
		print links.twitter_retrieve(this_news_source)
		return True
		
	def twitter_news_backup(self): # link object
		news_sources = NewsSource.all().fetch(1000)
		for this_news_source in news_sources:
			self.twitter_news_refresh(news_source=this_news_source.key())
		from utils.utils import run_task
		return run_task('twitter_news_refresh')
"""



class Links():

  def __init__(self): 
     self.save = [] 


  	    

  def twitter_retrieve(self, this_user, platform="twitter", test=False):
        link_count = []
        from utils import twitter
        api = twitter.Api() # username, password    
        statuses = self.get_twitter_statuses(this_user.twitter_username, api) 
        if test is not False: statuses = self.get_test_statuses(test)
        if not statuses:
        	logging.warning('twitter API appears to be down...')
        	return False
        	#statuses = self.get_test_statuses() #return "getUserTimeline not working - twitter may be down"
        import datetime, re
        user_object = getattr(statuses[0], 'user', None)
        if user_object: this_user = self.update_user(this_user, user_object)
        http_pattern = re.compile("http([/.a-zA-Z0-9///:_-]*)[a-zA-Z0-9_-]\.[a-zA-Z0-9///_-][/.a-zA-Z0-9///_-]([/.?&=a-zA-Z0-9///_-]*)")
        www_pattern = re.compile("www([/.a-zA-Z0-9///:_-]*)[a-zA-Z0-9_-]\.[a-zA-Z0-9///_-][/.a-zA-Z0-9///_-]([/.?&=a-zA-Z0-9///_-]*)")
        for status in statuses:
            status.date = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            httpmatch = http_pattern.search(status.text)
            if not httpmatch: 
                wwwmatch = www_pattern.search(status.text)
                if not wwwmatch: continue # no links found
                status.link = "http://" + wwwmatch.group().strip()# create real date object from status['created_at']                     
            else: status.link = httpmatch.group().strip()         
            if 'nytimes.com/' in status.link: return False # FOR NOW.
            tasks = Tasks()
            print ""
            print status.link
            save_this_link = tasks.save_link(this_user=this_user.key(), used_url=status.link, text= status.text, 
                                        publish_date=status.date, platform=platform, id=status.id)
            if not save_this_link: print "cannot save this link!"
            if save_this_link is not False: link_count.append(status.link)                            
            
        logging.info("found %s new links from %s updates for user %s on %s platform - %s" % (str(len(link_count)), str(len(statuses)), this_user.name, platform, str(link_count) ))
        return link_count


  def update_user(self, this_user, user_object):
	print ""
	print user_object
	if getattr(user_object, 'name', None) and not this_user.name: this_user.name = user_object.name
	#if user_object.description and not this_user.description:
	# screen_name is twitter_username 
	if getattr(user_object, 'location', None): this_user.location = user_object.location
	if getattr(user_object, 'profile_image_url', None): this_user.profile_image_url = user_object.profile_image_url
	if getattr(user_object, 'followers_count', None): this_user.followers_count = user_object.followers_count
	logging.info('saving profile updates for user %s' % str(this_user.__dict__) )
	db.put(this_user)
	return this_user
  
  	
#  @memoize('test_statuses', FETCH_CACHETIME) # um 20 minutes?
  def get_test_statuses(self, test_name):
        class Status(object): pass
        data = open("data/" + test_name + ".json")
        status_data = eval( data.read() )
        statuses = []
        for status in status_data:
            status_obj = Status()
            status_obj.created_at = status['created_at']
            status_obj.user = Status()
            status_obj.user.name = status['user']['name']
            status_obj.user.location = status['user']['location']
            status_obj.user.profile_image_url = status['user']['profile_image_url']
            #status_obj.user.followers_count = status['user']['followers_count']
            status_obj.text = status['text']
            status_obj.id = status['id']
            statuses.append(status_obj)
        return statuses
        
#  @memoize('statuses', FETCH_CACHETIME) # um 20 minutes?
  def get_twitter_statuses(self, this_user, api):
        try: data = api.GetUserTimeline(this_user, count=STATUS_COUNT)
        except: return False
        return data
        

#  @memoize('get_page', FETCH_CACHETIME)
  def get_page(self, used_url):
	# fetch the page and get header/redirect info
	page = {}
	from google.appengine.api import urlfetch
	try: 
	    fetch_page = urlfetch.fetch(used_url, follow_redirects=False)
	    logging.info("url %s returned status code %s" % (used_url, fetch_page.status_code))
	    if fetch_page.status_code > 399: 
	        logging.warning("url %s returned error status code %s" % (used_url, fetch_page.status_code))
	        return False
	    if 299 < fetch_page.status_code < 303: 
	        page['location'] = fetch_page.headers.get('location')
	        if not page['location']:
	            logging.info("url %s error --  redirect status and no location in header" % (used_url))
	            return False
	        logging.info('fetching redirected page %s' % page['location'])
	        fetch_page = urlfetch.fetch(page['location'], follow_redirects=True)
	        
	    else: page['location'] = used_url # status code 200
	    page['title'], page['content'] = self.extract_content(fetch_page.content)   
	    logging.info('content extracted from %s -- title: %s content: %s'  % (page['location'], page['title'], page['content']) )# divs also?  
	   # if len(page['content']) < 10: return "pass"
	    	    
 	except:  
 	    return "fail"
 	    logging.error('unable to fetch url %s' % used_url) # anything else?
 	    return False
	return page
	
	

#  @memoize('extract_content', CACHETIME)
  def extract_content(self, html_doc):
    from utils.BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(html_doc)
    import re
    codes = re.compile( '&.{1,6};' )
    try: 
        title = soup.html.head.title.contents[0].encode("latin1").decode('utf-8')
        title = codes.sub('', title).replace("\n","")
    except: title = None
    if title: content = title
    else: content = ""
    content_nodes = []
    content_nodes.extend( soup.html.body.findAll('h1') )
    content_nodes.extend( soup.html.body.findAll('p')[:10] )
    # Um just the paragraphs 
    for node in content_nodes:
		  try: this_text = node.findAll(text=True)[0].encode("latin1").decode('utf-8') 
		  except: continue
		  if len(this_text) > MIN_TEXT_LENGTH: content += " " + this_text
    
    content = codes.sub('', content[:CONTENT_LIMIT])	
    
    return title, content


	

  def add_link_relationships(self, shared_article, source_link):     	
	save = []
	logging.info('this article is related to %s links' % str(len(shared_article.related_to)) )
	for link_url in shared_article.related_to: 
	    matching_links = Link.gql("WHERE url = :1", link_url).fetch(1000)
	    if len(matching_links) == 0:
	        logging.warning('cannot find links for article: %s' % shared_article.url)
	        continue
	    for this_link in matching_links: #  	     
				# save key, value pairs to each link for each article-link combo 				
				if this_link.user.key() == source_link.user.key(): continue							
				source_link.add_relationship( this_link, shared_article )
				# this_link.add_relationship( source_link.key, shared_article )
				save.append(source_link.clean())	    
	logging.info('added %s link relationships for article %s' % (str(len(save)), shared_article.url))
	return entity_set(save)

  
  
  # Utils
  
  def get_link_key_name(self, this_user, url, platform):
      return this_user.name + "_" + url + "_" + platform
  
  

class Scoops():
  
  
  def find_scoops(self, this_user):
    """
    
    Find Instances of Scoops by Analyzing Link Relationships
    
    """
    self.save_scoops = []
    # Analyze link patterns compared to media outlets 
    print "finding scoops"
    print this_user.links.fetch(1000)
    for user_link in this_user.links.fetch(1000): 

      if user_link.been_scooped > 1 or user_link.has_scooped > 0: continue # TODO   
      relationships = user_link.get_relationships()
      print ""
      print relationships
      for link_key, article_urls in relationships.items():
      	
			  this_other_link = db.get(link_key)
			  
			  if this_other_link.user.key() == this_user.key(): 
			      logging.error('inappropriate relationship')
			      continue
			      
			  if this_other_link.been_scooped > 1 or this_other_link.has_scooped > 0: continue # TODO   
			  
			  if not this_other_link.is_news_source(): 
			      logging.info(' url %s by user %s matched url by non-news user %s' % (str(user_link.user.name), str(this_other_link.url), str(this_other_link.user.name) ) )
			  # A news link and the user link
			  # map out a list of time deltas between link and each news story, and then rank and cutoff

			  time_delta = user_link.publish_date - this_other_link.publish_date 
			  logging.info(time_delta)
			  # convert to seconds and manually make negative

			  if str(time_delta).startswith('-'): 
			      scooper = this_user
			      scooped = this_other_link.user
			      scooper_link = user_link		  
			      scooped_link = this_other_link	 
			  else: 
			      scooper = this_other_link.user
			      scooped = this_user
			      scooper_link = this_other_link
			      scooped_link = user_link 
			      
			  #if time_delta < DELTA_SECONDS_LIMIT: continue 
					 
			  scoop_key_name = self.get_scoop_key_name(this_user.name, this_other_link.user.name, user_link.url)
			  existing_scoop = Scoop.get_by_key_name(scoop_key_name)
			  if existing_scoop: continue
			  new_scoop = Scoop(key_name = scoop_key_name, 
			                    time_delta = int(time_delta.seconds), 
								scooper = scooper,
								scooped = scooped,
								scooper_link = scooper_link,
								# related articles (all of the articles from both links, with shared ones up top)
								scooped_link = scooped_link
								)
			  logging.info('saving new scoop: %s' % new_scoop.__dict__ )
			  # Only the matched articles
			  new_scoop.matched_articles.extend([ db.Link(article) for article in article_urls ])
			  new_scoop.matched_count = len( new_scoop.matched_articles )
			  # All related articles
			  new_scoop.related_articles.extend([ db.Link(article) for article in article_urls ])
			  new_scoop.related_articles.extend( user_link.related_articles )
			  new_scoop.related_articles.extend( this_other_link.related_articles )
			  scooper_link.has_scooped += 1
			  scooped_link.been_scooped += 1
			  self.save_scoops.extend([ new_scoop.clean(), scooper_link, scooped_link ])

    db.put(entity_set( self.save_scoops ) )
    print "found " + str(len(self.save_scoops)) + " scoops"




  def get_scoop_key_name(self, scooper_name, scooped_name, link):
      return scooper_name + "_" + scooped_name + "_" + link




  def flag(self, scoop_key):
  	this_scoop = Scoop.get_by_key_name(scoop_key)
  	this_scoop.flagged += 1
  	db.put(this_scoop)
  	return
