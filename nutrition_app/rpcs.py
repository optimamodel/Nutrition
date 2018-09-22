"""
Optima Nutrition remote procedure calls (RPCs)
    
Last update: 2018sep20 by cliffk
"""

###############################################################
### Imports
##############################################################

import os
import numpy as np
import sciris as sc
import scirisweb as sw
import nutrition.ui as nu
from . import config
from matplotlib.pyplot import rc
rc('font', size=12)

# Globals
RPC_dict = {} # Dictionary to hold all of the registered RPCs in this module.
RPC = sw.makeRPCtag(RPC_dict) # RPC registration decorator factory created using call to make_RPC().
datastore = None


###############################################################
### Helper functions
##############################################################

def get_path(filename=None, username=None):
    if filename is None: filename = ''
    base_dir = sw.flaskapp.datastore.tempfolder
    user_id = str(get_user(username).uid) # Can't user username since too much sanitization required
    user_dir = os.path.join(base_dir, user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    fullpath = os.path.join(user_dir, filename) # Generate the full file name with path.
    return fullpath


def sanitize(vals, skip=False, forcefloat=False, verbose=False, as_nan=False, die=True):
    ''' Make sure values are numeric, and either return nans or skip vals that aren't -- WARNING, duplicates lots of other things!'''
    if verbose: print('Sanitizing vals of %s: %s' % (type(vals), vals))
    if as_nan: missingval = np.nan
    else:      missingval = None
    
    if not sc.isstring(vals) and sc.isiterable(vals):
        as_array = False if forcefloat else True
    else:
        vals = [vals]
        as_array = False
    output = []
    for val in vals:
        if val=='':
            sanival = missingval
        elif val==None:
            sanival = missingval
        else:
            try:
                factor = 1.0
                if sc.isstring(val):
                    val = val.replace(',','') # Remove commas, if present
                    val = val.replace('$','') # Remove dollars, if present
                    # if val.endswith('%'): factor = 0.01 # Scale if percentage has been used -- CK: not used since already converted from percentage
                sanival = float(val)*factor
            except Exception as E:
                errormsg = 'Could not sanitize value "%s": %s' % (val, str(E))
                if die: raise Exception(errormsg)
                else:   print(errormsg+'; returning %s' % missingval)
                sanival = missingval
        if not skip or (sanival is not None and not np.isnan(sanival)):
            output.append(sanival)
    if as_array:
        return output
    else:
        return output[0]


@RPC()
def get_version_info():
	''' Return the information about the project. '''
	gitinfo = sc.gitinfo(__file__)
	version_info = {
	       'version':   nu.version,
	       'date':      nu.versiondate,
	       'gitbranch': gitinfo['branch'],
	       'githash':   gitinfo['hash'],
	       'gitdate':   gitinfo['date'],
	}
	return version_info
      

def get_user(username=None):
    ''' Ensure it's a valid Optima Nutrition user '''
    user = datastore.loaduser(username)
    dosave = False
    if not hasattr(user, 'projects'):
        user.projects = []
        dosave = True
    if dosave:
        datastore.saveuser(user)
    return user


def find_datastore():
    ''' Ensure the datastore is loaded '''
    global datastore
    if datastore is None:
        datastore = sw.get_datastore(config=config)
    return datastore # So can be used externally

find_datastore() # Run this on load


##################################################################################
### Convenience functions -- WARNING, make these more symmetric
##################################################################################
    
def load_project(project_key, die=None):
    output = datastore.loadblob(project_key, objtype='project', die=die)
    return output

def load_result(result_key, die=None):
    output = datastore.loadblob(result_key, objtype='result', die=die)
    return output

def save_project(project, die=None): # NB, only for saving an existing project
    project.modified = sc.now()
    output = datastore.saveblob(obj=project, objtype='project', die=die)
    return output

def save_new_project(proj, username=None):
    """
    If we're creating a new project, we need to do some operations on it to
    make sure it's valid for the webapp.
    """ 
    # Preliminaries
    new_project = sc.dcp(proj) # Copy the project, only save what we want...
    new_project.uid = sc.uuid()
    
    # Get unique name
    user = get_user(username)
    current_project_names = []
    for project_key in user.projects:
        proj = load_project(project_key)
        current_project_names.append(proj.name)
    new_project_name = sc.uniquename(new_project.name, namelist=current_project_names)
    new_project.name = new_project_name
    
    # Ensure it's a valid webapp project
    if not hasattr(new_project, 'webapp'):
        new_project.webapp = sc.prettyobj()
        new_project.webapp.username = username
        new_project.webapp.tasks = []
    
    # Save all the things
    key = save_project(new_project)
    user.projects.append(key)
    datastore.saveuser(user)
    return key,new_project


def save_result(result, die=None):
    output = datastore.saveblob(obj=result, objtype='result', die=die)
    return output


def del_project(project_key, die=None):
    key = datastore.getkey(key=project_key, objtype='project')
    project = load_project(key)
    user = get_user(project.webapp.username)
    output = datastore.delete(key)
    if key in user.projects:
        user.projects.remove(key)
    else:
        print('Warning: deleting project %s (%s), but not found in user "%s" projects' % (project.name, key, user.username))
    datastore.saveuser(user)
    return output


@RPC()
def delete_projects(project_keys):
    ''' Delete one or more projects '''
    project_keys = sc.promotetolist(project_keys)
    for project_key in project_keys:
        del_project(project_key)
    return None



##################################################################################
### Project RPCs
##################################################################################

@RPC()
def project_json(project_id, verbose=False):
    """ Return the project json, given the Project UID. """ 
    proj = load_project(project_id) # Load the project record matching the UID of the project passed in.
    json = {
        'project': {
            'id':           proj.uid,
            'name':         proj.name,
            'username':     proj.webapp.username,
            'hasData':      len(proj.datasets)>0,
            'creationTime': proj.created,
            'updatedTime':  proj.modified,
            'n_results':    len(proj.results),
            'n_tasks':      len(proj.webapp.tasks)
        }
    }
    if verbose: sc.pp(json)
    return json
    

@RPC()
def project_jsons(username, verbose=False):
    """ Return project jsons for all projects the user has to the client. """ 
    output = {'projects':[]}
    user = get_user(username)
    for project_key in user.projects:
        json = project_json(project_key)
        output['projects'].append(json)
    if verbose: sc.pp(output)
    return output


@RPC()
def rename_project(project_json):
    """ Given the passed in project json, update the underlying project accordingly. """ 
    proj = load_project(project_json['project']['id']) # Load the project corresponding with this json.
    proj.name = project_json['project']['name'] # Use the json to set the actual project.
    proj.modified = sc.now() # Set the modified time to now.
    save_project(proj) # Save the changed project to the DataStore.
    return None


@RPC()
def add_demo_project(username):
    """ Add a demo Optima Nutrition project """
    proj = nu.demo(scens=True, optims=True)  # Create the project, loading in the desired spreadsheets.
    proj.name = 'Demo project'
    print(">> add_demo_project %s" % (proj.name)) # Display the call information.
    key,proj = save_new_project(proj, username) # Save the new project in the DataStore.
    return {'projectID': str(proj.uid)} # Return the new project UID in the return message.


@RPC(call_type='download')
def create_new_project(username, proj_name, *args, **kwargs):
    """ Create a new Optima Nutrition project. """
    proj = nu.Project(name=proj_name) # Create the project
    print(">> create_new_project %s" % (proj.name))     # Display the call information.
    key,proj = save_new_project(proj, username) # Save the new project in the DataStore.
    file_name = '%s databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username)
    proj.input_sheet.save(full_file_name)
    print(">> download_databook %s" % (full_file_name))
    return full_file_name

    
@RPC()
def copy_project(project_key):
    """
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    """
    proj = load_project(project_key, die=True) # Get the Project object for the project to be copied.
    new_project = sc.dcp(proj) # Make a copy of the project loaded in to work with.
    print(">> copy_project %s" % (new_project.name))  # Display the call information.
    key,new_project = save_new_project(new_project, proj.webapp.username) # Save a DataStore projects record for the copy project.
    copy_project_id = new_project.uid # Remember the new project UID (created in save_project_as_new()).
    return { 'projectId': copy_project_id } # Return the UID for the new projects record.



##################################################################################
### Upload/download RPCs
##################################################################################

@RPC(call_type='upload')
def upload_project(prj_filename, username):
    """
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    """
    print(">> create_project_from_prj_file '%s'" % prj_filename) # Display the call information.
    try: # Try to open the .prj file, and return an error message if this fails.
        proj = sc.loadobj(prj_filename)
    except Exception:
        return { 'error': 'BadFileFormatError' }
    key,proj = save_new_project(proj, username) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='download')   
