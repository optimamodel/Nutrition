"""
main.py -- main code for Sciris users to change to create their web apps
    
Last update: 3/23/18 (gchadder3)
"""

#
# Imports (Block 1)
#

from flask import request, current_app, json, jsonify, send_from_directory
from flask_login import current_user
from werkzeug.utils import secure_filename
import numpy as np
import mpld3
import sys
import os
import sciris
import sciris.scirisobjects as sobj
import sciris.datastore as ds
import sciris.user as user
import sciris.project as project
import hptool
from hptool.webapp import config
from hptool import uuid, dcp, Burden, Interventions


#
# Script code (Block 1)
#

# Get the full path for the loaded sciris repo.  (It in sys path at the 
# beginning because the caller puts it there.)
scirisRepoFullPath = os.path.dirname(sciris.__file__)

# If we have a full path for the model directory, load scirismain.py from that.
if os.path.isabs(config.MODEL_DIR):
    modelDirTarget = config.MODEL_DIR
    
# Otherwise (we have a relative path), use it (correcting so it is with 
# respect to the sciris repo directory).
else:
    modelDirTarget = '%s%s%s' % (os.pardir, os.sep, config.MODEL_DIR) 
    
# If we have a full path for the webapp directory, load scirismain.py from that.
if os.path.isabs(config.WEBAPP_DIR):
    webappDirTarget = config.WEBAPP_DIR
    
# Otherwise (we have a relative path), use it (correcting so it is with 
# respect to the sciris repo directory).
else:
    webappDirTarget = '%s%s%s' % (os.pardir, os.sep, config.WEBAPP_DIR) 
    
#
# Imports (Block 2, dependent on config file)
#  
    
# Append the model directory to the path and import needed files.    
sys.path.append(modelDirTarget)


# Append the webapp directory to the path and import needed files.    
sys.path.append(webappDirTarget)

#
# Classes
#

class ProjectSO(sobj.ScirisObject):
    """
    A ScirisObject-wrapped hptool Project object.
    
    Methods:
        __init__(theProject: Project, ownerUID: UUID, theUID: UUID [None]): 
            void -- constructor
        loadFromCopy(otherObject): void -- assuming otherObject is another 
            object of our type, copy its contents to us (calls the 
            ScirisObject superclass version of this method also)   
        show(): void -- print the contents of the object
        getUserFrontEndRepr(): dict -- get a JSON-friendly dictionary 
            representation of the object state the front-end uses for non-
            admin purposes  
        saveAsFile(loadDir: str): str -- given a load dictionary, save the 
            project in a file there and return the file name
                    
    Attributes:
        theProject (Project) -- the actual Project object being wrapped
        ownerUID (UUID) -- the UID of the User that owns the Project
        
    Usage:
        >>> myProject = ProjectSO(theProject,uuid.UUID('12345678123456781234567812345678'))                      
    """
    
    def  __init__(self, theProject, ownerUID, theUID=None):
        # NOTE: theUID argument is ignored but kept here to not mess up
        # inheritance.
        
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        validUID = sobj.getValidUUID(ownerUID)
        
        # If we have a valid UUID...
        if validUID is not None:       
            # Set superclass parameters (passing in the actual Project's UID).
            super(ProjectSO, self).__init__(theProject.uid)
                   
            # Set the project to the Sciris Project that is passed in.
            self.theProject = theProject
            
            # Set the owner (User) UID.
            self.ownerUID = validUID
        
    def loadFromCopy(self, otherObject):
        if type(otherObject) == type(self):
            # Do the superclass copying.
            super(ProjectSO, self).loadFromCopy(otherObject)
            
            # Copy the Project object itself.
            self.theProject = dcp(otherObject.theProject)
            
            # Copy the owner UID.
            self.ownerUID = otherObject.ownerUID
              
    def show(self):
        # Show superclass attributes.
        super(ProjectSO, self).show()  
        
        # Show the Optima defined display text for the project.
        print '---------------------'
        print 'Owner User UID: %s' % self.ownerUID.hex
        print 'Project Name: %s' % self.theProject.name
        print 'Creation Time: %s' % self.theProject.created
        print 'Update Time: %s' % self.theProject.modified
        print 'Data Upload Time: %s' % self.theProject.spreadsheetdate
        
    def getUserFrontEndRepr(self):
        objInfo = {
            'project': {
                'id': self.uid,
                'name': self.theProject.name,
                'userId': self.ownerUID,
                'creationTime': self.theProject.created,
                'updatedTime': self.theProject.modified,
                'dataUploadTime': self.theProject.spreadsheetdate
            }
        }
        return objInfo
    
    def saveAsFile(self, loadDir):
        # Use the uploads directory to put the file in.
        dirname = ds.uploadsPath
    
        # Create a filename containing the project name followed by a .prj 
        # suffix.
        fileName = '%s.prj' % self.theProject.name
        
        # Generate the full file name with path.
        fullFileName = '%s%s%s' % (dirname, os.sep, fileName)   
     
        # Write the object to a Gzip string pickle file.
        ds.objectToGzipStringPickleFile(fullFileName, self.theProject)
        
        # Return the filename (not the full one).
        return self.theProject.name + ".prj"
    
