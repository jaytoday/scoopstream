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
from utils.utils import memoize


STATUS_COUNT = '10'
DELTA_SECONDS_LIMIT = -20000
MIN_TEXT_LENGTH = 50
FETCH_CACHETIME = 240000
CACHETIME = 18000

class Links():

  def __init__(self, this_user, news_source=False):
      self.this_user = this_user
      self.news_source = news_source
  
  
  def twitter_retrieve(self, platform="twitter"):
        self.save = []
        from utils import twitter
        api = twitter.Api() # username, password
        statuses = self.get_test_statuses()
        #try: statuses = self.get_twitter_statuses(self.this_user.twitter_username, api) 
        #except: statuses = self.get_test_statuses() #return "getUserTimeline not working - twitter may be down"
        import datetime, re
        http_pattern = re.compile("http([/.a-zA-Z0-9///:_-]*)[a-zA-Z0-9_-]\.[a-zA-Z0-9///:_-][/.a-zA-Z0-9///:_-]([/.?&=a-zA-Z0-9///:_-]*)")
        www_pattern = re.compile("www([/.a-zA-Z0-9///:]*)[a-zA-Z0-9]\.[a-zA-Z0-9///:][/.a-zA-Z0-9///:]([/.a-zA-Z0-9///:]*)")
        for status in statuses:
            status.date = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            httpmatch = http_pattern.search(status.text)
            if not httpmatch: 
                wwwmatch = www_pattern.search(status.text)
                if not wwwmatch: continue # no links found
                status.link = "http://" + wwwmatch.group.strip()# create real date object from status['created_at']                     
            else: status.link = httpmatch.group().strip()
            self.save_link(status.link, status.text, status.date, platform=platform, id=status.id)
        self.save = list( set(self.save) )
        #db.put(self.save)
        return
        for item in self.save:
            try: 
                db.put(item)
                print "was able to save " + str(item.__dict__)
            except: print "cannot save " + str(item.__dict__)
        return "found " + str(len(self.save)) + " new links"


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
        
#  @memoize('statuses', FETCH_CACHETIME) # um 20 minutes?
  def get_twitter_statuses(self, user, api):
        data = api.GetUserTimeline(user, count=STATUS_COUNT)
        return data
        

  def save_link(self, used_url, text, publish_date, platform=None, id=None):
      link_key_name = self.get_link_key_name(used_url, platform)
      from datastore import Link
      existing_link = Link.get_by_key_name(link_key_name)
      if existing_link: 
          logging.warning('save_link already saved with key_name %s' % link_key_name)
          print "link already exists"
          return "link already exists"
      this_page = self.get_page(used_url)
      if not this_page: return logging.warning("not saving page!")
      text = db.Text(text)
      new_link = Link(key_name = link_key_name,
                      used_url = used_url,
                      text = text,
                      publish_date = publish_date)
      if this_page['location'] != "error": new_link.url = this_page['location'] 
      else: new_link.url = used_url
      if this_page['content'] != "error": new_link.content = db.Text(this_page['content']) 
      
      new_link.is_news_source = self.news_source
      if self.news_source: new_link.news_source = self.this_user
      else: new_link.user = self.this_user
      #link location, platform, date

      if new_link.content: self.analyze_link(new_link)    
      logging.info('saving new link: %s: ', str(new_link.url) )
      if new_link: self.save.append(new_link)

