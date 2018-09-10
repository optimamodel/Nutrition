"""
Optima Nutrition remote procedure calls (RPCs)
    
Last update: 2018aug30 by cliffk
"""

###############################################################
### Imports
##############################################################

import os
from zipfile import ZipFile
from flask_login import current_user
from shutil import copyfile
import mpld3
import numpy as np
import sciris as sc
import scirisweb as sw
import nutrition.ui as nu
from . import projects as prj
from matplotlib.pyplot import rc
rc('font', size=12)

# Globals
RPC_dict = {} # Dictionary to hold all of the registered RPCs in this module.
RPC = sw.makeRPCtag(RPC_dict) # RPC registration decorator factory created using call to make_RPC().

        
###############################################################
### Other functions (mostly helpers for the RPCs)
##############################################################

def to_number(raw):
    ''' Convert something to a number. WARNING, I'm sure this already exists!! '''
    try:
        output = float(raw)
    except Exception as E:
        if raw is None:
            output = None
        else:
            raise E
    return output


def get_path(filename, online=True):
    if online:
        dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
        fullpath = '%s%s%s' % (dirname, os.sep, filename) # Generate the full file name with path.
    else:
        fullpath = filename
    return fullpath


def sanitize(vals, skip=False, forcefloat=False, verbose=True):
    ''' Make sure values are numeric, and either return nans or skip vals that aren't -- WARNING, duplicates lots of other things!'''
    if verbose: print('Sanitizing vals of %s: %s' % (type(vals), vals))
    if sc.isiterable(vals):
        as_array = False if forcefloat else True
    else:
        vals = [vals]
        as_array = False
    output = []
    for val in vals:
        if val=='':
            sanival = np.nan
        elif val==None:
            sanival = np.nan
        else:
            try:
                factor = 1.0
                if sc.isstring(val):
                    val = val.replace(',','') # Remove commas, if present
                    val = val.replace('$','') # Remove dollars, if present
                    # if val.endswith('%'): factor = 0.01 # Scale if percentage has been used -- CK: not used since already converted from percentage
                sanival = float(val)*factor
            except Exception as E:
                print('Could not sanitize value "%s": %s; returning nan' % (val, repr(E)))
                sanival = np.nan
        if not np.isnan(sanival) or not skip:
            output.append(sanival)
    if as_array:
        return output
    else:
        return output[0]
  
      
def load_project_record(project_id, raise_exception=True):
    """ Return the project DataStore reocord, given a project UID. """ 
    project_record = prj.proj_collection.get_object_by_uid(project_id) # Load the matching prj.ProjectSO object from the database.
    if project_record is None: # If we have no match, we may want to throw an exception.
        if raise_exception:
            raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
    return project_record # Return the Project object for the match (None if none found).


def load_project(project_id, raise_exception=True, online=True):
    """
    Return the Nutrition Project object, given a project UID, or None if no 
    ID match is found.
    """ 
    if not online:  return project_id # If running offline, just return the project
    project_record = load_project_record(project_id, raise_exception=raise_exception) # Load the project record matching the ID passed in.
    if project_record is None: # If there is no match, raise an exception or return None.
        if raise_exception: raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
        else:               return None
    return project_record.proj # Return the found project.


def load_project_summary_from_project_record(project_record):
    """ Return the project summary, given the DataStore record. """ 
    return project_record.get_user_front_end_repr() # Return the built project summary.
    
      
def save_project(proj, online=True):
    """
    Given a Project object, wrap it in a new prj.ProjectSO object and put this 
    in the project collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Project.
    """ 
    # If offline, just save to a file and return
    if not online:
        proj.save()
        return None
    
    project_record = load_project_record(proj.uid) # Load the project record matching the UID of the project passed in.
    new_project = sc.dcp(proj) # Copy the project, only save what we want...
    new_project.modified = sc.now()
         
    # Create the new project entry and enter it into the ProjectCollection.
    # Note: We don't need to pass in project.uid as a 3rd argument because 
    # the constructor will automatically use the Project's UID.
    projSO = prj.ProjectSO(new_project, project_record.owner_uid)
    prj.proj_collection.update_object(projSO)
    return None