# newer (more complicated) version...
#class ProjectSO(sobj.ScirisObject):
#    """
#    A Sciris project.
#    
#    Methods:
#        __init__(name: str, ownerUID: UUID, theUID: UUID [None], 
#            spreadsheetPath: str [None]): void -- constructor            
#        updateName(newName: str): void -- change the project name to newName
#        updateSpreadsheet(spreadsheetPath: str): void -- change the 
#            spreadsheet the project is using
#            
#        saveToPrjFile(dirPath: str, saveResults: bool [False]) -- save the 
#            project to a .prj file and return the full path
#            
#        loadFromCopy(otherObject): void -- assuming otherObject is another 
#            object of our type, copy its contents to us (calls the 
#            ScirisObject superclass version of this method also)             
#        show(): void -- print the contents of the object
#        getUserFrontEndRepr(): dict -- get a JSON-friendly dictionary 
#            representation of the object state the front-end uses for non-
#            admin purposes 
#            
#        saveAsFile(loadDir: str): str -- given a load dictionary, save the 
#            project in a file there and return the file name
#            
#    Attributes:
#        theProject (Project) -- the actual Project object being wrapped
#        uid (UUID) -- the UID of the Project
#        ownerUID (UUID) -- the UID of the User that owns the Project        
#        name (str) -- the Project's name
#        spreadsheetPath (str) -- the full path name for the Excel spreadsheet
#        createdTime (datetime.datetime) -- the time that the Project was 
#            created
#        updatedTime (datetime.datetime) -- the time that the Project was last 
#            updated
#        dataUploadTime (datetime.datetime) -- the time that the Project's 
#            spreadsheet was last updated
#        
#    Usage:
#        >>> theProj = Project('myproject', uuid.UUID('12345678123456781234567812345672'), uuid.UUID('12345678123456781234567812345678'))                    
#    """ 
#    
#    def  __init__(self, name, ownerUID, theUID=None, spreadsheetPath=None):
#        # Make sure owner has a valid UUID, converting a hex text to a
#        # UUID object, if needed.        
#        validOwnerUID = sobj.getValidUUID(ownerUID)
#        
#        # If we have a valid UUID...
#        if validOwnerUID is not None:  
#            # Set the owner (User) UID.
#            self.ownerUID = validOwnerUID
#                       
#            # If a UUID was passed in...
#            if theUID is not None:
#                # Make sure the argument is a valid UUID, converting a hex text to a
#                # UUID object, if needed.        
#                validUID = sobj.getValidUUID(theUID) 
#                
#                # If a validUID was found, use it.
#                if validUID is not None:
#                    self.uid = validUID
#                # Otherwise, generate a new random UUID using uuid4().
#                else:
#                    self.uid = uuid()
#            # Otherwise, generate a new random UUID using uuid4().
#            else:
#                self.uid = uuid()
#                
#            # Set the project name.
#            self.name = name
#            
#            # Set the spreadsheetPath.
#            self.spreadsheetPath = spreadsheetPath
#                                
#            # Set the creation time for now.
#            self.createdTime = project.now_utc()
#            
#            # Set the updating time to None.
#            self.updatedTime = None
#            
#            # Set the spreadsheet upload time to None.
#            self.dataUploadTime = None
#            
#            # If we have passed in a spreadsheet path...
#            if self.spreadsheetPath is not None:
#                # Set the data spreadsheet upload time for now.
#                self.dataUploadTime = project.now_utc()
#                
#            # Set the type prefix to 'user'.
#            self.typePrefix = 'project'
#            
#            # Set the file suffix to '.usr'.
#            self.fileSuffix = '.prj'
#            
#            # Set the instance label to the username.
#            self.instanceLabel = name   
#          
#    def updateName(self, newName):
#        # Set the project name.
#        self.name = newName
#        self.instanceLabel = newName
#        
#        # Set the updating time to now.
#        self.updatedTime = project.now_utc()
#        
#    def updateSpreadsheet(self, spreadsheetPath):
#        # Set the spreadsheetPath from what's passed in.
#        self.spreadsheetPath = spreadsheetPath
#        
#        # Set the data spreadsheet upload time for now.
#        self.dataUploadTime = project.now_utc()
#        
#        # Set the updating time to now.
#        self.updatedTime = project.now_utc()
#        
##    def saveToPrjFile(self, dirPath, saveResults=False):
##        # Create a filename containing the project name followed by a .prj 
##        # suffix.
##        fileName = '%s.prj' % self.name
##        
##        # Generate the full file name with path.
##        fullFileName = '%s%s%s' % (dirPath, os.sep, fileName)
##        
##        # Write the object to a Gzip string pickle file.
##        objectToGzipStringPickleFile(fullFileName, self)
##        
##        # Return the full file name.
##        return fullFileName
#
#    def loadFromCopy(self, otherObject):
#        if type(otherObject) == type(self):
#            # Do the superclass copying.
#            super(ProjectSO, self).loadFromCopy(otherObject)
#            
#            self.ownerUID = otherObject.ownerUID
#            self.name = otherObject.name
#            self.spreadsheetPath = otherObject.spreadsheetPath
#            self.createdTime = otherObject.createdTime
#            self.updatedTime = otherObject.updatedTime
#            self.dataUploadTime = otherObject.dataUploadTime
#            
#            # Copy the owner UID.
#            self.ownerUID = otherObject.ownerUID
#            
#    def show(self):
#        # Show superclass attributes.
#        super(ProjectSO, self).show()  
#        
#        print '---------------------'
#
#        print 'Owner User UID: %s' % self.ownerUID.hex
#        print 'Project Name: %s' % self.name
#        print 'Spreadsheet Path: %s' % self.spreadsheetPath
#        print 'Creation Time: %s' % self.createdTime
#        print 'Update Time: %s' % self.updatedTime
#        print 'Data Upload Time: %s' % self.dataUploadTime
#        
#    def getUserFrontEndRepr(self):
#        objInfo = {
#            'project': {
#                'id': self.uid,
#                'name': self.name,
#                'userId': self.ownerUID,
#                'spreadsheetPath': self.spreadsheetPath,
#                'creationTime': self.createdTime,
#                'updatedTime': self.updatedTime,
#                'dataUploadTime': self.dataUploadTime
#            }
#        }
#        return objInfo
#    
##    def saveAsFile(self, loadDir):
##        # Save the project in the file.
##        self.theProject.saveToPrjFile(loadDir, saveResults=True)
##        
##        # Return the filename (not the full one).
##        return self.theProject.name + ".prj" 

