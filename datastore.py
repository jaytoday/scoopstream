from google.appengine.ext import db


"""

Models are defined in this module. 

"""


class TwitterUser(db.Model): 
    id = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    pledge = db.IntegerProperty()

class EmailUpdate(db.Model): 
  email_address = db.EmailProperty(required=True)

  