def save_project_as_new(proj, user_id):
    """
    Given a Project object and a user UID, wrap the Project in a new prj.ProjectSO 
    object and put this in the project collection, after getting a fresh UID
    for this Project.  Then do the actual save.
    """ 
    proj.uid = sc.uuid() # Set a new project UID, so we aren't replicating the UID passed in.
    projSO = prj.ProjectSO(proj, user_id) # Create the new project entry and enter it into the ProjectCollection.
    prj.proj_collection.add_object(projSO)  
    print(">> save_project_as_new '%s'" % proj.name) # Display the call information.
    save_project(proj) # Save the changed Project object to the DataStore.
    return None





##################################################################################
### Project RPCs
##################################################################################

# Not a project RPC, but doesn't really belong
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

    
@RPC()
def get_scirisdemo_projects():
    """ Return the projects associated with the Sciris Demo user. """
    user_id = sw.get_scirisdemo_user() # Get the user UID for the _ScirisDemo user.
    project_entries = prj.proj_collection.get_project_entries_by_user(user_id) # Get the prj.ProjectSO entries matching the _ScirisDemo user UID.
    project_summary_list = map(load_project_summary_from_project_record, project_entries) # Collect the project summaries for that user into a list.
    sorted_summary_list = sorted(project_summary_list, key=lambda proj: proj['project']['name']) # Sorts by project name
    output = {'projects': sorted_summary_list} # Return a dictionary holding the project summaries.
    return output


@RPC()
def load_project_summary(project_id):
    """ Return the project summary, given the Project UID. """ 
    project_entry = load_project_record(project_id) # Load the project record matching the UID of the project passed in.
    return load_project_summary_from_project_record(project_entry) # Return a project summary from the accessed prj.ProjectSO entry.


@RPC()
def load_current_user_project_summaries():
    """ Return project summaries for all projects the user has to the client. """ 
    project_entries = prj.proj_collection.get_project_entries_by_user(current_user.get_id()) # Get the prj.ProjectSO entries matching the user UID.
    return {'projects': map(load_project_summary_from_project_record, project_entries)}# Grab a list of project summaries from the list of prj.ProjectSO objects we just got.


@RPC()
def load_all_project_summaries():
    """ Return project summaries for all projects to the client. """ 
    project_entries = prj.proj_collection.get_all_objects() # Get all of the prj.ProjectSO entries.
    return {'projects': map(load_project_summary_from_project_record, project_entries)} # Grab a list of project summaries from the list of prj.ProjectSO objects we just got.
        
        
@RPC()
def delete_projects(project_ids):
    """ Delete all of the projects with the passed in UIDs. """ 
    for project_id in project_ids: # Loop over the project UIDs of the projects to be deleted...
        record = load_project_record(project_id, raise_exception=True) # Load the project record matching the UID of the project passed in.
        if record is not None: # If a matching record is found, delete the object from the ProjectCollection.
            prj.proj_collection.delete_object_by_uid(project_id)
    return None