#
# Initialization functions 
#
        
def init_filepaths(theApp):
    # Set the Sciris root path to the parent of the current directory, the 
    # latter being the sciris/bin directory since that is where the code is 
    # executed from.
    ds.scirisRootPath = os.path.abspath(os.pardir)
    
    #  Using the current_app set to the passed in app..
    with theApp.app_context():
        # Set the uploads path.
        
        # If we have an absolute directory, use it.
        if os.path.isabs(current_app.config['UPLOADS_DIR']):
            ds.uploadsPath = current_app.config['UPLOADS_DIR']
            
        # Otherwise (we have a relative path), use it (correcting so it is with 
        # respect to the sciris repo directory).
        else:
            ds.uploadsPath = '%s%s%s' % (os.pardir, os.sep, 
                current_app.config['UPLOADS_DIR'])  
        
        # Set the file save root path.
        
        # If we have an absolute directory, use it.
        if os.path.isabs(current_app.config['FILESAVEROOT_DIR']):
            ds.fileSaveRootPath = current_app.config['FILESAVEROOT_DIR']
            
        # Otherwise (we have a relative path), use it (correcting so it is with 
        # respect to the sciris repo directory).
        else:
            ds.fileSaveRootPath = '%s%s%s' % (os.pardir, os.sep, 
                current_app.config['FILESAVEROOT_DIR'])
         
    # If the datafiles path doesn't exist yet...
    if not os.path.exists(ds.fileSaveRootPath):
        # Create datafiles directory.
        os.mkdir(ds.fileSaveRootPath)
        
        # Create an uploads subdirectory of this.
        os.mkdir(ds.uploadsPath)
        
        # # Create the fake data for scatterplots.
        # sd = model.ScatterplotData(model.makeUniformRandomData(50))
        # fullFileName = '%s%sgraph1.csv' % (ds.fileSaveRootPath, os.sep)
        # sd.saveAsCsv(fullFileName)
        
        # sd = model.ScatterplotData(model.makeUniformRandomData(50))
        # fullFileName = '%s%sgraph2.csv' % (ds.fileSaveRootPath, os.sep)
        # sd.saveAsCsv(fullFileName)
        
        # sd = model.ScatterplotData(model.makeUniformRandomData(50))
        # fullFileName = '%s%sgraph3.csv' % (ds.fileSaveRootPath, os.sep)
        # sd.saveAsCsv(fullFileName) 
        
