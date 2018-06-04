"""
api.py -- code related to HealthPrior project management
    
Last update: 6/1/18 (gchadder3)
"""

#
# Imports
#

import sciris.fileio as fileio
import sciris.scirisobjects as sobj
import sciris.datastore as ds
import sciris.user as user
import os
import uuid
import datetime
import dateutil
import dateutil.tz
from zipfile import ZipFile
from flask_login import current_user
import mpld3

import sciris.web as sw
import sciris.core as sc
import hptool as hp

#
# Globals
#

# The ProjectCollection object for all of the app's projects.  Gets 
# initialized by and loaded by init_projects().
proj_collection = None

# Dictionary to hold all of the registered RPCs in this module.
RPC_dict = {}

# RPC registration decorator factory created using call to make_register_RPC().
register_RPC = sw.make_register_RPC(RPC_dict)

#
# Classes
#

class ProjectSO(sobj.ScirisObject):
    """
    A ScirisObject-wrapped Optima Nutrition Project object.
    
    Methods:
        __init__(proj: Project, owner_uid: UUID, uid: UUID [None]): 
            void -- constructor
        load_from_copy(other_object): void -- assuming other_object is another 
            object of our type, copy its contents to us (calls the 
            ScirisObject superclass version of this method also)   
        show(): void -- print the contents of the object
        get_user_front_end_repr(): dict -- get a JSON-friendly dictionary 
            representation of the object state the front-end uses for non-
            admin purposes  
        save_as_file(load_dir: str): str -- given a load dictionary, save the 
            project in a file there and return the file name
                    
    Attributes:
        proj (Project) -- the actual Project object being wrapped
        owner_uid (UUID) -- the UID of the User that owns the Project
        
    Usage:
        >>> my_project = ProjectSO(proj, owner_uid)                      
    """
    
    def  __init__(self, proj, owner_uid, uid=None):
        # NOTE: uid argument is ignored but kept here to not mess up
        # inheritance.
        
        # Make sure the owner UID argument is a valid UUID, converting a hex 
        # text to a UUID object, if needed.        
        valid_uuid = sobj.get_valid_uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:       
            # Set superclass parameters.
            super(ProjectSO, self).__init__(proj.uid)
                                   
            # Set the project to the Optima Project that is passed in.
            self.proj = proj
            
            # Set the owner (User) UID.
            self.owner_uid = valid_uuid
        
    def load_from_copy(self, other_object):
        if type(other_object) == type(self):
            # Do the superclass copying.
            super(ProjectSO, self).load_from_copy(other_object)
            
            # Copy the Project object itself.
            self.proj = sc.dcp(other_object.proj)
            
            # Copy the owner UID.
            self.owner_uid = other_object.owner_uid
                
    def show(self):
        # Show superclass attributes.
        super(ProjectSO, self).show()  
        
        # Show the Optima defined display text for the project.
        print '---------------------'
        print 'Owner User UID: %s' % self.owner_uid.hex
        print 'Project Name: %s' % self.proj.name
        print 'Creation Time: %s' % self.proj.created
        print 'Update Time: %s' % self.proj.modified
            
    def get_user_front_end_repr(self):
        obj_info = {
            'project': {
                'id': self.uid,
                'name': self.proj.name,
                'userId': self.owner_uid,
                'creationTime': self.proj.created,
                'updatedTime': self.proj.modified     
            }
        }
        return obj_info
    
    def save_as_file(self, load_dir):
        # Create a filename containing the project name followed by a .prj 
        # suffix.
        file_name = '%s.prj' % self.proj.name
        
        # Generate the full file name with path.
        full_file_name = '%s%s%s' % (load_dir, os.sep, file_name)   
     
        # Write the object to a Gzip string pickle file.
        ds.object_to_gzip_string_pickle_file(full_file_name, self.proj)
        
        # Return the filename (not the full one).
        return self.proj.name + ".prj"
    
        
