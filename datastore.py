from google.appengine.ext import db


"""

Models are defined in this module. 

"""

class User(db.Model): 
    name = db.StringProperty(required=False)
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    twitter_username = db.StringProperty(required=False)

class NewsSource(db.Model): 
    name = db.StringProperty(required=False)
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    twitter_username = db.StringProperty(required=False)
    #image
    

class Link(db.Model): 
    date = db.DateTimeProperty(auto_now_add=True)
    publish_date = db.DateTimeProperty()
    modified = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User, collection_name="links", required=False)
    news_source = db.ReferenceProperty(NewsSource, collection_name="links", required=False)
    is_news_source = db.BooleanProperty(default=False)
    url = db.LinkProperty()
    used_url = db.LinkProperty(required=False) # if different than url 
    link_location = db.LinkProperty(required=False) # status update link
    text = db.TextProperty(required=False)
    story = db.StringProperty(required=False)
    #platform
    

class Scoop(db.Model): 
  date = db.DateTimeProperty(auto_now_add=True)
  modified = db.DateTimeProperty(auto_now=True)
  time_delta = db.IntegerProperty() # this might have to be seconds, with dynamic property for relative time
  user = db.ReferenceProperty(User, collection_name="scoops")
  news_source = db.ReferenceProperty(NewsSource, collection_name="scoops")
  news_link = db.ReferenceProperty(Link, collection_name="scooped")
  user_link = db.ReferenceProperty(Link, collection_name="scoops")