#  @memoize('get_page', FETCH_CACHETIME)
  def get_page(self, used_url):
	page = {}
	from google.appengine.api import urlfetch
	print "getting page"
	if True: 
	    fetch_page = urlfetch.fetch(used_url, follow_redirects=False)
	    logging.info("url %s returned status code %s" % (used_url, fetch_page.status_code))
	    if fetch_page.status_code > 399: 
	        logging.warning("url %s returned error status code %s" % (used_url, fetch_page.status_code))
	        return False
	    if 299 < fetch_page.status_code < 303: 
	        page['location'] = fetch_page.headers.get('location')
	        if not page['location']:
	            logging.info("url %s returned error no location in header" % (used_url))
	            return False
	        logging.info('fetching redirected page')
	        fetch_page = urlfetch.fetch(page['location'], follow_redirects=True)
	    else: page['location'] = used_url # status code 200
	   
	    page['content'] = self.extract_content(fetch_page.content)   
	    logging.info('content extracted from %s:  %s'  % (page['location'], page['content']) )# divs also?  
	    
 #	except:  logging.error('unable to fetch url %s' % used_url) # anything else?
	return { "location": page.get('location', None), "content": page.get('content', None) }  
	
	

#  @memoize('extract_content', CACHETIME)
  def extract_content(self, html_doc):
    from utils.BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(html_doc)
    content = "".join( [str(node.findAll(text=True)[0]) for node in soup.findAll('p') if len(str(node)) > MIN_TEXT_LENGTH] )
    # there may be a problem with this
    return content


  @memoize('analyze_link', FETCH_CACHETIME)
  def analyze_link(self, link): # link object
	#db.put(self.save) # need to be saved
	save = []
	import zemanta
	analysis = zemanta.analyze( link.content )
	if not analysis: return False
	from datastore import RelatedArticle, Link
	for article in analysis['articles']:
	    
	    this_article = RelatedArticle.get_by_key_name(article['url'])
	    if not this_article: 
	        this_article = RelatedArticle(key_name = article['url'], 
	                                      url = article['url'],
	                                      title = article['title']) 
	    new_articles = [ db.Link(article['url']) for article in analysis['articles'] ]
	    try: this_article.also_related.extend(new_articles) # each article should be included once
	    except: this_article.also_related = new_articles
	    if len(this_article.related_to) > 1 : save.extend( self.add_link_relationships(this_article) )
	    
	    if this_article: save.append(this_article)	
	
	# What about analysis['keywords'], etc?
	
	 
	self.save.extend( save ) 
	

  def add_link_relationships(self, shared_article):     
	save = []
	from datastore import RelatedArticle, Link # - global?
	these_links = []	
	for link_url in shared_article.related_to: 
	    this_link = Link.get_by_key_name(link_url)
	    if not this_link:
	        logging.warning('link doesnt exist')
	        continue
	    these_links.append(this_link)	    
	    # save key, value pairs to each link for each article-link combo 
	    for link_url in shared_article.related_to: this_link.add_relationship( link_url, shared_article )
	    save.append(this_link)	
	return save

  
  
  # Utils
  
  def get_link_key_name(self, url, platform):
      return self.this_user.name + "_" + url + "_" + platform
  
  
  
  
  def find_scoops(self):
    self.save_scoops = []
    # Analyze link patterns compared to media outlets 
    if self.news_source: return "cannot analyze news source" 
    from datastore import Link
    for user_link in self.this_user.links: 
      news_stories = Link.gql("WHERE story = :1 AND is_news_source = True", user_link.story).fetch(1000)
      # map out a list of time deltas between link and each news story, and then rank and cutoff
      from datastore import Scoop 
      for story in news_stories:
          time_delta = user_link.publish_date - story.publish_date
          # convert to seconds and manually make negative
          if str(time_delta).startswith('-'): neg = True
          else: neg = False
          time_delta = int( time_delta.seconds)
          if neg: time_delta = 0 - time_delta
          if time_delta < DELTA_SECONDS_LIMIT: continue 
                 
          new_scoop = Scoop(time_delta = time_delta, 
                            user = self.this_user,
                            news_source = story.news_source,
                            user_link = user_link,
                            news_link = story
                            )
          self.save_scoops.append(new_scoop)
    db.put(self.save_scoops)
    print "found " + str(len(self.save_scoops)) + " scoops"




def get_scoops(User, news_source=False):
    pass