class ProjectCollection(sobj.ScirisCollection):
    """
    A collection of Projects.
    
    Methods:
        __init__(uid: UUID [None], type_prefix: str ['projectscoll'], 
            file_suffix: str ['.pc'], 
            instance_label: str ['Projects Collection']): void -- constructor  
        get_user_front_end_repr(owner_uid: UUID): list -- return a list of dicts 
            containing JSON-friendly project contents for each project that 
            is owned by the specified user UID
        get_project_entries_by_user(owner_uid: UUID): list -- return the ProjectSOs 
            that match the owning User UID in a list
        
    Usage:
        >>> proj_collection = ProjectCollection(uuid.UUID('12345678123456781234567812345678'))                      
    """
    
    def __init__(self, uid, type_prefix='projectscoll', file_suffix='.pc', 
        instance_label='Projects Collection'):
        # Set superclass parameters.
        super(ProjectCollection, self).__init__(uid, type_prefix, file_suffix, 
             instance_label)
            
    def get_user_front_end_repr(self, owner_uid):
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        valid_uuid = sobj.get_valid_uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:               
            # Get dictionaries for each Project in the dictionary.
            projects_info = [self.obj_dict[key].get_user_front_end_repr() \
                for key in self.obj_dict \
                if self.obj_dict[key].owner_uid == valid_uuid]
            return projects_info
        
        # Otherwise, return an empty list.
        else:
            return []
        
    def get_project_entries_by_user(self, owner_uid):
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        valid_uuid = sobj.get_valid_uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:    
            # Get ProjectSO entries for each Project in the dictionary.
            project_entries = [self.obj_dict[key] \
                for key in self.obj_dict \
                if self.obj_dict[key].owner_uid == valid_uuid]
            return project_entries
        
        # Otherwise, return an empty list.
        else:
            return []


#
# Initialization function
#

def init_projects(app):
    global proj_collection  # need this to allow modification within the module
    
    # Look for an existing ProjectCollection.
    proj_collection_uid = ds.data_store.get_uid_from_instance('projectscoll', 
        'Projects Collection')
    
    # Create the projects collection object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    proj_collection = ProjectCollection(proj_collection_uid)
    
    # If there was a match...
    if proj_collection_uid is not None:
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Loading ProjectCollection from the DataStore.'
        proj_collection.load_from_data_store() 
    
    # Else (no match)...
    else:
        # Load the data path holding the Excel files.
        data_path = hp.HPpath('data')
    
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Creating a new ProjectCollection.'   
        proj_collection.add_to_data_store()
        
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Starting a demo project.'
        proj = hp.Project(name='Afghanistan test 1', 
            burdenfile=data_path + 'ihme-gbd.xlsx', 
            interventionsfile=data_path + 'dcp-data-afg-v1.xlsx')  
        projSO = ProjectSO(proj, user.get_scirisdemo_user())
#        projSO = ProjectSO('Afghanistan test 1', 
#            user.get_scirisdemo_user(), 
#            spreadsheet_path=None)
        proj_collection.add_object(projSO)
        
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Starting a second demo project.'
        proj = hp.Project(name='Afghanistan HBP equity')
        projSO = ProjectSO(proj, user.get_scirisdemo_user())
#        projSO = ProjectSO('Afghanistan HBP equity', 
#            user.get_scirisdemo_user(), 
#            spreadsheet_path=None)
        proj_collection.add_object(projSO)
        
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Starting a third demo project.'
        proj = hp.Project(name='Final Afghanistan HBP')
        projSO = ProjectSO(proj, user.get_scirisdemo_user())
#        projSO = ProjectSO('Final Afghanistan HBP', 
#            user.get_scirisdemo_user(), 
#            spreadsheet_path=None)
        proj_collection.add_object(projSO)
        
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Starting a fourth demo project.'
        proj = hp.Project(name='Pakistan test 1')  
        projSO = ProjectSO(proj, user.get_scirisdemo_user())
