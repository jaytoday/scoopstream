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
from utils.utils import memoize, task, entity_set

from datastore import User, NewsSource, Link, RelatedArticle

STATUS_COUNT = '30'
DELTA_SECONDS_LIMIT = -20000
MIN_TEXT_LENGTH = 50
FETCH_CACHETIME = 0#2000
CACHETIME = 0#1000
CONTENT_LIMIT = 800


class Tasks():

	def __init__(self): 
	    self.save = []
		
	@task('save_link')
	def save_link(self, **kwargs): 
	#def save_link(self, this_user, used_url, text, publish_date, *args):
		  # temporarily have to do this
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
		  from datastore import Link
		  # check if link is already saved
		  existing_link = Link.get_by_key_name(link_key_name)
		  if existing_link: 
			  logging.warning('save_link already saved with key_name %s. Going to attempt rerun.' % link_key_name)
			  print "link already exists: ", link_key_name
			  return "rerun"
			  
		  this_page = link_methods.get_page(used_url)
		  if not this_page: 
			  print "unable to fetch and save page: ", used_url
			  return logging.warning("unable to fetch and save page: %s" % used_url)
		  text = db.Text(text)
		  new_link = Link(key_name = link_key_name,
						  used_url = used_url,
						  text = text,
						  publish_date = publish_date)
						  
		  new_link.url = this_page['location'] 
		  new_link.content = db.Text(this_page['content'], encoding='utf-8') # major encoding issues
		  new_link.is_news_source = this_user.is_news_source()
		  if this_user.is_news_source(): new_link.news_source = this_user
		  else: new_link.user = this_user
		  #link location, platform, date

		  if new_link.content: self.analyze_link(link=new_link.key())    
		  # or we can put new_link in rotating memcache queue
		  
		  
		  logging.info('saving new link: %s: ', str(new_link) )
		  if new_link: self.save.append(new_link)		  
		  db.put(self.save)
		  return self.save
		  


		

	@task('analyze_link')
	def analyze_link(self, **kwargs ): # link object
		link = db.get( kwargs.get('link') )
		import zemanta
		logging.info('analyzing link: %s' % str(link.url) )
		analysis = zemanta.analyze( link.content )
		if not analysis or analysis['status'] == 'fail': 
		    logging.error('unable to get zemanta analysis for link %s' % str(link.url) )
		    return False # true or false?
		from datastore import RelatedArticle, Link
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
			if len(this_article.related_to) > 1 : 
				link_methods = Links()
				self.save.extend( link_methods.add_link_relationships(this_article, link ) )	    
			self.save.append(this_article)
		self.save.append(link)	
		self.save = entity_set(self.save)
		for entity in self.save: logging.info('saved entity: %s', str(entity.url) )
		db.put( self.save)		
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




