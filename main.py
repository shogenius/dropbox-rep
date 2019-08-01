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
from visualise import Visualise
from changedir import ChangeDir


JINJA2_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)

class MainPage(webapp2.RequestHandler):

    # This function takes in an email and returns the name stripped from the email
    def getName(self, email):
        name = email.split('@')[0]
        return name

    #this method loops through the blob collection and looks for the
    #blobs that have the same key as the current parent (current location on the application)
    #and returns those.
    def getCurrentFiles(self, blob_collection, currentParentKey):
        currentFiles = []
        for blob in blob_collection.blobs:
            if blob.parentKeyCopy == currentParentKey:
                currentFiles.append(blob)
        return currentFiles

    #This function takes in key in the string format and returns the number of components it contains
    #What I mean by components is each element followed by a comma
    def getNumberOfKeys(self, key_string):
        keyList = key_string.split(",")
        return len(keyList)

    #This function generates the root folder
    def initDB(self, parent):
        #creating the root folder
        #the number of elements is calculated like the following:
        #   MyUser, username, Folder, folder_id
        #     1   +    1   +    1  +     1           = 4
        #the root has no parent!
        folder1 = Folder(id = "root", parent = parent, name = "/", numberOfElements = 4)
        #confirming the adding of the folder
        folder1.put()
        #addint the blob collection and liking it to the user key which
        #is here represented by the parent variable
        collection = BlobCollection(id = parent.id())
        #confirming the adding of the collection
        collection.put()

    def get(self):
        #setting up variables to be used later
        url = ''
        url_string = ''
        welcome = 'Welcome back'
        #getting the connected user
        user = users.get_current_user()
        #setting up the type or response header as html as we
        #are going to be displaying html templates.
        self.response.headers['Content-Type'] = 'text/html'
        #if a user is connceted do the following
        if user:
            #create a logout link
            url = users.create_logout_url(self.request.uri)
            #logout string
            url_string = 'logout'
            #making an ndb key of model MyUser
            myuser_key = ndb.Key('MyUser', self.getName(user.email()))
            #getting the key's entity from the ndb
            myuser = myuser_key.get()
            #if the entity returned is null do the following
            if myuser == None:
                #create a first time welcome string
                welcome = 'Welcome to the application'
                #creating the myuser object to save it in the
                #ndb as an already connected user
                myuser = MyUser(id=self.getName(user.email()))
                #putting the myuser object in the ndb
                myuser.put()
                #this adds the root folder to the ndb
                self.initDB(myuser.key)
                #as this scenario only happens when the user is first connected
                #it's a good time to add the root directory to the ndb

            #creating an ndb key of the root folder in order to query it for the firt set of folders
            entity_key = ndb.Key('MyUser', str(myuser.key.id()) , 'Folder', 'root')
            #querying for the folders that have the same number of key elements (this is explained at a later stage and further more in the documentation)
            #I am also using an ancestor query in order to get the correct folders belonging to the connected user
            currentFolders = Folder.query(Folder.numberOfElements == entity_key.get().numberOfElements + 2, ancestor = entity_key).fetch()
            #setting the currently open folder's name to display in the template
            currentLocation = entity_key.get().name
            #making a key for collection of blobs appropriate to the connected user
            collection_key = ndb.Key('BlobCollection', myuser_key.id())
            #getting the collection
            collection = collection_key.get()
            #getting the files that are present on the root
            currentFiles = self.getCurrentFiles(collection, entity_key)
            #setting up the template values
            template_values = {
                'url' : url,
                'url_string' : url_string,
                'user' : user,
                'currentFolders' : currentFolders,
                'currentLocation' : currentLocation,
                'currentLocation_key': entity_key,
                'welcome' : welcome,
                'collection' : currentFiles,
                'upload_url' : blobstore.create_upload_url('/upload')
            }

            template = JINJA2_ENVIRONMENT.get_template('main.html')
            self.response.write(template.render(template_values))
        #in the case no user is connected
        else:
            #create a login url
            url = users.create_login_url(self.request.uri)
            #create a login string
            url_string = 'login'
            #setting up the template values
            template_values = {
            'url' : url,
            'url_string' : url_string,
            'user' : user,
            'welcome' : welcome
            }

            template = JINJA2_ENVIRONMENT.get_template('main.html')
            self.response.write(template.render(template_values))

    def post(self):
        #setting up the type or response header as html as we
        #are going to be displaying html templates.
        self.response.headers['Content-Type'] = 'text/html'
        #setting up variables to be used later
        url = ''
        url_string = ''
        welcome = 'Welcome back'
        currentParent_key = ''
        currentFiles = ''
        currentFolders = ''
        currentLocation = ''
        currentLocation_key = ''
        alert = ''
        #getting the connected user
        user = users.get_current_user()
        #create a logout link as a user must be connected to access featured buttons
        url = users.create_logout_url(self.request.uri)
        #logout string
        url_string = 'logout'
        #creating a myuser key
        myuser_key = ndb.Key('MyUser', self.getName(user.email()))
        #using the created key to get the proper entity
        myuser = myuser_key.get()
        #getting input values that have "button" as a name property
        action = self.request.get('button')

        collection_key = ndb.Key('BlobCollection', myuser_key.id())
        collection = collection_key.get()

        #checking if the input received had "add" as a value
        if action == 'add':
            #getting the name input entered by the user
            name = self.request.get('name')
            #getting the currently open folder's key
            currentParent = self.request.get('currentParent')
            #turning the returned result from 'Unicode' type into a proper ndb key
            currentParent_key = eval("ndb."+currentParent)
            #getting the current location's entity
            currentParent = currentParent_key.get()
            #creating a new folder with the current directory as a parent
            new_folder = Folder(id = str(str(currentParent.key.id())+"/"+name), parent = currentParent_key, name = name)
            #putting the folder in the ndb
            new_folder.put()
            #checking the number of elements of the key of the new folder
            numberOfElements = self.getNumberOfKeys(str(new_folder.key.flat()))
            #adding the number of key elements to the new folder
            new_folder.numberOfElements = numberOfElements
            #putting the folder in the ndb
            new_folder.put()
            #querying for the folder that will be displayed under the current directory using the parent as an ancestor
            #the number of elements count is done in order to prevent from displaying all of the current parent directory's subfolders
            #In fact, ancestor queries does not return the immediate child but all the children of a parent directory.
            #so the count is a work around to solve this issue.
            currentFolders = Folder.query(Folder.numberOfElements == currentParent_key.get().numberOfElements + 2, ancestor = currentParent_key).fetch()
            #setting the currently open folder's name to display in the template
            currentLocation = currentParent.name
            #getting the files that are present on the approriate directory
            currentFiles = self.getCurrentFiles(collection, currentParent_key)

        elif action == '==>':
            #getting the selected folder by the user
            targettedFolder = self.request.get('currentFolder')
            #turning the returned result from 'Unicode' type into a proper ndb key
            targettedFolder_key = eval("ndb."+targettedFolder)
            #setting the currently open folder's name to display in the template
            currentLocation = targettedFolder_key.get().name
            #querying for the subfolders of the current folder by setting the selected folder's key as the ancestor and putting the number of elements
            #constraint in order to only get the immediate children
            currentFolders = Folder.query(Folder.numberOfElements == targettedFolder_key.get().numberOfElements + 2, ancestor = targettedFolder_key).fetch()
            #getting the files that are present on the approriate directory
            currentFiles = self.getCurrentFiles(collection, targettedFolder_key)
            #assigning the key to the global variable so it can recognized by the template
            currentParent_key = targettedFolder_key


        elif action == '../':
            #getting the currently open folder's key
            location = self.request.get('currentParent')
            #turning the returned result from 'Unicode' type into a proper ndb key
            location_key = eval("ndb."+location)
            #getting the parent folder of the currently open folder
            parent_key = location_key.parent()
            #querying for the immediate children of the parent folder of the currently open folder
            currentFolders = Folder.query(Folder.numberOfElements == parent_key.get().numberOfElements + 2, ancestor = parent_key).fetch()
            #setting the currently open folder's name to display in the template
            currentLocation = parent_key.get().name
            #getting the files that are present on the approriate directory
            currentFiles = self.getCurrentFiles(collection, parent_key)
            #assigning the keys to the approriate global variables so they can recognized by the template
            currentParent_key = parent_key
            currentLocation_key = location_key


        elif action == 'Delete':
            #getting the index of the file to be deleted
            file_name = self.request.get("file_name")
            for element in enumerate(collection.blobs, start = 0):

                if element[1].filename == file_name:
                    # getting the blob info of that file using the previously retrieved index
                    blobInfo = blobstore.BlobInfo(collection.blobs[element[0]].blobKey)
                    #deleting the blob information
                    blobInfo.delete()
                    #deleting the blob
                    del collection.blobs[element[0]]
                    #confirming the deletion
                    collection.put()
                    break
            #getting the currently open folder's key
            currentParent = self.request.get('currentParent')
            #turning the returned result from 'Unicode' type into a proper ndb key
            currentParent_key = eval("ndb."+currentParent)
            #getting the current location's entity
            currentParent = currentParent_key.get()
            #querying for the immediate children of the parent folder of the currently open folder
            currentFolders = Folder.query(Folder.numberOfElements == currentParent_key.get().numberOfElements + 2, ancestor = currentParent_key).fetch()
            #setting the currently open folder's name to display in the template
            currentLocation = currentParent.name
            #getting the files that are present on the approriate directory
            currentFiles = self.getCurrentFiles(collection, currentParent_key)

        elif action == 'Delete Folder':
            #getting the currently open folder's key
            currentParent = self.request.get('currentParent')
            #getting the key of the folder to be deleted
            folderToDelete = self.request.get('currentFolder')
            #turning the returned result from 'Unicode' type into a proper ndb key
            folderToDelete_key = eval('ndb.'+folderToDelete)
            #getting the folder entity using the previously made key
            folderToDelete_entity = folderToDelete_key.get()
            #querying for the immediate children of the folder to be deleted
            childrenFolders = Folder.query(Folder.numberOfElements == folderToDelete_key.get().numberOfElements + 2, ancestor = folderToDelete_key).fetch()
            #boolean variable used to check if the folder has any files in it
            isEmpty = True
            #checking if the folder has any children
            if (len(childrenFolders) > 0):
                #displaying the message
                alert = "Make sure the folder is empty before trying to delete!"
            #if the folder has no children we have to check for files
            elif(len(childrenFolders) == 0):
                #looping through the collection of files and
                #checking if the folder to be deleted is the parent of any of the files
                for index in enumerate(collection.blobs, start = 0):
                    if collection.blobs[index[0]].parentKeyCopy == folderToDelete_key:
                        isEmpty = False
                        break
                #if the folder has no children files
                if(isEmpty):
                    #the folder is deleted
                    folderToDelete_key.delete()
                #otherwise
                else:
                    #displaying the message
                    alert = "Make sure the folder is empty before trying to delete!"

            #turning the returned result from 'Unicode' type into a proper ndb key
            currentParent_key = eval("ndb."+currentParent)
            #getting the current location's entity
            currentParent = currentParent_key.get()
            #querying for the immediate children of the parent folder of the currently open folder
            currentFolders = Folder.query(Folder.numberOfElements == currentParent_key.get().numberOfElements + 2, ancestor = currentParent_key).fetch()
            #setting the currently open folder's name to display in the template
            currentLocation = currentParent.name
            #getting the files that are present on the approriate directory
            currentFiles = self.getCurrentFiles(collection, currentParent_key)


        elif action == '<< Back':
            #getting the currently open folder's key
            currentParent = self.request.get('currentLocation')
            #turning the returned result from 'Unicode' type into a proper ndb key
            currentParent_key = eval("ndb."+currentParent)
            #getting the current location's entity
            currentParent = currentParent_key.get()
            #querying for the immediate children of the parent folder of the currently open folder
            currentFolders = Folder.query(Folder.numberOfElements == currentParent_key.get().numberOfElements + 2, ancestor = currentParent_key).fetch()
            #setting the currently open folder's name to display in the template
            currentLocation = currentParent.name
            #getting the files that are present on the approriate directory
            currentFiles = self.getCurrentFiles(collection, currentParent_key)

        #setting up the template values
        template_values = {
            'url' : url,
            'url_string' : url_string,
            'user' : user,
            'currentFolders' : currentFolders,
            'currentLocation' : currentLocation,
            'currentLocation_key': currentParent_key,
            'welcome' : welcome,
            'collection' : currentFiles,
            'upload_url' : blobstore.create_upload_url('/upload'),
            'alert' : alert
        }
        template = JINJA2_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
('/', MainPage),
('/upload', UploadHandler),
('/download', DownloadHandler),
('/visualise', Visualise),
('/changedir', ChangeDir)
])