#        projSO = ProjectSO('Pakistan test 1', 
#            user.get_scirisdemo_user(), 
#            spreadsheet_path=None)
        proj_collection.add_object(projSO)
        
    if app.config['LOGGING_MODE'] == 'FULL':
        # Show what's in the ProjectCollection.    
        proj_collection.show()
        
#
# Other functions (mostly helpers for the RPCs)
#
    
def now_utc():
    ''' Get the current time, in UTC time '''
    now = datetime.datetime.now(dateutil.tz.tzutc())
    return now

def load_project_record(project_id, raise_exception=True):
    """
    Return the project DataStore reocord, given a project UID.
    """ 
    
    # Load the matching ProjectSO object from the database.
    project_record = proj_collection.get_object_by_uid(project_id)

    # If we have no match, we may want to throw an exception.
    if project_record is None:
        if raise_exception:
            raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
            
    # Return the Project object for the match (None if none found).
    return project_record

def load_project(project_id, raise_exception=True):
    """
    Return the Nutrition Project object, given a project UID, or None if no 
    ID match is found.
    """ 
    
    # Load the project record matching the ID passed in.
    project_record = load_project_record(project_id, 
        raise_exception=raise_exception)
    
    # If there is no match, raise an exception or return None.
    if project_record is None:
        if raise_exception:
            raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
        else:
            return None
        
    # Return the found project.
    return project_record.proj

def load_project_summary_from_project_record(project_record):
    """
    Return the project summary, given the DataStore record.
    """ 
    
    # Return the built project summary.
    return project_record.get_user_front_end_repr()
  
def load_current_user_project_summaries2():
    """
    Return project summaries for all projects the user has to the client.
    """ 
    
    # Get the ProjectSO entries matching the user UID.
    project_entries = proj_collection.get_project_entries_by_user(current_user.get_id())
    
    # Grab a list of project summaries from the list of ProjectSO objects we 
    # just got.
    return {'projects': map(load_project_summary_from_project_record, 
        project_entries)}
                
def get_unique_name(name, other_names=None):
    """
    Given a name and a list of other names, find a replacement to the name 
    that doesn't conflict with the other names, and pass it back.
    """
    
    # If no list of other_names is passed in, load up a list with all of the 
    # names from the project summaries.
    if other_names is None:
        other_names = [p['project']['name'] for p in load_current_user_project_summaries2()['projects']]
      
    # Start with the passed in name.
    i = 0
    unique_name = name
    
    # Try adding an index (i) to the name until we find one that no longer 
    # matches one of the other names in the list.
    while unique_name in other_names:
        i += 1
        unique_name = "%s (%d)" % (name, i)
        
    # Return the found name.
    return unique_name