def init_datastore(theApp):
    # Create the DataStore object, setting up Redis.
    with theApp.app_context():
        ds.theDataStore = ds.DataStore(redisDbURL=current_app.config['REDIS_URL'])

    # Load the DataStore state from disk.
    ds.theDataStore.load()
    
    # Uncomment this line (for now) to reset the database, and then recomment
    # before running for usage.
#    ds.theDataStore.deleteAll()
    
def init_users(theApp):
    # Look for an existing users dictionary.
    theUserDictUID = ds.theDataStore.getUIDFromInstance('userdict', 'Users Dictionary')
    
    # Create the user dictionary object.  Note, that if no match was found, 
    # this will be assigned a new UID.
    user.theUserDict = user.UserDict(theUserDictUID)
    
    # If there was a match...
    if theUserDictUID is not None:
        print '>> Loading UserDict from the DataStore.'
        user.theUserDict.loadFromDataStore() 
    
    # Else (no match)...
    else:
        print '>> Creating a new UserDict.'   
        user.theUserDict.addToDataStore()
        user.theUserDict.add(user.testUser)
        user.theUserDict.add(user.testUser2)
        user.theUserDict.add(user.testUser3)

    # Show all of the handles in theDataStore.
    print '>> List of all DataStore handles...'
    ds.theDataStore.showHandles()
    
    # Show all of the users in theUserDict.
    print '>> List of all users...'
    user.theUserDict.show()
    
def init_projects(theApp):
    # Look for an existing ProjectCollection.
    theProjsUID = ds.theDataStore.getUIDFromInstance('projectscoll', 
        'Projects Collection')
    
    # Create the projects collection object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    project.theProjCollection = project.ProjectCollection(theProjsUID)
    
    # If there was a match...
    if theProjsUID is not None:
        print '>> Loading ProjectCollection from the DataStore.'
        project.theProjCollection.loadFromDataStore() 
    
    # Else (no match)...
    else:
        # Load the data path holding the Excel files.
        dataPath = hptool.HPpath('data')
    
        print '>> Creating a new ProjectCollection.'   
        project.theProjCollection.addToDataStore()
        
        print '>> Starting a demo project.'
        theProject = hptool.Project(name='Afghanistan test 1', 
            burdenfile=dataPath + 'ihme-gbd.xlsx', 
            interventionsfile=dataPath + 'dcp-data.xlsx')  
        theProjectSO = ProjectSO(theProject, user.get_scirisdemo_user())
#        theProjectSO = ProjectSO('Afghanistan test 1', 
#            user.get_scirisdemo_user(), 
#            spreadsheetPath=None)
        project.theProjCollection.addObject(theProjectSO)
        
        print '>> Starting a second demo project.'
        theProject = hptool.Project(name='Afghanistan HBP equity')
        theProjectSO = ProjectSO(theProject, user.get_scirisdemo_user())
#        theProjectSO = ProjectSO('Afghanistan HBP equity', 
#            user.get_scirisdemo_user(), 
#            spreadsheetPath=None)
        project.theProjCollection.addObject(theProjectSO)
        
        print '>> Starting a third demo project.'
        theProject = hptool.Project(name='Final Afghanistan HBP')
        theProjectSO = ProjectSO(theProject, user.get_scirisdemo_user())
#        theProjectSO = ProjectSO('Final Afghanistan HBP', 
#            user.get_scirisdemo_user(), 
#            spreadsheetPath=None)
        project.theProjCollection.addObject(theProjectSO)
        
        print '>> Starting a fourth demo project.'
        theProject = hptool.Project(name='Pakistan test 1')  
        theProjectSO = ProjectSO(theProject, user.get_scirisdemo_user())
#        theProjectSO = ProjectSO('Pakistan test 1', 
#            user.get_scirisdemo_user(), 
#            spreadsheetPath=None)
        project.theProjCollection.addObject(theProjectSO)
        
    # Show what's in the ProjectCollection.    
    project.theProjCollection.show()
    
def init_main(theApp): 
    print('-- Welcome to the HealthPrior webapp, version %s (%s) --' % (hptool.version, hptool.versiondate))
    return None
    
#
# Other functions
#

