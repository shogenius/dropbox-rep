import webapp2
import jinja2
import os
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.blobstore import BlobInfo
from folder import Folder
from myuser import MyUser
from blobcollection import BlobCollection
from uploadhandler import UploadHandler
from downloadhandler import DownloadHandler
from blob import Blob


JINJA2_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)

class Visualise(webapp2.RequestHandler):
    # This function takes in an email and returns the name stripped from the email
    def getName(self, email):
        name = email.split('@')[0]
        return name

    def get(self):
        #setting up the type or response header as html as we
        #are going to be displaying html templates.
        self.response.headers['Content-Type'] = 'text/html'
        #if a user is connceted do the following
        currentLocation = self.request.get("currentParent")
        currentLocation_key = eval("ndb."+currentLocation)
        #getting the connected user
        user = users.get_current_user()
        myuser_key =ndb.Key("MyUser", self.getName(user.email()))
        collection_key = ndb.Key('BlobCollection', myuser_key.id())
        collection = collection_key.get()

        #setting up the template values
        template_values = {
            'currentLocation_key': currentLocation_key,
            'collection' : collection.blobs
        }

        template = JINJA2_ENVIRONMENT.get_template('visualise.html')
        self.response.write(template.render(template_values))