def save_project(proj):
    """
    Given a Project object, wrap it in a new ProjectSO object and put this 
    in the project collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Project.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_record = load_project_record(proj.uid)
    
    # Copy the project, only save what we want...
    new_project = sc.dcp(proj)
         
    # Create the new project entry and enter it into the ProjectCollection.
    # Note: We don't need to pass in project.uid as a 3rd argument because 
    # the constructor will automatically use the Project's UID.
    projSO = ProjectSO(new_project, project_record.owner_uid)
    proj_collection.update_object(projSO)
    
def update_project_with_fn(project_id, update_project_fn):
    """
    Do an update of a hptool Project, given the UID and a function that 
    does the actual Project updating.
    """ 
    
    # Load the project.
    proj = load_project(project_id)
    
    # Execute the passed-in function that modifies the project.
    update_project_fn(proj)
    
    # Set the updating time to now.
    proj.modified = now_utc()
    
    # Save the changed project.
    save_project(proj) 
    
def save_project_as_new(proj, user_id):
    """
    Given a Project object and a user UID, wrap the Project in a new ProjectSO 
    object and put this in the project collection, after getting a fresh UID
    for this Project.  Then do the actual save.
    """ 
    
    # Set a new project UID, so we aren't replicating the UID passed in.
    proj.uid = sc.uuid()
    
    # Create the new project entry and enter it into the ProjectCollection.
    projSO = ProjectSO(proj, user_id)
    proj_collection.add_object(projSO)  

    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> save_project_as_new '%s'" % proj.name)

    # Save the changed Project object to the DataStore.
    save_project(proj)
    
    return None

def get_burden_set_fe_repr(burdenset):
    obj_info = {
        'burdenset': {
            'name': burdenset.name,
            'uid': burdenset.uid,
            'creationTime': burdenset.created,
            'updateTime': burdenset.modified
        }
    }
    return obj_info

def get_interv_set_fe_repr(interv_set):
    obj_info = {
        'intervset': {
            'name': interv_set.name,
            'uid': interv_set.uid,
            'creationTime': interv_set.created,
            'updateTime': interv_set.modified
        }
    }
    return obj_info

def get_package_set_fe_repr(packageset):
    obj_info = {
        'packageset': {
            'name': packageset.name,
            'uid': packageset.uid,
            'creationTime': packageset.created,
            'updateTime': packageset.modified
        }
    }
    return obj_info

#
# RPC functions
#

##
## Project RPCs
##
    
@register_RPC(validation_type='nonanonymous user')
def get_scirisdemo_projects():
    """
    Return the projects associated with the Sciris Demo user.
    """
    
    # Get the user UID for the _ScirisDemo user.
    user_id = user.get_scirisdemo_user()
   
    # Get the ProjectSO entries matching the _ScirisDemo user UID.
    project_entries = proj_collection.get_project_entries_by_user(user_id)

    # Collect the project summaries for that user into a list.
    project_summary_list = map(load_project_summary_from_project_record, 
        project_entries)
    
    # Sort the projects by the project name.
    sorted_summary_list = sorted(project_summary_list, 
        key=lambda proj: proj['project']['name']) # Sorts by project name
    
    # Return a dictionary holding the project summaries.
    output = {'projects': sorted_summary_list}
    return output

@register_RPC(validation_type='nonanonymous user')
def load_project_summary(project_id):
    """
    Return the project summary, given the Project UID.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_entry = load_project_record(project_id)
    
    # Return a project summary from the accessed ProjectSO entry.
    return load_project_summary_from_project_record(project_entry)

@register_RPC(validation_type='nonanonymous user')
def load_current_user_project_summaries():
    """
    Return project summaries for all projects the user has to the client.
    """ 
    
    return load_current_user_project_summaries2()

@register_RPC(validation_type='nonanonymous user')                
def load_all_project_summaries():
    """
    Return project summaries for all projects to the client.
    """ 
    
    # Get all of the ProjectSO entries.
    project_entries = proj_collection.get_all_objects()
    
    # Grab a list of project summaries from the list of ProjectSO objects we 
    # just got.
    return {'projects': map(load_project_summary_from_project_record, 
        project_entries)}
            
@register_RPC(validation_type='nonanonymous user')    
def delete_projects(project_ids):
    """
    Delete all of the projects with the passed in UIDs.
    """ 
    
    # Loop over the project UIDs of the projects to be deleted...
    for project_id in project_ids:
        # Load the project record matching the UID of the project passed in.
        record = load_project_record(project_id, raise_exception=True)
        
        # If a matching record is found, delete the object from the 
        # ProjectCollection.
        if record is not None:
            proj_collection.delete_object_by_uid(project_id)

