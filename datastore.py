from google.appengine.ext import db
from google.appengine.api import datastore_types



"""

Models are defined in this module. 

"""

# Should these be one model type?

class User(db.Model): 
    name = db.StringProperty(required=False)
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    twitter_username = db.StringProperty(required=False)
    location = db.StringProperty(required=False)
    description = db.StringProperty(required=False)
    profile_image_url = db.StringProperty(required=False)
    followers_count = db.IntegerProperty(required=False) #twitter
    statuses_count = db.IntegerProperty(required=False) #twitter
    is_news_source = db.BooleanProperty(default=True)

    def twitter_formatted_name(self): # for views
        if self.name: my_name = self.name
        else: my_name = self.twitter_username
        return "<a href='http://www.twitter.com/" + self.twitter_username + "'>" + my_name + "</a>"

    def profile_image(self): # for views
        return "<img src='" + self.profile_image_url + "'>"


class Link(db.Model): 
    """
    
    An additional requirement for newworthiness could be that at least 
    one or two related articles match news site URLs in a whitelist
    
    """
    date = db.DateTimeProperty(auto_now_add=True)
    publish_date = db.DateTimeProperty()
    modified = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User, collection_name="links", required=False)
    been_scooped = db.IntegerProperty(default=0)
    has_scooped = db.IntegerProperty(default=0)
    url = db.LinkProperty()
    used_url = db.LinkProperty(required=False) # if different than url 
    link_location = db.LinkProperty(required=False) # status update link
    text = db.TextProperty(required=False) # status update text
    id = db.StringProperty(required=False) # deprecated
    title = db.StringProperty(required=False) 
    content = db.TextProperty(required=False)
    related_articles = db.ListProperty(db.Link) # url is key_name of RelatedLink
    relationships = db.TextProperty(default="{}")

    def clean(self): # for views
        self.related_articles = list ( set(self.related_articles) )
        return self

    def formatted_link(self): # for views
        return "<a href='" + self.url + "'>" + self.title + "</a>"

    def tweet_link(self): # for views
        return "http://twitter.com/" + self.user.twitter_username + "/status/" + self.id


        
    def is_news_source(self): # for views
        return self.user.is_news_source
    
    def add_relationship(self, this_link, shared_article): # for views
      	import logging
      	if this_link.user == self.user: logging.error('adding relationship double jeopardy!')
      	link_key = this_link.key()	
      	relationships = eval(self.relationships)
      	try: 
      	    if str(shared_article.url) in relationships[link_key]: return False
      	    else: 
      	        relationships[link_key].append(str(shared_article.url))
      	        logging.info("%s adding relationship with Link %s for shared article %s " % (str(self.url), str(this_link.url), shared_article.url ) )
      	        
      	        
        except KeyError: relationships[link_key] = [ str(shared_article.url) ]
        self.relationships = db.Text(str(relationships))
        db.put(self)   
      	return self

      	
      	
      	# not saving

    def get_relationships(self): # for views
      	relationships = eval(self.relationships)
      	#we might want to convert strings to db.Key() here
      	# map out the links using preferences or popularity
      	return relationships
      	

    def singles_night(self): # for views
      	relationships = eval(self.relationships)
      	from datastore import Link, RelatedArticle
      	article = RelatedArticle.all().get()
      	news_bool = self.is_news_source
      	link = Link.gql("WHERE is_news_source != :1", news_bool).get()
      	relationships[link.url] = article.url
      	self.related_articles.append(article.url)
      	link.related_articles.append(article.url)
      	self.relationships = str(relationships)
      	print self.__dict__
      	db.put([self, link ])      	
      	# map out the links using preferences or popularity
      	
      	

class RelatedArticle(db.Model): 
    # Result of analysis of Link content
    
    # related links from zemanta/evri -- These Can Be Treated As Links If They Are From Good Sources
    # key_name
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    url = db.LinkProperty()
    related_to =  db.ListProperty(db.Link)  
    also_related = db.ListProperty(db.Link) 
    # po
    
    def clean(self): # for views
        self.related_to = list ( set(self.related_to) )
        self.also_related = list ( set(self.also_related) )
        return self

    

class Scoop(db.Model): 
  date = db.DateTimeProperty(auto_now_add=True)
  modified = db.DateTimeProperty(auto_now=True)
  time_delta = db.IntegerProperty() # this might have to be seconds, with dynamic property for relative time
  scooper = db.ReferenceProperty(User, collection_name="scoops")
  scooped = db.ReferenceProperty(User, collection_name="scooped")
  scooped_link = db.ReferenceProperty(Link, collection_name="scooped")
  scooper_link = db.ReferenceProperty(Link, collection_name="scoops")
  related_articles =  db.ListProperty(db.Link)
  matched_articles =  db.ListProperty(db.Link)
  matched_count = db.IntegerProperty()
  flagged = db.IntegerProperty(default=0)

  def clean(self): # for views
        self.related_articles = list ( set(self.related_articles) )
        return self

  def humanized_time_delta(self): # for views
      	return self.time_delta