@RPC(call_type='download')   
def download_project(project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s.prj' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    sc.saveobj(full_file_name, proj) # Write the object to a Gzip string pickle file.
    print(">> download_project %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_databook(project_id, key=None):
    """ Download databook """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s_databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.input_sheet.save(full_file_name)
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_defaults(project_id):
    """
    Download defaults
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s_defaults.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.dataset().defaults_sheet.save(full_file_name)
    print(">> download_defaults %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def load_zip_of_prj_files(project_ids):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    prjs = [load_project_record(id).save_as_file(dirname) for id in project_ids] # Build a list of prj.ProjectSO objects for each of the selected projects, saving each of them in separate .prj files.
    zip_fname = 'Projects %s.zip' % sc.getdate() # Make the zip file name and the full server file path version of the same..
    server_zip_fname = os.path.join(dirname, sc.sanitizefilename(zip_fname))
    with ZipFile(server_zip_fname, 'w') as zipfile: # Create the zip file, putting all of the .prj files in a projects directory.
        for project in prjs:
            zipfile.write(os.path.join(dirname, project), 'projects/{}'.format(project))
    print(">> load_zip_of_prj_files %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.


@RPC()
def add_demo_project(user_id):
    """ Add a demo Optima Nutrition project """
    new_proj_name = sc.uniquename('Demo project', namelist=None) # Get a unique name for the project to be added.
    proj = nu.demo(scens=True, optims=True)  # Create the project, loading in the desired spreadsheets.
    proj.name = new_proj_name
    print(">> add_demo_project %s" % (proj.name)) # Display the call information.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='download')
def create_new_project(user_id, proj_name):
    """ Create a new Optima Nutrition project. """
    template_name = 'template_input.xlsx'
    new_proj_name = sc.uniquename(proj_name, namelist=None) # Get a unique name for the project to be added.
    proj = nu.Project(name=new_proj_name) # Create the project
    print(">> create_new_project %s" % (proj.name))     # Display the call information.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    databook_path = sc.makefilepath(filename=template_name, folder=nu.ONpath('applications'))
    file_name = '%s databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name)
    copyfile(databook_path, full_file_name)
    print(">> download_databook %s" % (full_file_name))
    return full_file_name


@RPC(call_type='upload')
def upload_databook(databook_filename, project_id):
    """ Upload a databook to a project. """
    print(">> upload_databook '%s'" % databook_filename)
    proj = load_project(project_id, raise_exception=True)
    proj.load_data(filepath=databook_filename) # Reset the project name to a new project name that is unique.
    proj.modified = sc.now()
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC()
def update_project_from_summary(project_summary):
    """ Given the passed in project summary, update the underlying project accordingly. """ 
    proj = load_project(project_summary['project']['id']) # Load the project corresponding with this summary.
    proj.name = project_summary['project']['name'] # Use the summary to set the actual project.
    proj.modified = sc.now() # Set the modified time to now.
    save_project(proj) # Save the changed project to the DataStore.
    return None
    
@RPC()
def copy_project(project_id):
    """
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    """
    project_record = load_project_record(project_id, raise_exception=True) # Get the Project object for the project to be copied.
    proj = project_record.proj
    new_project = sc.dcp(proj) # Make a copy of the project loaded in to work with.
    new_project.name = sc.uniquename(proj.name, namelist=None) # Just change the project name, and we have the new version of the Project object to be saved as a copy.
    user_id = current_user.get_id() # Set the user UID for the new projects record to be the current user.
    print(">> copy_project %s" % (new_project.name))  # Display the call information.
    save_project_as_new(new_project, user_id) # Save a DataStore projects record for the copy project.
    copy_project_id = new_project.uid # Remember the new project UID (created in save_project_as_new()).
    return { 'projectId': copy_project_id } # Return the UID for the new projects record.


@RPC(call_type='upload')
def create_project_from_prj_file(prj_filename, user_id):
    """
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    """
    print(">> create_project_from_prj_file '%s'" % prj_filename) # Display the call information.
    try: # Try to open the .prj file, and return an error message if this fails.
        proj = sc.loadobj(prj_filename)
    except Exception:
        return { 'error': 'BadFileFormatError' }
    proj.name = sc.uniquename(proj.name, namelist=None) # Reset the project name to a new project name that is unique.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='download')
def export_results(project_id, online=True):
    proj = load_project(project_id, raise_exception=True, online=online) # Load the project with the matching UID.
    file_name = '%s outputs.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, online=online) # Generate the full file name with path.
    proj.write_results(full_file_name, keys=-1)
    print(">> export_results %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def export_graphs(project_id, online=True):
    proj = load_project(project_id, raise_exception=True, online=online) # Load the project with the matching UID.
    file_name = '%s graphs.pdf' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, online=online) # Generate the full file name with path.
    figs = proj.plot(-1) # Generate the plots
    sc.savefigs(figs, filetype='singlepdf', filename=full_file_name)
    print(">> export_graphs %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


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
        ['head', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'blnk', 'blnk', 'edit'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['head', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'blnk', 'blnk', 'edit'],
        ['blnk', 'blnk', 'blnk', 'blnk', 'blnk'],
        ['head', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'edit', 'edit', 'blnk'],
        ['blnk', 'name', 'blnk', 'blnk', 'edit'],
    ]
    
    formats['Treatment of SAM'] = [
        ['blnk', 'head', 'head', 'head'],
        ['head', 'name', 'name', 'edit'],
        ['head', 'name', 'name', 'edit'],
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
def get_sheet_data(project_id, key=None, online=True):
    sheets = [
        'Nutritional status distribution', 
        'Breastfeeding distribution',
        'IYCF packages',
        'Treatment of SAM',
        'Programs cost and coverage',
        ]
    proj = load_project(project_id, raise_exception=True, online=online)
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
def save_sheet_data(project_id, sheetdata, key=None, online=True):
    proj = load_project(project_id, raise_exception=True, online=online)
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
    proj.dataset(key).load(project=proj, from_file=False)
    print('Saving project...')
    save_project(proj, online=online)
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
                elif js_scen['scen_type'] == 'coverage': # Add commas
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
def get_scen_info(project_id, key=None, online=True):
    print('Getting scenario info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    scenario_summaries = []
    for py_scen in proj.scens.values():
        js_scen = py_to_js_scen(py_scen, proj, key=key)
        scenario_summaries.append(js_scen)
    print('JavaScript scenario info:')
    sc.pp(scenario_summaries)

    return scenario_summaries


@RPC()
def set_scen_info(project_id, scenario_summaries, online=True):
    print('Setting scenario info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    proj.scens.clear()
    for j,js_scen in enumerate(scenario_summaries):
        print('Setting scenario %s of %s...' % (j+1, len(scenario_summaries)))
        json = js_to_py_scen(js_scen)
        proj.add_scen(json=json)
        print('Python scenario info for scenario %s:' % (j+1))
        sc.pp(json)
        
    print('Saving project...')
    save_project(proj, online=online)
    return None


@RPC()
def get_default_scen(project_id, scen_type=None):
    print('Creating default scenario...')
    if scen_type is None: scen_type = 'coverage'
    proj = load_project(project_id, raise_exception=True)
    py_scens = proj.demo_scens(doadd=False)
    py_scen = py_scens[0] # Pull out the first one
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
def run_scens(project_id, online=True, doplot=True):
    
    print('Running scenarios...')
    proj = load_project(project_id, raise_exception=True, online=online)
    proj.results.clear() # Remove any existing results
    proj.run_scens()
    
    # Get graphs
    graphs = []
    if doplot:
        figs = proj.plot('scens')
        for f,fig in enumerate(figs.values()):
            for ax in fig.get_axes():
                ax.set_facecolor('none')
            graph_dict = mpld3.fig_to_dict(fig)
            graphs.append(graph_dict)
            print('Converted figure %s of %s' % (f+1, len(figs)))
        
    # Get cost-effectiveness table
    costeff = proj.get_costeff()
    table = reformat_costeff(costeff)
    
    print('Saving project...')
    save_project(proj, online=online)
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
    weightslist = [{'label':item[0], 'weight':item[1]} for item in zip(obj_labels, py_optim.weights)]
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
    json = sc.odict()
    attrs = ['name', 'model_name', 'fix_curr', 'filter_progs']
    for attr in attrs:
        json[attr] = js_optim[attr]
    try:
        json['weights'] = []
        for item in js_optim['weightslist']:
            val = to_number(item['weight'])
            json['weights'].append(val)
        json['weights'] = np.array(json['weights'])
    except Exception as E:
        print('Unable to convert "%s" to weights' % js_optim['weights'])
        raise E
    jsm = js_optim['mults']
    if isinstance(jsm, list):
        vals = jsm
    elif sc.isstring(jsm):
        try:
            vals = [float(jsm)]
        except Exception as E:
            print('Cannot figure out what to do with multipliers "%s"' % jsm)
            raise E
    else:
        raise Exception('Cannot figure out multipliers type "%s" for "%s"' % (type(jsm), jsm))
    json['mults'] = vals
    json['add_funds'] = sanitize(js_optim['add_funds'], forcefloat=True)
    json['prog_set'] = [] # These require more TLC
    for js_spec in js_optim['spec']:
        if js_spec['included']:
            json['prog_set'].append(js_spec['name'])  
    return json
    

@RPC()
def get_optim_info(project_id, online=True):
    print('Getting optimization info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    optim_summaries = []
    for py_optim in proj.optims.values():
        js_optim = py_to_js_optim(py_optim, proj)
        optim_summaries.append(js_optim)
    print('JavaScript optimization info:')
    sc.pp(optim_summaries)
    return optim_summaries


@RPC()
def set_optim_info(project_id, optim_summaries, online=True):
    print('Setting optimization info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    proj.optims.clear()
    for j,js_optim in enumerate(optim_summaries):
        print('Setting optimization %s of %s...' % (j+1, len(optim_summaries)))
        json = js_to_py_optim(js_optim)
        print('Python optimization info for optimization %s:' % (j+1))
        print(json)
        proj.add_optim(json=json)
    print('Saving project...')
    save_project(proj, online=online)   
    return None
    

@RPC()
def get_default_optim(project_id):
    print('Getting default optimization...')
    proj = load_project(project_id, raise_exception=True)
    py_optim = proj.demo_optims(doadd=False)[0]
    js_optim = py_to_js_optim(py_optim, proj, default_included=True)
    print('Created default JavaScript optimization:')
    sc.pp(js_optim)
    return js_optim


@RPC()
def plot_optimization(project_id, cache_id, online=True):
    proj = load_project(project_id, raise_exception=True, online=online)
    figs = proj.plot(key=cache_id, optim=True) # Only plot allocation
    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = mpld3.fig_to_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    return {'graphs': graphs}









###############################################################
### Results global and classes
##############################################################
    

# Global for the results cache.
results_cache = None


class ResultSet(sw.Blob):

    def __init__(self, uid, result_set, set_label):
        super(ResultSet, self).__init__(uid, type_prefix='resultset', 
            file_suffix='.rst', instance_label=set_label)
        self.result_set = result_set  # can be single Result or list of Results
        
    def show(self):
        # Show superclass attributes.
        super(ResultSet, self).show()  
        
        # Show the defined display text for the project.
        print('---------------------')
        print('Result set contents: ')
        print(self.result_set)


class ResultsCache(sw.BlobDict):

    def __init__(self, uid):
        super(ResultsCache, self).__init__(uid, type_prefix='resultscache', 
            file_suffix='.rca', instance_label='Results Cache', 
            objs_within_coll=False)
        
        # Create the Python dict to hold the hashes from cache_ids to the UIDs.
        self.cache_id_hashes = {}
        
    def load_from_copy(self, other_object):
        if type(other_object) == type(self):
            # Do the superclass copying.
            super(ResultsCache, self).load_from_copy(other_object)
            
            self.cache_id_hashes = other_object.cache_id_hashes
            
    def retrieve(self, cache_id):
        print('>> ResultsCache.retrieve() called') 
        print('>>   cache_id = %s' % cache_id)
        
        # Get the UID for the blob corresponding to the cache ID (if any).
        result_set_blob_uid = self.cache_id_hashes.get(cache_id, None)
        
        # If we found no match, return None.
        if result_set_blob_uid is None:
            print('>> ERROR: ResultSet %s not in cache_id_hashes' % result_set_blob_uid)
            return None
        
        # Otherwise, return the object found.
        else:
            obj = self.get_object_by_uid(result_set_blob_uid)
            if obj is None:
                print('>> ERROR: ResultSet %s not in DataStore handle_dict' % result_set_blob_uid)
                return None
            else:
                return self.get_object_by_uid(result_set_blob_uid).result_set
    
    def store(self, cache_id, result_set):
        print('>> ResultsCache.store() called')
        print('>>   cache_id = %s' % cache_id)
        print('>>   result_set contents:')
        print(result_set)
        
        # If there already is a cache entry for this, update the object there.
        if cache_id in self.cache_id_hashes.keys():
            result_set_blob = ResultSet(self.cache_id_hashes[cache_id], 
                result_set, cache_id)
            print('>> Running update_object()')
            self.update_object(result_set_blob)
            
        # Otherwise, update the cache ID hashes and add the new object.
        else:
            print('>> Running add_object()')
            result_set_blob = ResultSet(None, result_set, cache_id)
            self.cache_id_hashes[cache_id] = result_set_blob.uid
            self.add_object(result_set_blob)
    
    def delete(self, cache_id):
        print('>> ResultsCache.delete()')
        print('>>   cache_id = %s' % cache_id)
        
        # Get the UID for the blob corresponding to the cache ID (if any).
        result_set_blob_uid = self.cache_id_hashes.get(cache_id, None)
        
        # If we found no match, give an error.
        if result_set_blob_uid is None:
            print('>> ERROR: ResultSet not in cache_id_hashes')
            
        # Otherwise, delete the object found.
        else:
            del self.cache_id_hashes[cache_id] 
            self.delete_object_by_uid(result_set_blob_uid)
        
    def delete_all(self):
        print('>> ResultsCache.delete_all() called')
        # Reset the hashes from cache_ids to UIDs.
        self.cache_id_hashes = {}
        
        # Do the rest of the deletion process.
        self.delete_all_objects()
        
    def delete_by_project(self, project_uid):
        print('>> ResultsCache.delete_by_project() called')
        print('>>   project_uid = %s' % project_uid)
        
        # Build a list of the keys that match the given project.
        matching_cache_ids = []
        for cache_id in self.cache_id_hashes.keys():
            cache_id_project = re.sub(':.*', '', cache_id)
            if cache_id_project == project_uid:
                matching_cache_ids.append(cache_id)
        
        # For each matching key, delete the entry.
        for cache_id in matching_cache_ids:
            self.delete(cache_id)
            
    def show(self):
        super(sw.BlobDict, self).show()   # Show superclass attributes.
        if self.objs_within_coll: print('Objects stored within dict?: Yes')
        else:                     print('Objects stored within dict?: No')
        print('Cache ID dict contents: ')
        print(self.cache_id_hashes)         
        print('---------------------')
        print('Contents')
        print('---------------------')
        
        if self.objs_within_coll: # If we are storing things inside the obj_dict...
            for key in self.obj_dict: # For each key in the dictionary...
                obj = self.obj_dict[key] # Get the object pointed to.
                obj.show() # Show the handle contents.
        else: # Otherwise, we are using the UUID set.
            for uid in self.ds_uuid_set: # For each item in the set...
                obj = sw.globalvars.data_store.retrieve(uid)
                if obj is None:
                    print('--------------------------------------------')
                    print('ERROR: UID %s object failed to retrieve' % uid)
                else:
                    obj.show() # Show the object with that UID in the DataStore.
        print('--------------------------------------------')


##############################################################
### Task functions and RPCs
##############################################################
    

def tasks_delete_by_project(project_uid):
    print('>> tasks_delete_by_project() called')
    print('>>   project_uid = %s' % project_uid)
    
    # Look for an existing tasks dictionary.
    task_dict_uid = sw.globalvars.data_store.get_uid('taskdict', 'Task Dictionary')
    
    # Create the task dictionary object.
    task_dict = sw.TaskDict(task_dict_uid)
    
    # Load the TaskDict tasks from Redis.
    task_dict.load_from_data_store()

    # Build a list of the keys that match the given project.
    matching_task_ids = []
    for task_id in task_dict.task_id_hashes.keys():
        task_id_project = re.sub(':.*', '', task_id)
        if task_id_project == project_uid:
            matching_task_ids.append(task_id)
            
    print('>> Task IDs to be deleted:')
    print(matching_task_ids)
    
    # For each matching key, delete the task, aborting it in Celery also.
    for task_id in matching_task_ids:
        sw.delete_task(task_id)
            

##############################################################
### Results / ResultSet functions and RPCs
##############################################################
    

def init_results_cache(app):
    global results_cache
    
    # Look for an existing ResultsCache.
    results_cache_uid = sw.globalvars.data_store.get_uid('resultscache', 'Results Cache')
    
    # Create the results cache object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    results_cache = ResultsCache(results_cache_uid)  
    
    # If there was a match...
    if results_cache_uid is not None:
#        if app.config['LOGGING_MODE'] == 'FULL':
#            print('>> Loading ResultsCache from the DataStore.')
        results_cache.load_from_data_store()
        
    # Else (no match)...
    else:
        if app.config['LOGGING_MODE'] == 'FULL':
            print('>> Creating a new ResultsCache.') 
        results_cache.add_to_data_store()
        
    # Uncomment this to delete all the entries in the cache.
#    results_cache.delete_all()
    
    if app.config['LOGGING_MODE'] == 'FULL':
        # Show what's in the ResultsCache.    
#        results_cache.show()
        print('>> Loaded results cache with %s results' % len(results_cache.keys()))

        
def apptasks_load_results_cache():
    # Look for an existing ResultsCache.
    results_cache_uid = sw.globalvars.data_store.get_uid('resultscache', 'Results Cache')
    
    # Create the results cache object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    results_cache = ResultsCache(results_cache_uid)
    
    # If there was a match...
    if results_cache_uid is not None:
        # Load the cache from the persistent storage.
        results_cache.load_from_data_store()
        
        # Return the cache state to the Celery worker.
        return results_cache
        
    # Else (no match)...
    else: 
        print('>>> ERROR: RESULTS CACHE NOT IN DATASTORE')
        return None  


def fetch_results_cache_entry(cache_id):
    # Reload the whole data_store (handle_dict), just in case a Celery worker 
    # has modified handle_dict, for example, by adding a new ResultsCache 
    # entry.
    # NOTE: It is possible this line can be removed if Celery never writes  
    # to handle_dict.
    sw.globalvars.data_store.load()
    
    # Load the latest results_cache from persistent store.
    results_cache.load_from_data_store()
    
    # Retrieve and return the results from the cache..
    return results_cache.retrieve(cache_id)


def put_results_cache_entry(cache_id, results, apptasks_call=False):
    global results_cache
    
    # If a Celery worker has made the call...
    if apptasks_call:
        # Load the latest ResultsCache from persistent storage.  It is likely 
        # to have changed because the webapp process added a new cache entry.
        results_cache = apptasks_load_results_cache()
        
        # If we have no cache, give an error.
        if not (cache_id in results_cache.cache_id_hashes.keys()):
            print('>>> WARNING: A NEW CACHE ENTRY IS BEING ADDED BY CELERY, WHICH IS POTENTIALLY UNSAFE.  YOU SHOULD HAVE THE WEBAPP CALL make_results_cache_entry(cache_id) FIRST TO AVOID THIS')
            
    else:      
        # Load the latest results_cache from persistent store.
        results_cache.load_from_data_store()
    
    # Reload the whole data_store (handle_dict), just in case a Celery worker 
    # has modified handle_dict, for example, by adding a new ResultsCache 
    # entry.
    # NOTE: It is possible this line can be removed if Celery never writes  
    # to handle_dict.    
    sw.globalvars.data_store.load()
    
    # Actually, store the results in the cache.
    results_cache.store(cache_id, results)


@RPC() 
def check_results_cache_entry(cache_id):
    print('Checking for cached results...')
    # Load the results from the cache and check if we got a result.
    results = fetch_results_cache_entry(cache_id)   
    return { 'found': (results is not None) }


# NOTE: This function should be called by the Optimizations FE pages before the 
# call is made to launch_task().  That is because we want to avoid the Celery 
# workers adding new cache entries through its own call to ResultsCache.store()
# because that is unsafe due to conflicts over the DataStore handle_dict.
@RPC()
def make_results_cache_entry(cache_id):
    # TODO: We might want to have a check here to see if this is a new entry 
    # in the cache, and if it isn't, just exit out, so the store doesn't 
    # overwrite the already-stored result.  However, this may not really be an 
    # issue because "Plot results" is disabled during the running of a task.
    results_cache.store(cache_id, None)

    
@RPC()
def delete_results_cache_entry(cache_id):
    results_cache.delete(cache_id)
    