@register_RPC(call_type='download', validation_type='nonanonymous user')   
def download_project(project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    
    # Load the project with the matching UID.
    proj = load_project(project_id, raise_exception=True)
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path
        
    # Create a filename containing the project name followed by a .prj 
    # suffix.
    file_name = '%s.prj' % proj.name
        
    # Generate the full file name with path.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name)
        
    # Write the object to a Gzip string pickle file.
    fileio.object_to_gzip_string_pickle_file(full_file_name, proj)
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> download_project %s" % (full_file_name))
    
    # Return the full filename.
    return full_file_name

@register_RPC(call_type='download', validation_type='nonanonymous user')
def load_zip_of_prj_files(project_ids):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path

    # Build a list of ProjectSO objects for each of the selected projects, 
    # saving each of them in separate .prj files.
    prjs = [load_project_record(id).save_as_file(dirname) for id in project_ids]
    
    # Make the zip file name and the full server file path version of the same..
    zip_fname = '{}.zip'.format(uuid.uuid4())
    server_zip_fname = os.path.join(dirname, zip_fname)
    
    # Create the zip file, putting all of the .prj files in a projects 
    # directory.
    with ZipFile(server_zip_fname, 'w') as zipfile:
        for prj in prjs:
            zipfile.write(os.path.join(dirname, prj), 'projects/{}'.format(prj))
            
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> load_zip_of_prj_files %s" % (server_zip_fname))

    # Return the server file name.
    return server_zip_fname

@register_RPC(validation_type='nonanonymous user')
def create_new_project(user_id):
    """
    Create a new HealthPrior project.
    """
    
    # Load the data path holding the Excel files.
    data_path = hp.HPpath('data')
    
    # Get a unique name for the project to be added.
    new_proj_name = get_unique_name('New project', other_names=None)
    
    # Create the project, loading in the desired spreadsheets.
    proj = hp.Project(name=new_proj_name, 
        burdenfile=data_path + 'ihme-gbd.xlsx', 
        interventionsfile=data_path + 'dcp-data-afg-v1.xlsx')  
    
    # Set the burden population size.
    proj.burden().popsize = 36373.176 # From UN population division 
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> create_new_project %s" % (proj.name))    
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(proj.uid) }
 
@register_RPC(validation_type='nonanonymous user')
def update_project_from_summary(project_summary):
    """
    Given the passed in project summary, update the underlying project 
    accordingly.
    """ 
    
    # Load the project corresponding with this summary.
    proj = load_project(project_summary['project']['id'])
       
    # Use the summary to set the actual project.
    proj.name = project_summary['project']['name']
    
    # Set the modified time to now.
    proj.modified = now_utc()
    
    # Save the changed project to the DataStore.
    save_project(proj)
    
@register_RPC(validation_type='nonanonymous user')    
def copy_project(project_id):
    """
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    """
    
    # Get the Project object for the project to be copied.
    project_record = load_project_record(project_id, raise_exception=True)
    proj = project_record.proj
    
    # Make a copy of the project loaded in to work with.
    new_project = sc.dcp(proj)
    
    # Just change the project name, and we have the new version of the 
    # Project object to be saved as a copy.
    new_project.name = get_unique_name(proj.name, other_names=None)
    
    # Set the user UID for the new projects record to be the current user.
    user_id = current_user.get_id() 
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> copy_project %s" % (new_project.name)) 
    
    # Save a DataStore projects record for the copy project.
    save_project_as_new(new_project, user_id)
    
    # Remember the new project UID (created in save_project_as_new()).
    copy_project_id = new_project.uid

    # Return the UID for the new projects record.
    return { 'projectId': copy_project_id }

@register_RPC(call_type='upload', validation_type='nonanonymous user')
def create_project_from_prj_file(prj_filename, user_id):
    """
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    """
    
    # Display the call information.
    print(">> create_project_from_prj_file '%s'" % prj_filename)
    
    # Try to open the .prj file, and return an error message if this fails.
    try:
        proj = fileio.gzip_string_pickle_file_to_object(prj_filename)
    except Exception:
        return { 'projectId': 'BadFileFormatError' }
    
    # Reset the project name to a new project name that is unique.
    proj.name = get_unique_name(proj.name, other_names=None)
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(proj.uid) }

##
## Burden set RPCs
##  
    
@register_RPC(validation_type='nonanonymous user')     
def get_project_burden_sets(project_id):
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get a list of the Burden objects.
    burdensets = [proj.burdensets[ind] for ind in range(len(proj.burdensets))] 
    
    # Return the JSON-friendly result.
    return {'burdensets': map(get_burden_set_fe_repr, burdensets)}

