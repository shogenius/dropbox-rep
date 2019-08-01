from google.appengine.ext import ndb

class Folder(ndb.Model):
    name = ndb.StringProperty()
    numberOfElements = ndb.IntegerProperty()