# Do the meat of the RPC calls, passing args and kwargs to the appropriate 
# function in the appropriate handler location.
def doRPC(rpcType, handlerLocation, requestMethod, username=None):
    # If we are doing an upload, pull the RPC information out of the request 
    # form instead of the request data.
    if rpcType == 'upload':
        # Pull out the function name, args, and kwargs
        fn_name = request.form.get('funcname')
        args = json.loads(request.form.get('args', "[]"))
        kwargs = json.loads(request.form.get('kwargs', "{}"))
    
    # Otherwise (normal and download RPCs), pull the RPC information from the 
    # request data.
    else:
        # Convert the request.data JSON to a Python dict, and pull out the 
        # function name, args, and kwargs.  
        if requestMethod in ['POST', 'PUT']:
            reqdict = json.loads(request.data)
        elif requestMethod == 'GET':
            reqdict = request.args
        fn_name = reqdict['funcname']
        args = reqdict.get('args', [])
        # Insert the username as a the first argument if it is passed in not
        # None.
        if username is not None:
            args.insert(0, username)
        kwargs = reqdict.get('kwargs', {})
        
    # Check to see if the function exists here in main.py and get it 
    # ready to call if it is.  Any versions of the functions in main.py 
    # override those versions in user.py or project.py (or other places 
    # where we have handlers).
    funcExists = hasattr(sys.modules[__name__], fn_name)
    print('>> Checking RPC function "main.%s" -> %s' % (fn_name, funcExists))
    if funcExists:
        func = getattr(sys.modules[__name__], fn_name)
        handlerLocation = 'main'
        
    # Otherwise (it's not in main.py), if the handlerLocation is 'user'...
    elif handlerLocation == 'user':
        # Check to see if there is a match.
        funcExists = hasattr(user, fn_name)
        print('>> Checking RPC function "user.%s" -> %s' % (fn_name, funcExists))
        
        # If there is a match, get the function ready.
        if funcExists:
            func = getattr(user, fn_name)
            
    # Otherwise (the function isn't in main.py and the handler is not 'user')...
    elif handlerLocation == 'project':
        # Check to see if there is a match.
        funcExists = hasattr(project, fn_name)
        print('>> Checking RPC function "project.%s" -> %s' % (fn_name, funcExists))
        
        # If there is a match, get the function ready.
        if funcExists:
            func = getattr(project, fn_name)   
            
    elif handlerLocation not in['scirismain', 'main', 'user', 'project']:
        return jsonify({'error': 
            'Attempted to call RPC function in non-existent handler location \'%s\'' \
                % handlerLocation}) 

    # If the function doesn't exist, return an error to the client saying it 
    # doesn't exist.
    if not funcExists:
        return jsonify({'error': 
            'Attempted to call non-existent RPC function \'%s\'' % fn_name}) 
    
    # If we are doing an upload.
    if rpcType == 'upload':
        # Grab the formData file that was uploaded.    
        file = request.files['uploadfile']
        
        # Grab the filename of this file, and generate the full upload path / 
        # filename.
        filename = secure_filename(file.filename)
        uploaded_fname = os.path.join(ds.uploadsPath, filename)
        
        # Save the file to the uploads directory.
        file.save(uploaded_fname)
        
        # Prepend the file name to the args list.
        args.insert(0, uploaded_fname)
        
    # Show the call of the function.    
    print('>> Calling RPC function "%s.%s"' % (handlerLocation, fn_name))
    
    # Execute the function to get the results.
    result = func(*args, **kwargs)  
    
    # If we are doing a download, prepare the response and send it off.
    if rpcType == 'download':
        # If we got None for a result (the full file name), return an error to 
        # the client.
        if result is None:
            return jsonify({'error': 'Could not find requested resource'})
    
        # Pull out the directory and file names from the full file name.
        dirName, fileName = os.path.split(result)
         
        # Make the response message with the file loaded as an attachment.
        response = send_from_directory(dirName, fileName, as_attachment=True)
        response.status_code = 201  # Status 201 = Created
        response.headers['filename'] = fileName
        
        # Return the response message.
        return response
    
    # Otherwise (normal and upload RPCs), 
    else:
        # If None was returned by the RPC function, return ''.
        if result is None:
            return ''
        
        # Otherwise, convert the result (probably a dict) to JSON and return it.
        else:
            return jsonify(json_sanitize_result(result))

def json_sanitize_result(theResult):
    """
    This is the main conversion function for Python data-structures into
    JSON-compatible data structures.

    Use this as much as possible to guard against data corruption!

    Args:
        theResult: almost any kind of data structure that is a combination
            of list, numpy.ndarray, etc.

    Returns:
        A converted dict/list/value that should be JSON compatible
    """

    if isinstance(theResult, list) or isinstance(theResult, tuple):
        return [json_sanitize_result(p) for p in list(theResult)]
    
    if isinstance(theResult, np.ndarray):
        if theResult.shape: # Handle most cases, incluing e.g. array([5])
            return [json_sanitize_result(p) for p in list(theResult)]
        else: # Handle the special case of e.g. array(5)
            return [json_sanitize_result(p) for p in list(np.array([theResult]))]

    if isinstance(theResult, dict):
        return {str(k): json_sanitize_result(v) for k, v in theResult.items()}

    if isinstance(theResult, np.bool_):
        return bool(theResult)

    if isinstance(theResult, float):
        if np.isnan(theResult):
            return None

    if isinstance(theResult, np.float64):
        if np.isnan(theResult):
            return None
        else:
            return float(theResult)

    if isinstance(theResult, unicode):
        return theResult