@register_RPC(validation_type='nonanonymous user')
def get_project_burden_set_diseases(project_id, burdenset_numindex):
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get the burden set that matches burdenset_numindex.
    burdenset = proj.burden(key=burdenset_numindex)
    
    # Return an empty list if no data is present.
    if burdenset.data is None:
        return { 'diseases': [] }

    # Gather the list for all of the diseases.
    disease_data = burdenset.export(cols=['active','cause','dalys','deaths','prevalence'], header=False)
    
    # Return success.
    return { 'diseases': disease_data }

@register_RPC(validation_type='nonanonymous user')    
def create_burden_set(project_id, new_burden_set_name):

    def update_project_fn(proj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        unique_name = get_unique_name(new_burden_set_name, 
            other_names=list(proj.burdensets))
        
        # Create a new (empty) burden set.
        new_burden_set = hp.Burden(project=proj, name=unique_name)
                
        # Load data from the Excel spreadsheet.
        # NOTE: We may want to take this out later in favor leaving the 
        # new sets empty to start.
        data_path = hp.HPpath('data')
        new_burden_set.loaddata(data_path+'ihme-gbd.xlsx')
        
        # Put the new burden set in the dictionary.
        proj.burdensets[unique_name] = new_burden_set
        
    # Do the project update using the internal function.
    update_project_with_fn(project_id, update_project_fn)

    # Return the new burden sets.
    return get_project_burden_sets(project_id)

@register_RPC(validation_type='nonanonymous user')
def delete_burden_set(project_id, burdenset_numindex):

    def update_project_fn(proj):
        proj.burdensets.pop(burdenset_numindex)
        
    # Do the project update using the internal function.    
    update_project_with_fn(project_id, update_project_fn)   

@register_RPC(validation_type='nonanonymous user')    
def copy_burden_set(project_id, burdenset_numindex):

    def update_project_fn(proj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        unique_name = get_unique_name(proj.burdensets[burdenset_numindex].name, 
            other_names=list(proj.burdensets))
        
        # Create a new burdenset which is a copy of the old one.
        new_burden_set = sc.dcp(proj.burdensets[burdenset_numindex])
        
        # Overwrite the old name with the new.
        new_burden_set.name = unique_name
       
        # Put the new burden set in the dictionary.
        proj.burdensets[unique_name] = new_burden_set
        
    # Do the project update using the internal function.  
    update_project_with_fn(project_id, update_project_fn)
    
    # Return the new burden sets.
    return get_project_burden_sets(project_id) 

@register_RPC(validation_type='nonanonymous user')
def rename_burden_set(project_id, burdenset_numindex, new_burden_set_name):

    def update_project_fn(proj):
        # Overwrite the old name with the new.
        proj.burdensets[burdenset_numindex].name = new_burden_set_name
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)

@register_RPC(validation_type='nonanonymous user')
def update_burden_set_disease(project_id, burdenset_numindex, 
    disease_numindex, data):

    def update_project_fn(proj):
        # Set the data records for what gets passed in.
        data_record = proj.burdensets[burdenset_numindex].data[disease_numindex]
        data_record[0] = data[0]
        data_record[7] = data[1]
        data_record[8] = data[2]
        data_record[9] = data[3]
        data_record[10] = data[4]
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)




# TODO: move this into the helper functions.  It's here now for testing 
# purposes.  Or, maybe remove dependency on this entirely, since it's a one-
# liner.
def make_mpld3_graph_dict(fig):
    mpld3_dict = mpld3.fig_to_dict(fig)
    return mpld3_dict

