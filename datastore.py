from google.appengine.ext import db


"""

Models are defined in this module. 

"""

# Should these be one model type?

class User(db.Model): 
    name = db.StringProperty(required=False)
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    twitter_username = db.StringProperty(required=False)

    def is_news_source(self): return False
    
class NewsSource(db.Model): 
    name = db.StringProperty(required=False)
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    twitter_username = db.StringProperty(required=False)
    #image

    def is_news_source(self): return True

class Link(db.Model): 
    date = db.DateTimeProperty(auto_now_add=True)
    publish_date = db.DateTimeProperty()
    modified = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User, collection_name="links", required=False)
    news_source = db.ReferenceProperty(NewsSource, collection_name="links", required=False)
    is_news_source = db.BooleanProperty(default=False)
    been_scooped = db.IntegerProperty(default=0)
    url = db.LinkProperty()
    used_url = db.LinkProperty(required=False) # if different than url 
    link_location = db.LinkProperty(required=False) # status update link
    text = db.TextProperty(required=False) # status update text
    story = db.StringProperty(required=False) # deprecated
    content = db.TextProperty(required=False)
    related_articles = db.ListProperty(db.Link) # url is key_name of RelatedLink
    relationships = db.TextProperty(default="{}")

    def add_relationship(self, link_key, shared_article): # for views
      	import logging
      	logging.info("%s adding link relationship for Link with key %s from %s shared article" % (str(self.url), link_key[-5:], shared_article.url ) ) 
      	relationships = eval(self.relationships)
      	try: 
      	    if str(shared_article.url) not in relationships[link_key]: relationships[link_key].append(str(shared_article.url)) 
        except KeyError: relationships[link_key] = [ str(shared_article.url) ]
      	self.relationships = db.Text(str(relationships))
      	db.put(self) # PERFORMANCE, AHH!
      	return self
      	# Relationship is always two ways, right?
      	
      	
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
    related_to =  db.ListProperty(db.Link) #  
    also_related = db.ListProperty(db.Link) # url is key_name of RelatedLink # all of the articles it is mentioned with
    # po
    
    
    

class Scoop(db.Model): 
  date = db.DateTimeProperty(auto_now_add=True)
  modified = db.DateTimeProperty(auto_now=True)
  time_delta = db.IntegerProperty() # this might have to be seconds, with dynamic property for relative time
  user = db.ReferenceProperty(User, collection_name="scoops")
  news_source = db.ReferenceProperty(NewsSource, collection_name="scoops")
  news_link = db.ReferenceProperty(Link, collection_name="scooped")
  user_link = db.ReferenceProperty(Link, collection_name="scoops")
  related_articles =  db.ListProperty(db.Link)

  def humanized_time_delta(self): # for views
      	return self.time_delta
