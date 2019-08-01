from google.appengine.ext import ndb

class Blob(ndb.Model):
    filename = ndb.StringProperty()
    blobKey = ndb.BlobKeyProperty()
    parentKeyCopy = ndb.KeyProperty()