@register_RPC(validation_type='nonanonymous user')
def get_project_burden_plots(project_id, burdenset_numindex, engine='matplotlib'):
    ''' Plot the disease burden '''
    
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get the burden set that matches burdenset_numindex.
    burdenset = proj.burden(key=burdenset_numindex)
    
    figs = []
    for which in ['dalys','deaths','prevalence']:        
        fig = burdenset.plottopcauses(which=which) # Create the figure
        figs.append(fig)
    
    # Gather the list for all of the diseases.
    graphs = []
    for fig in figs:
        graph_dict = make_mpld3_graph_dict(fig)
        graphs.append(graph_dict)
    
    # Return success -- WARNING, hard-coded to 3 graphs!
    return {'graph1': graphs[0],
            'graph2': graphs[1],
            'graph3': graphs[2],}
    
##
## Intervention set RPCs
## 

@register_RPC(validation_type='nonanonymous user')    
def get_project_interv_sets(project_id):
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get a list of the Interventions objects.
    interv_sets = [proj.intersets[ind] for ind in range(len(proj.intersets))] 
    
    # Return the JSON-friendly result.
    return {'intervsets': map(get_interv_set_fe_repr, interv_sets)}

@register_RPC(validation_type='nonanonymous user')
def get_project_interv_set_intervs(project_id, intervset_numindex):
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get the intervention set that matches intervset_numindex.
    intervset = proj.inter(key=intervset_numindex)
    
    # Return an empty list if no data is present.
    if intervset.data is None:
        return { 'interventions': [] } 
    
    # Gather the list for all of the interventions.
    interv_data = [list(interv) for interv in intervset.data]
    
    # Return success.
    return { 'interventions': interv_data }

@register_RPC(validation_type='nonanonymous user')
def create_interv_set(project_id, new_interv_set_name):

    def update_project_fn(proj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        unique_name = get_unique_name(new_interv_set_name, 
            other_names=list(proj.intersets))
        
        # Create a new (empty) intervention set.
        new_intervset = hp.Interventions(project=proj, name=unique_name)
        
        # Load data from the Excel spreadsheet.
        # NOTE: We may want to take this out later in favor leaving the 
        # new sets empty to start.
        data_path = hp.HPpath('data')
        new_intervset.loaddata(data_path+'dcp-data-afg-v1.xlsx')
        
        # Put the new intervention set in the dictionary.
        proj.intersets[unique_name] = new_intervset
        
    # Do the project update using the internal function.
    update_project_with_fn(project_id, update_project_fn)

    # Return the new intervention sets.
    return get_project_interv_sets(project_id)

@register_RPC(validation_type='nonanonymous user')
def delete_interv_set(project_id, intervset_numindex):

    def update_project_fn(proj):
        proj.intersets.pop(intervset_numindex)
        
    # Do the project update using the internal function.    
    update_project_with_fn(project_id, update_project_fn)   

@register_RPC(validation_type='nonanonymous user')    
def copy_interv_set(project_id, intervset_numindex):

    def update_project_fn(proj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        unique_name = get_unique_name(proj.intersets[intervset_numindex].name, 
            other_names=list(proj.intersets))
        
        # Create a new intervention set which is a copy of the old one.
        new_intervset = sc.dcp(proj.intersets[intervset_numindex])
        
        # Overwrite the old name with the new.
        new_intervset.name = unique_name
       
        # Put the new intervention set in the dictionary.
        proj.intersets[unique_name] = new_intervset
        
    # Do the project update using the internal function.  
    update_project_with_fn(project_id, update_project_fn)
    
    # Return the new intervention sets.
    return get_project_interv_sets(project_id)

@register_RPC(validation_type='nonanonymous user')
def rename_interv_set(project_id, intervset_numindex, new_interv_set_name):

    def update_project_fn(proj):
        # Overwrite the old name with the new.
        proj.intersets[intervset_numindex].name = new_interv_set_name
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)

@register_RPC(validation_type='nonanonymous user')    
def update_interv_set_interv(project_id, intervset_numindex, 
    interv_numindex, data):

    def update_project_fn(proj):
        # Set the data records for what gets passed in.
        data_record = proj.intersets[intervset_numindex].data[interv_numindex]
        data_record[0] = data[0]
        data_record[1] = data[1]
        data_record[3] = data[2]
        data_record[4] = data[3]
        data_record[5] = data[4]
        data_record[6] = data[5]
        data_record[7] = data[6]
        data_record[8] = data[7]
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)