def download_project(project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s.prj' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    sc.saveobj(full_file_name, proj) # Write the object to a Gzip string pickle file.
    print(">> download_project %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def download_projects(project_keys, username):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    basedir = get_path('', username) # Use the downloads directory to put the file in.
    project_paths = []
    for project_key in project_keys:
        proj = load_project(project_key)
        project_path = proj.save(folder=basedir)
        project_paths.append(project_path)
    zip_fname = 'Projects %s.zip' % sc.getdate() # Make the zip file name and the full server file path version of the same..
    server_zip_fname = get_path(zip_fname, username)
    sc.savezip(server_zip_fname, project_paths)
    print(">> load_zip_of_prj_files %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.


@RPC(call_type='download')   
def download_databook(project_id, key=None):
    """ Download databook """
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s_databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    proj.input_sheet.save(full_file_name)
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_defaults(project_id):
    """
    Download defaults
    """
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s_defaults.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    proj.defaults_sheet.save(full_file_name)
    print(">> download_defaults %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='upload')
def upload_databook(databook_filename, project_id):
    """ Upload a databook to a project. """
    print(">> upload_databook '%s'" % databook_filename)
    proj = load_project(project_id, die=True)
    proj.load_data(inputspath=databook_filename) # Reset the project name to a new project name that is unique.
    proj.modified = sc.now()
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='upload')
def upload_defaults(defaults_filename, project_id):
    """ Upload a databook to a project. """
    print(">> upload_databook '%s'" % defaults_filename)
    proj = load_project(project_id, die=True)
    try:
        proj.load_data(defaultspath=defaults_filename) # Reset the project name to a new project name that is unique.
    except Exception as E:
        print('Defaults uploaded, but data not loaded (probably since inputs have not been uploaded yet): %s' % str(E))
    proj.modified = sc.now()
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.



##################################################################################
### Input functions and RPCs
##################################################################################

def define_formats():
    ''' Hard-coded sheet formats '''
    formats = sc.odict()
    
    formats['Nutritional status distribution'] = [
        ['head', 'head', 'name', 'name', 'name', 'name', 'name', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['name', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['name', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['name', 'blnk', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit'],
        ['blnk', 'name', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc'],
    ]
    
    formats['Breastfeeding distribution'] = [
        ['head', 'head', 'head', 'head', 'head', 'head', 'head'],
        ['name', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
    ]
    
    # These are for when we get formulas working
#    formats['Nutritional status distribution'] = [
#        ['head', 'head', 'name', 'name', 'name', 'name', 'name', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['name', 'name', 'calc', 'calc', 'calc', 'calc', 'calc', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'name', 'calc', 'calc', 'calc', 'calc', 'calc', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['name', 'name', 'calc', 'calc', 'calc', 'calc', 'calc', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'name', 'calc', 'calc', 'calc', 'calc', 'calc', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
#        ['name', 'blnk', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name', 'name'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit', 'edit'],
#        ['blnk', 'name', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc', 'calc'],
#    ]
#    
#    formats['Breastfeeding distribution'] = [
#        ['head', 'head', 'head', 'head', 'head', 'head', 'head'],
#        ['name', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
#        ['blnk', 'name', 'edit', 'edit', 'edit', 'edit', 'edit'],
#        ['blnk', 'name', 'calc', 'calc', 'calc', 'calc', 'calc'],
#    ]
    
    formats['IYCF packages'] = [
        ['head', 'head', 'head', 'head', 'head'],
        ['head', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'blnk', 'blnk', 'tick'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['head', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'blnk', 'blnk', 'tick'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['head', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'tick', 'tick', 'blnk'],
        ['blnk', 'name', 'blnk', 'blnk', 'tick'],
    ]
    
    formats['Treatment of SAM'] = [
        ['blnk', 'head', 'head', 'head'],
        ['head', 'name', 'name', 'tick'],
        ['head', 'name', 'name', 'tick'],
    ]
    
    formats['Programs cost and coverage'] = [
        ['head', 'head', 'head', 'head'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'calc'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'calc'],
        ['name', 'edit', 'edit', 'calc'],
        ['name', 'edit', 'edit', 'calc'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'calc'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
        ['name', 'edit', 'edit', 'edit'],
    ]
    
    return formats
    

@RPC()
def get_sheet_data(project_id, key=None):
    sheets = [
        'Nutritional status distribution', 
        'Breastfeeding distribution',
        'IYCF packages',
        'Treatment of SAM',
        'Programs cost and coverage',
        ]
    proj = load_project(project_id, die=True)
    wb = proj.input_sheet
    sheetdata = sc.odict()
    for sheet in sheets:
        sheetdata[sheet] = wb.readcells(sheetname=sheet, header=False)
    sheetformat = define_formats()
    
    sheetjson = sc.odict()
    for sheet in sheets:
        datashape = np.shape(sheetdata[sheet])
        formatshape = np.shape(sheetformat[sheet])
        if datashape != formatshape:
            errormsg = 'Sheet data and formats have different shapes: %s vs. %s' % (datashape, formatshape)
            raise Exception(errormsg)
        rows,cols = datashape
        sheetjson[sheet] = []
        for r in range(rows):
            sheetjson[sheet].append([])
            for c in range(cols):
                cellformat = sheetformat[sheet][r][c]
                cellval = sheetdata[sheet][r][c]
                if sc.isnumber(cellval):
                    cellval = sc.sigfig(cellval, sigfigs=3, sep=',')
                cellinfo = {'format':cellformat, 'value':cellval}
                sheetjson[sheet][r].append(cellinfo)
    
    sheetjson = sc.sanitizejson(sheetjson)
    return {'names':sheets, 'tables':sheetjson}


@RPC()
def save_sheet_data(project_id, sheetdata, key=None):
    proj = load_project(project_id, die=True)
    if key is None: key = proj.datasets.keys()[-1] # There should always be at least one
    wb = proj.input_sheet # CK: Warning, might want to change
    for sheet in sheetdata.keys():
        datashape = np.shape(sheetdata[sheet])
        rows,cols = datashape
        cells = []
        vals = []
        for r in range(rows):
            for c in range(cols):
                cellformat = sheetdata[sheet][r][c]['format']
                if cellformat == 'edit':
                    cellval    = sheetdata[sheet][r][c]['value']
                    try:    cellval = float(cellval)
                    except: cellval = str(cellval)
                    cells.append([r+1,c+1]) # Excel uses 1-based indexing
                    vals.append(cellval)
        wb.writecells(sheetname=sheet, cells=cells, vals=vals, verbose=False, wbargs={'data_only':True}) # Can turn on verbose
    proj.dataset(key).load(project=proj, fromfile=False)
    proj.add_model(key) # Refresh the model
    
    print('Saving project...')
    save_project(proj)
    return None

##################################################################################
### Scenario functions and RPCs
##################################################################################

def is_included(prog_set, program, default_included):
    if (program.name in prog_set) or (program.base_cov and default_included):
        answer = True
    else: 
        answer = False
    return answer
    

def py_to_js_scen(py_scen, proj, key=None, default_included=False):
    ''' Convert a Python to JSON representation of a scenario '''
    prog_names = proj.dataset().prog_names()
    settings = nu.Settings()
    scen_years = settings.n_years - 1 # First year is baseline
    attrs = ['name', 'active', 'scen_type']
    js_scen = {}
    for attr in attrs:
        js_scen[attr] = getattr(py_scen, attr) # Copy the attributes into a dictionary
    js_scen['progvals'] = []
    count = -1
    for prog_name in prog_names:
        program = proj.model(key).prog_info.programs[prog_name]
        this_spec = {}
        this_spec['name'] = prog_name
        this_spec['included'] = is_included(py_scen.prog_set, program, default_included)
        this_spec['vals'] = []
        
        # Calculate values
        if this_spec['included']:
            count += 1
            try:
                this_spec['vals'] = py_scen.vals[count]
            except:
                this_spec['vals'] = [None]
            while len(this_spec['vals']) < scen_years: # Ensure it's the right length
                this_spec['vals'].append(None)
        else:
            this_spec['vals'] = [None]*scen_years # WARNING, kludgy way to extract the number of years
        
        # Add formatting
        for y in range(len(this_spec['vals'])):
            if this_spec['vals'][y] is not None:
                if js_scen['scen_type'] == 'coverage': # Convert to percentage
                    this_spec['vals'][y] = str(round(100*this_spec['vals'][y])) # Enter to the nearest percentage
                elif js_scen['scen_type'] == 'budget': # Add commas
                    this_spec['vals'][y] = format(int(round(this_spec['vals'][y])), ',') # Add commas
        this_spec['base_cov'] = str(round(program.base_cov*100)) # Convert to percentage
        this_spec['base_spend'] = format(int(round(program.base_spend)), ',')
        js_scen['progvals'].append(this_spec)
        js_scen['t'] = [settings.t[0]+1, settings.t[1]] # First year is baseline year
    return js_scen
    
    
def js_to_py_scen(js_scen):
    ''' Convert a JSON to Python representation of a scenario '''
    py_json = sc.odict()
    for attr in ['name', 'scen_type', 'active']: # Copy these directly
        py_json[attr] = js_scen[attr]
    py_json['progvals'] = sc.odict() # These require more TLC
    for js_spec in js_scen['progvals']:
        if js_spec['included']:
            py_json['progvals'][js_spec['name']] = []
            vals = list(sanitize(js_spec['vals'], skip=True))
            for y in range(len(vals)):
                if js_scen['scen_type'] == 'coverage': # Convert from percentage
                        if vals[y] is not None:
                            vals[y] = vals[y]/100. # Convert from percentage
            py_json['progvals'][js_spec['name']] += vals
    return py_json
    

@RPC()
def get_scen_info(project_id, key=None):
    print('Getting scenario info...')
    proj = load_project(project_id, die=True)
    scenario_jsons = []
    for py_scen in proj.scens.values():
        js_scen = py_to_js_scen(py_scen, proj, key=key)
        scenario_jsons.append(js_scen)
    print('JavaScript scenario info:')
    sc.pp(scenario_jsons)

    return scenario_jsons


@RPC()
def set_scen_info(project_id, scenario_jsons):
    print('Setting scenario info...')
    proj = load_project(project_id, die=True)
    proj.scens.clear()
    for j,js_scen in enumerate(scenario_jsons):
        print('Setting scenario %s of %s...' % (j+1, len(scenario_jsons)))
        json = js_to_py_scen(js_scen)
        proj.add_scen(json=json)
        print('Python scenario info for scenario %s:' % (j+1))
        sc.pp(json)
        
    print('Saving project...')
    save_project(proj)
    return None


@RPC()
def get_default_scen(project_id, scen_type=None):
    print('Creating default scenario...')
    if scen_type is None: scen_type = 'coverage'
    proj = load_project(project_id, die=True)
    py_scens = proj.demo_scens(doadd=False)
    if scen_type == 'coverage': py_scen = py_scens[0] # Pull out the first one
    else:                       py_scen = py_scens[1] # Pull out the second one
    py_scen.scen_type = scen_type # Set the scenario type
    js_scen = py_to_js_scen(py_scen, proj, default_included=True)
    print('Created default JavaScript scenario:')
    sc.pp(js_scen)
    return js_scen


def reformat_costeff(costeff):
    ''' Changes the format from an odict to something jsonifiable '''
    outcomekeys = costeff[0][0].keys()
    emptycols = ['']*len(outcomekeys)
    table = []
    for i,scenkey,val1 in costeff.enumitems():
        for j,progkey,val2 in val1.enumitems():
            if j==0: 
                if i>0: table.append(['', '']+emptycols) # Blank row
                table.append(['header', scenkey]+emptycols) # e.g. ['header', 'Wasting example', '', '', '']
                table.append(['keys', 'Programs']+outcomekeys)      # e.g. ['keys', '', 'Number anaemic', 'Number dead', ...]
            table.append(['entry', progkey]+val2.values())  # e.g. ['entry', 'IYCF', '$23,348 per death', 'No impact', ...]
    return table

@RPC()
def run_scens(project_id, doplot=True):
    
    print('Running scenarios...')
    proj = load_project(project_id, die=True)
    proj.run_scens()
    
    # Get graphs
    graphs = []
    if doplot:
        figs = proj.plot('scens')
        for f,fig in enumerate(figs.values()):
            for ax in fig.get_axes():
                ax.set_facecolor('none')
            graph_dict = sw.mpld3ify(fig, jsonify=False)
            graphs.append(graph_dict)
            print('Converted figure %s of %s' % (f+1, len(figs)))
        
    # Get cost-effectiveness table
    costeff = nu.get_costeff(project=proj, results=proj.result('scens'))
    table = reformat_costeff(costeff)
    
    # Store results in cache
    proj = cache_results(proj)
    
    print('Saving project...')
    save_project(proj)
    output = {'graphs':graphs, 'table':table}
    return output




##################################################################################
### Optimization functions and RPCs
##################################################################################


def py_to_js_optim(py_optim, proj, key=None, default_included=False):
    ''' Convert a Python to JSON representation of an optimization '''
    obj_labels = nu.pretty_labels(direction=True).values()
    prog_names = proj.dataset().prog_names()
    js_optim = {}
    attrs = ['name', 'model_name', 'mults', 'add_funds', 'fix_curr', 'filter_progs']
    for attr in attrs:
        js_optim[attr] = getattr(py_optim, attr) # Copy the attributes into a dictionary
    weightslist = [{'label':item[0], 'weight':abs(item[1])} for item in zip(obj_labels, py_optim.weights)] # WARNING, ABS HACK
    js_optim['weightslist'] = weightslist
    js_optim['spec'] = []
    for prog_name in prog_names:
        program = proj.model(key).prog_info.programs[prog_name]
        this_spec = {}
        this_spec['name'] = prog_name
        this_spec['included'] = is_included(py_optim.prog_set, program, default_included)
        js_optim['spec'].append(this_spec)
    js_optim['objective_options'] = obj_labels # Not modified but used on the FE
    return js_optim
    
    
def js_to_py_optim(js_optim):
    ''' Convert a JSON to Python representation of an optimization '''
    obj_keys = nu.default_trackers()
    json = sc.odict()
    attrs = ['name', 'model_name', 'fix_curr', 'filter_progs']
    for attr in attrs:
        json[attr] = js_optim[attr]
    try:
        json['weights'] = sc.odict()
        for key,item in zip(obj_keys,js_optim['weightslist']):
            val = sanitize(item['weight'])
            json['weights'][key] = val
    except Exception as E:
        print('Unable to convert "%s" to weights' % js_optim['weightslist'])
        raise E
    jsm = js_optim['mults']
    if not jsm: jsm = 1.0
    if sc.isstring(jsm):
        jsm = jsm.split(',')
    vals = sanitize(jsm, die=True)
    json['mults'] = vals
    json['add_funds'] = sanitize(js_optim['add_funds'], forcefloat=True)
    json['prog_set'] = [] # These require more TLC
    for js_spec in js_optim['spec']:
        if js_spec['included']:
            json['prog_set'].append(js_spec['name'])  
    return json
    

@RPC()
def get_optim_info(project_id):
    print('Getting optimization info...')
    proj = load_project(project_id, die=True)
    optim_jsons = []
    for py_optim in proj.optims.values():
        js_optim = py_to_js_optim(py_optim, proj)
        optim_jsons.append(js_optim)
    print('JavaScript optimization info:')
    sc.pp(optim_jsons)
    return optim_jsons


@RPC()
def set_optim_info(project_id, optim_jsons):
    print('Setting optimization info...')
    proj = load_project(project_id, die=True)
    proj.optims.clear()
    for j,js_optim in enumerate(optim_jsons):
        print('Setting optimization %s of %s...' % (j+1, len(optim_jsons)))
        json = js_to_py_optim(js_optim)
        print('Python optimization info for optimization %s:' % (j+1))
        print(json)
        proj.add_optim(json=json)
    print('Saving project...')
    save_project(proj)   
    return None
    

@RPC()
def get_default_optim(project_id):
    print('Getting default optimization...')
    proj = load_project(project_id, die=True)
    py_optim = proj.demo_optims(doadd=False)[0]
    js_optim = py_to_js_optim(py_optim, proj, default_included=True)
    print('Created default JavaScript optimization:')
    sc.pp(js_optim)
    return js_optim


@RPC()
def plot_optimization(project_id, cache_id):
    proj = load_project(project_id, die=True)
    proj = retrieve_results(proj)
    figs = proj.plot(key=cache_id, optim=True) # Only plot allocation
    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = sw.mpld3ify(fig, jsonify=False)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    
    # Get cost-effectiveness table
    costeff = nu.get_costeff(project=proj, results=proj.result(cache_id))
    table = reformat_costeff(costeff)
    
    return {'graphs':graphs, 'table':table}





##################################################################################
### Results RPCs
##################################################################################

def cache_results(proj, verbose=True):
    ''' Store the results of the project in Redis '''
    for key,result in proj.results.items():
        if not sc.isstring(result):
            result_key = save_result(result)
            proj.results[key] = result_key
            if verbose: print('Cached result "%s" to "%s"' % (key, result_key))
    save_project(proj)
    return proj


def retrieve_results(proj, verbose=True):
    ''' Retrieve the results from the database back into the project '''
    for key,result_key in proj.results.items():
        if sc.isstring(result_key):
            result = load_result(result_key)
            proj.results[key] = result
            if verbose: print('Retrieved result "%s" from "%s"' % (key, result_key))
    return proj


@RPC(call_type='download')
def export_results(project_id):
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    proj = retrieve_results(proj)
    file_name = '%s outputs.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    proj.write_results(full_file_name, keys=-1)
    print(">> export_results %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def export_graphs(project_id):
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    proj = retrieve_results(proj)
    file_name = '%s graphs.pdf' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    figs = proj.plot(-1) # Generate the plots
    sc.savefigs(figs, filetype='singlepdf', filename=full_file_name)
    print(">> export_graphs %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.

