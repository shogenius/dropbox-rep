import webapp2
import jinja2
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from blob import Blob

class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def getName(self, email):
        name = email.split('@')[0]
        return name
    def get(self):
        #getting the connected user
        user = users.get_current_user()
        #creating a myuser key
        myuser_key = ndb.Key('MyUser', self.getName(user.email()))

        file_name = self.request.get("file_name")

        collection_key = ndb.Key('BlobCollection', myuser_key.id())
        collection = collection_key.get()
        for element in enumerate(collection.blobs, start = 0):
            if element[1].filename == file_name:
                self.send_blob(collection.blobs[element[0]].blobKey)
                break