class Links():

  def __init__(self): 
     self.save = [] 
 

  def twitter_retrieve(self, this_user, platform="twitter"):
        link_count = []
        from utils import twitter
        api = twitter.Api() # username, password
        #statuses = self.get_test_statuses()
        statuses = self.get_twitter_statuses(this_user.twitter_username, api) 
        if not statuses:
        	logging.warning('twitter API appears to be down...')
        	return False
        	#statuses = self.get_test_statuses() #return "getUserTimeline not working - twitter may be down"
        logging.info(str(statuses))
        import datetime, re
        http_pattern = re.compile("http([/.a-zA-Z0-9///:_-]*)[a-zA-Z0-9_-]\.[a-zA-Z0-9///_-][/.a-zA-Z0-9///_-]([/.?&=a-zA-Z0-9///_-]*)")
        www_pattern = re.compile("www([/.a-zA-Z0-9///:_-]*)[a-zA-Z0-9_-]\.[a-zA-Z0-9///_-][/.a-zA-Z0-9///_-]([/.?&=a-zA-Z0-9///_-]*)")
        for status in statuses:
            status.date = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            httpmatch = http_pattern.search(status.text)
            if not httpmatch: 
                wwwmatch = www_pattern.search(status.text)
                if not wwwmatch: continue # no links found
                status.link = "http://" + wwwmatch.group.strip()# create real date object from status['created_at']                     
            else: status.link = httpmatch.group().strip()         
            tasks = Tasks()
            print ""
            print status.link
            save_this_link = tasks.save_link(this_user=this_user.key(), used_url=status.link, text= status.text, 
                                        publish_date=status.date, platform=platform, id=status.id)
            if not save_this_link: print "cannot save this link!"
            if save_this_link is not False: link_count.append(status.link)                            
            
        logging.info("found %s new links for %s on %s platform - %s" % (str(len(link_count)), this_user.name, platform, str(link_count) ))
        return link_count


  @memoize('test_statuses', FETCH_CACHETIME) # um 20 minutes?
  def get_test_statuses(self):
        class Status(object): pass
        data = open("data/user_timeline.json")
        status_data = eval( data.read() )
        statuses = []
        for status in status_data:
            status_obj = Status()
            status_obj.created_at = status['created_at']
            status_obj.text = status['text']
            status_obj.id = status['id']
            statuses.append(status_obj)
        return statuses
        
  @memoize('statuses', FETCH_CACHETIME) # um 20 minutes?
  def get_twitter_statuses(self, this_user, api):
        try: data = api.GetUserTimeline(this_user, count=STATUS_COUNT)
        except: return False
        return data
        

  @memoize('get_page', FETCH_CACHETIME)
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
	        logging.info('fetching redirected page')
	        fetch_page = urlfetch.fetch(page['location'], follow_redirects=False)
	        logging.info(fetch_page.__dict__)
	    else: page['location'] = used_url # status code 200
	   
	    page['content'] = self.extract_content(fetch_page.content)   
	    if len(page['content']) < 10: return False
	    logging.info('content extracted from %s:  %s'  % (page['location'], page['content']) )# divs also?  	    
 	except:  
 	    logging.error('unable to fetch url %s' % used_url) # anything else?
 	    return False
	return { "location": page.get('location', None), "content": page.get('content', None) }  
	
	

  @memoize('extract_content', CACHETIME)
  def extract_content(self, html_doc):
    from utils.BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(html_doc)
    content = "".join( [str(node.findAll(text=True)) for node in soup.findAll('p') if len(str(node.findAll(text=True))) > MIN_TEXT_LENGTH] )
    # there may be a problem with this
    return content[:CONTENT_LIMIT]


	

  def add_link_relationships(self, shared_article, source_link):     	
	save = []
	from datastore import RelatedArticle, Link # - global?	
	logging.info('this article is related to %s links' % str(len(shared_article.related_to)) )
	for link_url in shared_article.related_to: 
	    matching_links = Link.gql("WHERE url = :1", link_url).fetch(1000)
	    if len(matching_links) == 0:
	        logging.warning('cannot find links for article: %s' % shared_article.url)
	        continue
	    for this_link in matching_links: #  	    
				if this_link.key() == source_link.key(): continue
				# save key, value pairs to each link for each article-link combo 
				link_key = str(this_link.key())								
				this_link.add_relationship( link_key, shared_article )
				save.append(this_link)
	    
	logging.info('added %s link relationships for article %s' % (str(len(save)), shared_article.url))
	return entity_set(save)

  
  
  # Utils
  
  def get_link_key_name(self, this_user, url, platform):
      return this_user.name + "_" + url + "_" + platform
  
  

class Scoops():
  
  
  def find_scoops(self, this_user):
    print ""
    print this_user

    self.save_scoops = []
    # Analyze link patterns compared to media outlets 
  #  if self.is_news_source: return "cannot analyze news source" 
    from datastore import Link, RelatedArticle, Scoop
    for user_link in this_user.links: 
    
      if user_link.been_scooped > 0: continue # TODO   
      relationships = user_link.get_relationships()
      for link_key, article_urls in relationships.items():
      	
			  this_link = db.get(db.Key(link_key))
			  if not this_link.is_news_source: 
			      logging.info(' url %s by user %s matched url by non-news user %s' % (str(user_link.user.name), str(this_link.url), str(this_link.user.name) ) )
			      return False 
			  news_link = this_link
			  # A news link and the user link
			  # map out a list of time deltas between link and each news story, and then rank and cutoff

			  time_delta = user_link.publish_date - news_link.publish_date
			  # convert to seconds and manually make negative
			  if str(time_delta).startswith('-'): neg = True
			  else: neg = False
			  time_delta = int( time_delta.seconds)
			  if neg: time_delta = 0 - time_delta
			  #if time_delta < DELTA_SECONDS_LIMIT: continue 
					 
			  scoop_key_name = self.get_scoop_key_name(this_user.name, news_link.news_source.name, user_link.url)
			  existing_scoop = Scoop.get_by_key_name(scoop_key_name)
			  if existing_scoop: continue
			  new_scoop = Scoop(key_name = scoop_key_name, 
			                    time_delta = time_delta, 
								user = this_user,
								news_source = news_link.news_source,
								user_link = user_link,
								# related articles (all of the articles from both links, with shared ones up top)
								news_link = news_link
								)
			  logging.info('saving new scoop: %s' % new_scoop.__dict__ )
			  new_scoop.related_articles.extend([ db.Link(article) for article in article_urls ])
			  new_scoop.related_articles.extend( user_link.related_articles )
			  new_scoop.related_articles.extend( news_link.related_articles )
			  self.save_scoops.append(new_scoop)

    db.put(self.save_scoops)
    print "found " + str(len(self.save_scoops)) + " scoops"




  def get_scoop_key_name(self, user_name, news_name, link):
      return user_name + "_" + news_name + "_" + link