##
## Package set RPCs
##   

@register_RPC(validation_type='nonanonymous user')    
def get_project_package_sets(project_id):
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get a list of the package objects.
    packagesets = [proj.packagesets[ind] for ind in range(len(proj.packagesets))] 
    
    # Return the JSON-friendly result.
    return {'packagesets': map(get_package_set_fe_repr, packagesets)}

@register_RPC(validation_type='nonanonymous user')
def get_project_package_set_results(project_id, packageset_numindex):
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get the package set that matches packageset_numindex.
    packageset = proj.package(key=packageset_numindex)
    
    # Return an empty list if no data is present.
    if packageset.results is None:
        return { 'results': [] }

    # Gather the list for all of the diseases.
    result_data = packageset.export(cols=['active','shortname','cause','coverage','dalys_averted'], header=False)
    
    # Return success.
    return { 'results': result_data }

@register_RPC(validation_type='nonanonymous user')    
def create_package_set(project_id, new_package_set_name):

    def update_project_fn(proj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        unique_name = get_unique_name(new_package_set_name, 
            other_names=list(proj.packagesets))
        
        # Create a new (empty) package set.
        new_packageset = hp.HealthPackage(project=proj, name=unique_name)
        
        # Put the new package set in the dictionary.
        proj.packagesets[unique_name] = new_packageset
        
    # Do the project update using the internal function.
    update_project_with_fn(project_id, update_project_fn)

    # Return the new package sets.
    return get_project_package_sets(project_id)

@register_RPC(validation_type='nonanonymous user')
def delete_package_set(project_id, packageset_numindex):

    def update_project_fn(proj):
        proj.packagesets.pop(packageset_numindex)
        
    # Do the project update using the internal function.    
    update_project_with_fn(project_id, update_project_fn)   

@register_RPC(validation_type='nonanonymous user')    
def copy_package_set(project_id, packageset_numindex):

    def update_project_fn(proj):
        # Get a unique name (just in case the one provided collides with an 
        # existing one).
        unique_name = get_unique_name(proj.packagesets[packageset_numindex].name, 
            other_names=list(proj.packagesets))
        
        # Create a new packageset which is a copy of the old one.
        new_packageset = sc.dcp(proj.packagesets[packageset_numindex])
        
        # Overwrite the old name with the new.
        new_packageset.name = unique_name
       
        # Put the new package set in the dictionary.
        proj.packagesets[unique_name] = new_packageset
        
    # Do the project update using the internal function.  
    update_project_with_fn(project_id, update_project_fn)
    
    # Return the new package sets.
    return get_project_package_sets(project_id) 

@register_RPC(validation_type='nonanonymous user')
def rename_package_set(project_id, packageset_numindex, new_package_set_name):

    def update_project_fn(proj):
        # Overwrite the old name with the new.
        proj.packagesets[packageset_numindex].name = new_package_set_name
        
    # Do the project update using the internal function. 
    update_project_with_fn(project_id, update_project_fn)

@register_RPC(validation_type='nonanonymous user')
def get_project_package_plots(project_id, packageset_numindex):
    ''' Plot the health packages '''
    
    # Get the Project object.
    proj = load_project(project_id)
    
    # Get the package set that matches packageset_numindex.
    packageset = proj.package(key=packageset_numindex)
    
    figs = []
    fig1 = packageset.plot_dalys()
    fig2 = packageset.plot_cascade()
    figs.append(fig1)
    figs.append(fig2)
    
    # Gather the list for all of the diseases.
    graphs = []
    for fig in figs:
        graph_dict = make_mpld3_graph_dict(fig)
        graphs.append(graph_dict)
    
    # Return success -- WARNING, should not be hard-coded!
    return {'graph1': graphs[0],
            'graph2': graphs[1],}