#        return str(theResult)  # original line  (watch to make sure the 
#                                                 new line doesn't break things)
    
    if isinstance(theResult, set):
        return list(theResult)

#    if isinstance(theResult, UUID):
#        return str(theResult)

    return theResult


def get_version_info():
	''' Return the informatino about the project. '''
	gitinfo = sciris.utils.gitinfo(__file__)
	version_info = {
        'version': hptool.version,
        'date': hptool.versiondate,
        'gitbranch': gitinfo['branch'],
        'githash': gitinfo['hash'],
        'gitdate': gitinfo['date'],
	}
	return version_info


##
## Project helper functions
##

def save_project(theProj):
    """
    Given a Project object, wrap it in a new ProjectSO object and put this 
    in the project collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Project.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_record = project.load_project_record(theProj.uid)
    
    # Copy the project, only save what we want...
    new_project = dcp(theProj)
         
    # Create the new project entry and enter it into the ProjectCollection.
    # Note: We don't need to pass in project.uid as a 3rd argument because 
    # the constructor will automatically use the Project's UID.
    theProjSO = ProjectSO(new_project, project_record.ownerUID)
    project.theProjCollection.updateObject(theProjSO)
    
def update_project_with_fn(project_id, update_project_fn):
    """
    Do an update of a hptool Project, given the UID and a function that 
    does the actual Project updating.
    """ 
    
    # Load the project.
    theProj = project.load_project(project_id)
    
    # Execute the passed-in function that modifies the project.
    update_project_fn(theProj)
    
    # Set the updating time to now.
    theProj.modified = project.now_utc()
    
    # Save the changed project.
    save_project(theProj) 
    
def save_project_as_new(theProj, user_id):
    """
    Given a Project object and a user UID, wrap the Project in a new ProjectSO 
    object and put this in the project collection, after getting a fresh UID
    for this Project.  Then do the actual save.
    """ 
    
    # Set a new project UID, so we aren't replicating the UID passed in.
    theProj.uid = uuid()
    
    # Create the new project entry and enter it into the ProjectCollection.
    theProjSO = ProjectSO(theProj, user_id)
    project.theProjCollection.addObject(theProjSO)  

    # Display the call information.
    print(">> save_project_as_new '%s'" % theProj.name)

    # Save the changed Project object to the DataStore.
    save_project(theProj)
    
    return None

def get_burden_set_fe_repr(theBurdenSet):
    objInfo = {
        'burdenset': {
            'name': theBurdenSet.name,
            'uid': theBurdenSet.uid,
            'creationTime': theBurdenSet.created,
            'updateTime': theBurdenSet.modified
        }
    }
    return objInfo

def get_interv_set_fe_repr(theIntervSet):
    objInfo = {
        'intervset': {
            'name': theIntervSet.name,
            'uid': theIntervSet.uid,
            'creationTime': theIntervSet.created,
            'updateTime': theIntervSet.modified
        }
    }
    return objInfo

#
# RPC functions
#

##
## User RPCs
##

# We will have some overrides here because we want to handle account editing 
# and password changing in a way different than the defaults.

##
## Project RPCs
##

# I've tried to maximimize the number of these functions that I am able to 
# move into sciris/project.py, but some that require dependency on the model 
# Project class are defined here.

def create_new_project(user_id):
    """
    Create a new HealthPrior project.
    """
    
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Load the data path holding the Excel files.
    dataPath = hptool.HPpath('data')
    
    # Get a unique name for the project to be added.
    newProjName = project.get_unique_name('New project', other_names=None)
    
    # Create the project, loading in the desired spreadsheets.
    theProj = hptool.Project(name=newProjName, 
        burdenfile=dataPath + 'ihme-gbd.xlsx', 
        interventionsfile=dataPath + 'dcp-data.xlsx')  
    
    # Set the burden population size.
    theProj.burden().popsize = 36373.176 # From UN population division 
    
    # Display the call information.
    print(">> create_new_project %s" % (theProj.name))    
    
    # Save the new project in the DataStore.
    save_project_as_new(theProj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(theProj.uid) }  
  
def update_project_from_summary(project_summary):
    """
    Given the passed in project summary, update the underlying project 
    accordingly.
    """ 
    
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}   
    
    # Load the project corresponding with this summary.
    theProj = project.load_project(project_summary['project']['id'])
       
    # Use the summary to set the actual project.
    theProj.name = project_summary['project']['name']
    
    # Set the modified time to now.
    theProj.modified = project.now_utc()
    
    # Save the changed project to the DataStore.
    save_project(theProj)
    
def copy_project(project_id):
    """
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    """
    
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}   
    
    # Get the Project object for the project to be copied.
    project_record = project.load_project_record(project_id, raise_exception=True)
    theProj = project_record.theProject
    
    # Make a copy of the project loaded in to work with.
    new_project = dcp(theProj)
    
    # Just change the project name, and we have the new version of the 
    # Project object to be saved as a copy.
    new_project.name = project.get_unique_name(theProj.name, other_names=None)
    
    # Set the user UID for the new projects record to be the current user.
    user_id = current_user.get_id() 
    
    # Display the call information.
    print(">> copy_project %s" % (new_project.name)) 
    
    # Save a DataStore projects record for the copy project.
    save_project_as_new(new_project, user_id)
    
    # Remember the new project UID (created in save_project_as_new()).
    copy_project_id = new_project.uid

    # Return the UID for the new projects record.
    return { 'projectId': copy_project_id }

def create_project_from_prj_file(prj_filename, user_id):
    """
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    """
    
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'uploadProjectRPC':
        return {'error': 'Unauthorized RPC'}  
    
    # Display the call information.
    print(">> create_project_from_prj_file '%s'" % prj_filename)
    
    # Try to open the .prj file, and return an error message if this fails.
    try:
        theProj = ds.gzipStringPickleFileToObject(prj_filename)
    except Exception:
        return { 'projectId': 'BadFileFormatError' }
    
    # Reset the project name to a new project name that is unique.
    theProj.name = project.get_unique_name(theProj.name, other_names=None)
    
    # Save the new project in the DataStore.
    save_project_as_new(theProj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(theProj.uid) }

##
## Burden set RPCs
##   
    
def get_project_burden_sets(project_id):
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Get the Project object.
    theProj = project.load_project(project_id)
    
    # Get a list of the Burden objects.
    burdenSets = [theProj.burdensets[ind] for ind in range(len(theProj.burdensets))] 
    
    # Return the JSON-friendly result.
    return {'burdensets': map(get_burden_set_fe_repr, burdenSets)}

def get_project_burden_set_diseases(project_id, burdenset_numindex):
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Get the Project object.
    theProj = project.load_project(project_id)
    
    # Get the burden set that matches burdenset_numindex.
    burdenSet = theProj.burden(key=burdenset_numindex)
    
    # Return an empty list if no data is present.
    if burdenSet.data is None:
        return { 'diseases': [] }

    # Gather the list for all of the diseases.
    diseaseData = burdenSet.export(cols=['active','cause','dalys','deaths','prevalence'], header=False)
    
    # Return success.
    return { 'diseases': diseaseData }
    
def create_burden_set(project_id, new_burden_set_name):

    def update_project_fn(theProj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        uniqueName = project.get_unique_name(new_burden_set_name, 
            other_names=list(theProj.burdensets))
        
        # Create a new (empty) burden set.
        newBurdenSet = Burden(project=theProj, name=uniqueName)
        dataPath = hptool.HPpath('data')
        newBurdenSet.loaddata(dataPath+'ihme-gbd.xlsx')
        
        # Put the new burden set in the dictionary.
        theProj.burdensets[uniqueName] = newBurdenSet
        
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Do the project update using the internal function.
    update_project_with_fn(project_id, update_project_fn)

    # Return the new burden sets.
    return get_project_burden_sets(project_id)

def delete_burden_set(project_id, burdenset_numindex):

    def update_project_fn(theProj):
        theProj.burdensets.pop(burdenset_numindex)
        
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Do the project update using the internal function.    
    update_project_with_fn(project_id, update_project_fn)   
    
def copy_burden_set(project_id, burdenset_numindex):

    def update_project_fn(theProj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        uniqueName = project.get_unique_name(theProj.burdensets[burdenset_numindex].name, 
            other_names=list(theProj.burdensets))
        
        # Create a new burdenset which is a copy of the old one.
        newBurdenSet = dcp(theProj.burdensets[burdenset_numindex])
        
        # Overwrite the old name with the new.
        newBurdenSet.name = uniqueName
       
        # Put the new burden set in the dictionary.
        theProj.burdensets[uniqueName] = newBurdenSet
        
    # Do the project update using the internal function.  
    update_project_with_fn(project_id, update_project_fn)
    
    # Return the new burden sets.
    return get_project_burden_sets(project_id) 

def rename_burden_set(project_id, burdenset_numindex, new_burden_set_name):

    def update_project_fn(theProj):
        # Overwrite the old name with the new.
        theProj.burdensets[burdenset_numindex].name = new_burden_set_name
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)
    
def get_project_burden_plots(project_id, burdenset_numindex, engine='bokeh'):
    ''' Plot the disease burden '''
    
#    def fixgraph(graph, graph_dict):
#        print('Warning, need to incorporate into mpld3')
#        ylabels = [l.get_text() for l in graph.axes[0].get_yticklabels()]
#        graph_dict['ylabels'] = ylabels
#        xlabels = [l.get_text() for l in graph.axes[0].get_xticklabels()]
#        graph_dict['xlabels'] = xlabels
#        return graph_dict
    
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Get the Project object.
    theProj = project.load_project(project_id)
    
    # Get the burden set that matches burdenset_numindex.
    burdenSet = theProj.burden(key=burdenset_numindex)
    
    figs = []
    for which in ['dalys','deaths','prevalence']:
        fig = burdenSet.plottopcauses(which=which) # Create the figure
        figs.append(fig)
        
    # Gather the list for all of the diseases.
    graphs = []
    for fig in figs:
        if engine=='matplotlib':
            graph_dict = mpld3.fig_to_dict(fig)
        elif engine=='bokeh':
            graph_dict = fig
            fig['script'] = '\n'.join(fig['script'].split('\n')[2:-1]) # Remove first and last lines
#        graph_dict = fixgraph(fig, graph_dict)
        graphs.append(graph_dict)
    
    # Return success.
    return {'graph1': graphs[0],
            'graph2': graphs[1],
            'graph3': graphs[2],}
    
##
## Intervention set RPCs
## 
    
def get_project_interv_sets(project_id):
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Get the Project object.
    theProj = project.load_project(project_id)
    
    # Get a list of the Interventions objects.
    intervSets = [theProj.intersets[ind] for ind in range(len(theProj.intersets))] 
    
    # Return the JSON-friendly result.
    return {'intervsets': map(get_interv_set_fe_repr, intervSets)}

def get_project_interv_set_intervs(project_id, intervset_numindex):
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Get the Project object.
    theProj = project.load_project(project_id)
    
    # Get the intervention set that matches intervset_numindex.
    intervSet = theProj.inter(key=intervset_numindex)
    
    # Return an empty list if no data is present.
    if intervSet.data is None:
        return { 'interventions': [] } 
    
    # Gather the list for all of the interventions.
    intervData = [list(theInterv) for theInterv in intervSet.data]
    
    # Return success.
    return { 'interventions': intervData }

def create_interv_set(project_id, new_interv_set_name):

    def update_project_fn(theProj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        uniqueName = project.get_unique_name(new_interv_set_name, 
            other_names=list(theProj.intersets))
        
        # Create a new (empty) intervention set.
        newIntervSet = Interventions(project=theProj, name=uniqueName)
        
        # Put the new intervention set in the dictionary.
        theProj.intersets[uniqueName] = newIntervSet
        
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Do the project update using the internal function.
    update_project_with_fn(project_id, update_project_fn)

    # Return the new intervention sets.
    return get_project_interv_sets(project_id)

def delete_interv_set(project_id, intervset_numindex):

    def update_project_fn(theProj):
        theProj.intersets.pop(intervset_numindex)
        
    # Check (for security purposes) that the function is being called by the 
    # correct endpoint, and if not, fail.
    if request.endpoint != 'normalProjectRPC':
        return {'error': 'Unauthorized RPC'}
    
    # Do the project update using the internal function.    
    update_project_with_fn(project_id, update_project_fn)   
    
def copy_interv_set(project_id, intervset_numindex):

    def update_project_fn(theProj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        uniqueName = project.get_unique_name(theProj.intersets[intervset_numindex].name, 
            other_names=list(theProj.intersets))
        
        # Create a new intervention set which is a copy of the old one.
        newIntervSet = dcp(theProj.intersets[intervset_numindex])
        
        # Overwrite the old name with the new.
        newIntervSet.name = uniqueName
       
        # Put the new intervention set in the dictionary.
        theProj.intersets[uniqueName] = newIntervSet
        
    # Do the project update using the internal function.  
    update_project_with_fn(project_id, update_project_fn)
    
    # Return the new intervention sets.
    return get_project_interv_sets(project_id)

def rename_interv_set(project_id, intervset_numindex, new_interv_set_name):

    def update_project_fn(theProj):
        # Overwrite the old name with the new.
        theProj.intersets[intervset_numindex].name = new_interv_set_name
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)
    
##
## Temporary (development) RPCs
##

def tester_func_main(project_id):
    theProjRecord = project.load_project_record(project_id)
    print theProjRecord
    
    return 'success'