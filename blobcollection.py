from google.appengine.ext import ndb
from blob import Blob

class BlobCollection(ndb.Model):
    blobs = ndb.StructuredProperty(Blob, repeated = True)
