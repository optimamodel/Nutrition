"""
rpcs.py -- code related to HealthPrior project management
    
Last update: 2018jun04 by cliffk
"""

#
# Imports
#

import os
from zipfile import ZipFile
from flask_login import current_user
import mpld3
import numpy as np

import sciris.corelib.fileio as fileio
import sciris.weblib.user as user
import sciris.core as sc
import sciris.web as sw

import nutrition.ui as nu
from . import projects as prj

# Dictionary to hold all of the registered RPCs in this module.
RPC_dict = {}

# RPC registration decorator factory created using call to make_register_RPC().
register_RPC = sw.make_register_RPC(RPC_dict)


        
###############################################################
#%% Other functions (mostly helpers for the RPCs)
##############################################################
    

def load_project_record(project_id, raise_exception=True):
    """
    Return the project DataStore reocord, given a project UID.
    """ 
    
    # Load the matching prj.ProjectSO object from the database.
    project_record = prj.proj_collection.get_object_by_uid(project_id)

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
    Return project summaries for all projects the user has to the client. -- WARNING, fix!
    """ 
    
    # Get the prj.ProjectSO entries matching the user UID.
    project_entries = prj.proj_collection.get_project_entries_by_user(current_user.get_id())
    
    # Grab a list of project summaries from the list of prj.ProjectSO objects we 
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
    Given a Project object, wrap it in a new prj.ProjectSO object and put this 
    in the project collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Project.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_record = load_project_record(proj.uid)
    
    # Copy the project, only save what we want...
    new_project = sc.dcp(proj)
    new_project.modified = sc.today()
         
    # Create the new project entry and enter it into the ProjectCollection.
    # Note: We don't need to pass in project.uid as a 3rd argument because 
    # the constructor will automatically use the Project's UID.
    projSO = prj.ProjectSO(new_project, project_record.owner_uid)
    prj.proj_collection.update_object(projSO)
    

def save_project_as_new(proj, user_id):
    """
    Given a Project object and a user UID, wrap the Project in a new prj.ProjectSO 
    object and put this in the project collection, after getting a fresh UID
    for this Project.  Then do the actual save.
    """ 
    
    # Set a new project UID, so we aren't replicating the UID passed in.
    proj.uid = sc.uuid()
    
    # Create the new project entry and enter it into the ProjectCollection.
    projSO = prj.ProjectSO(proj, user_id)
    prj.proj_collection.add_object(projSO)  

    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> save_project_as_new '%s'" % proj.name)

    # Save the changed Project object to the DataStore.
    save_project(proj)
    
    return None





##################################################################################
#%% Project RPCs
##################################################################################

# Not a project RPC, but doesn't really belong
@register_RPC()
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

    
@register_RPC(validation_type='nonanonymous user')
def get_scirisdemo_projects():
    """
    Return the projects associated with the Sciris Demo user.
    """
    
    # Get the user UID for the _ScirisDemo user.
    user_id = user.get_scirisdemo_user()
   
    # Get the prj.ProjectSO entries matching the _ScirisDemo user UID.
    project_entries = prj.proj_collection.get_project_entries_by_user(user_id)

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
    
    # Return a project summary from the accessed prj.ProjectSO entry.
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
    
    # Get all of the prj.ProjectSO entries.
    project_entries = prj.proj_collection.get_all_objects()
    
    # Grab a list of project summaries from the list of prj.ProjectSO objects we 
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
            prj.proj_collection.delete_object_by_uid(project_id)

@register_RPC(call_type='download', validation_type='nonanonymous user')   
def download_project(project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    dirname = fileio.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s.prj' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    fileio.object_to_gzip_string_pickle_file(full_file_name, proj) # Write the object to a Gzip string pickle file.
    print(">> download_project %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.

@register_RPC(call_type='download', validation_type='nonanonymous user')   
def download_databook(project_id):
    """
    Download databook
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    dirname = fileio.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s_databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    proj.dataset().demo_data.spreadsheet.save(full_file_name)
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@register_RPC(call_type='download', validation_type='nonanonymous user')   
def download_defaults(project_id):
    """
    Download defaults
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    dirname = fileio.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s_defaults.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    proj.dataset().default_params.spreadsheet.save(full_file_name)
    print(">> download_defaults %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@register_RPC(call_type='download', validation_type='nonanonymous user')
def load_zip_of_prj_files(project_ids):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path

    # Build a list of prj.ProjectSO objects for each of the selected projects, 
    # saving each of them in separate .prj files.
    prjs = [load_project_record(id).save_as_file(dirname) for id in project_ids]
    
    # Make the zip file name and the full server file path version of the same..
    zip_fname = '%s.zip' % str(sc.uuid())
    server_zip_fname = os.path.join(dirname, zip_fname)
    
    # Create the zip file, putting all of the .prj files in a projects 
    # directory.
    with ZipFile(server_zip_fname, 'w') as zipfile:
        for project in prjs:
            zipfile.write(os.path.join(dirname, project), 'projects/{}'.format(project))
            
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> load_zip_of_prj_files %s" % (server_zip_fname))

    # Return the server file name.
    return server_zip_fname

@register_RPC(validation_type='nonanonymous user')
def add_demo_project(user_id):
    """
    Add a demo Optima TB project
    """
    # Get a unique name for the project to be added.
    new_proj_name = get_unique_name('Demo project', other_names=None)
    
    # Create the project, loading in the desired spreadsheets.
    proj = nu.demo() 
    proj.name = new_proj_name
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> add_demo_project %s" % (proj.name))    
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(proj.uid) }


@register_RPC(call_type='download', validation_type='nonanonymous user')
def create_new_project(user_id, proj_name, num_pops, data_start, data_end):
    """
    Create a new Optima Nutrition project.
    """
    
    args = {"num_pops":int(num_pops), "data_start":int(data_start), "data_end":int(data_end)}
    
    # Get a unique name for the project to be added.
    new_proj_name = get_unique_name(proj_name, other_names=None)
    
    # Create the project, loading in the desired spreadsheets.
    proj = nu.Project(name=new_proj_name)
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> create_new_project %s" % (proj.name))    
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path
        
    # Create a filename containing the project name followed by a .prj 
    # suffix.
    file_name = '%s.xlsx' % proj.name
        
    # Generate the full file name with path.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name)
    
    # Return the databook
    proj.create_databook(databook_path=full_file_name, **args)
    
    print(">> download_databook %s" % (full_file_name))
    
    # Return the new project UID in the return message.
    return full_file_name


@register_RPC(call_type='upload', validation_type='nonanonymous user')
def upload_databook(databook_filename, project_id):
    """ Upload a databook to a project. """
    print(">> upload_databook '%s'" % databook_filename)
    proj = load_project(project_id, raise_exception=True)
    proj.load_data(filepath=databook_filename) # Reset the project name to a new project name that is unique.
    proj.modified = sc.today()
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


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
    proj.modified = sc.today()
    
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


##################################################################################
#%% Scenario functions and RPCs
##################################################################################

def py_to_js_scen(py_scen, prog_names):
    ''' Convert a Python to JSON representation of a scenario '''
    attrs = ['name', 'active', 'scen_type', 't']
    js_scen = {}
    for attr in attrs:
        js_scen[attr] = getattr(py_scen, attr) # Copy the attributes into a dictionary
    js_scen['spec'] = []
    for prog_name in prog_names:
        this_spec = {}
        this_spec['name'] = prog_name
        this_spec['included'] = True if prog_name in py_scen.prog_set else False
        this_spec['vals'] = []
        if prog_name in py_scen.scen:
            this_spec['vals'] = py_scen.scen[prog_name]
        else:
            this_spec['vals'] = [None]*py_scen.n_years()
        js_scen['spec'].append(this_spec)
    return js_scen
    

@register_RPC(validation_type='nonanonymous user')    
def get_scenario_info(project_id):

    print('Getting scenario info...')
    proj = load_project(project_id, raise_exception=True)
    
    scenario_summaries = []
    for py_scen in proj.scens.values():
        js_scen = py_to_js_scen(py_scen, proj.dataset().prog_names())
        scenario_summaries.append(js_scen)
    
    print('JavaScript scenario info:')
    print(scenario_summaries)

    return scenario_summaries


@register_RPC(validation_type='nonanonymous user')    
def get_default_scenario(project_id):

    print('Creating default scenario...')
    proj = load_project(project_id, raise_exception=True)
    
    py_scen = proj.default_scens(doadd=False)[0]
    js_scen = py_to_js_scen(py_scen, proj.dataset().prog_names())
    
    print('Created default JavaScript scenario:')
    print(js_scen)
    return js_scen


def sanitize(vals, skip=False):
    ''' Make sure values are numeric, and either return nans or skip vals that aren't '''
    if sc.isiterable(vals):
        as_array = True
    output = []
    for val in vals:
        if val=='':
            sanival = np.nan
        elif val==None:
            sanival = np.nan
        else:
            try:
                sanival = float(val)
            except Exception as E:
                print('Could not sanitize value "%s": %s; returning nan' % (val, repr(E)))
                sanival = np.nan
        if skip and not np.isnan(sanival):
            output.append(sanival)
        else:
            output.append(sanival)
    if as_array:
        return output
    else:
        return output[0]
    
    
@register_RPC(validation_type='nonanonymous user')    
def set_scenario_info(project_id, scenario_summaries):

    print('Setting scenario info...')
    proj = load_project(project_id, raise_exception=True)
    proj.scens.clear()
    
    for j,js_scen in enumerate(scenario_summaries):
        print('Setting scenario %s of %s...' % (j+1, len(scenario_summaries)))
        json = sc.odict()
        for attr in ['name', 'scen_type', 'active']: # Copy these directly
            json[attr] = js_scen[attr]
        json['prog_set'] = [] # These require more TLC
        json['scen'] = sc.odict()
        for js_spec in js_scen['spec']:
            if js_spec['included']:
                json['prog_set'].append(js_spec['name'])
                json['scen'][js_spec['name']] = sanitize(js_spec['vals'])
        
        print('Python scenario info for scenario %s:' % (j+1))
        print(json)
        
        proj.add_scen(json=json)
    
    print('Saving project...')
    save_project(proj)
    
    return None


@register_RPC(validation_type='nonanonymous user')    
def run_scenarios(project_id):
    
    print('Running scenarios...')
    proj = load_project(project_id, raise_exception=True)
    
    proj.run_scens()
    figs = proj.plot(toplot=['prevs', 'outputs']) # Do not plot allocation
    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = mpld3.fig_to_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    
    print('Saving project...')
    save_project(proj)    
    return {'graphs':graphs}




##################################################################################
#%% Optimization functions and RPCs
##################################################################################

def py_to_js_optim(py_optim, prog_names):
    ''' Convert a Python to JSON representation of an optimization '''
    attrs = ['name', 'mults', 'add_funds', 'objs']
    js_optim = {}
    for attr in attrs:
        js_optim[attr] = getattr(py_optim, attr) # Copy the attributes into a dictionary
    js_optim['spec'] = []
    for prog_name in prog_names:
        this_spec = {}
        this_spec['name'] = prog_name
        this_spec['included'] = True if prog_name in py_optim.prog_set else False
        this_spec['vals'] = []
        js_optim['spec'].append(this_spec)
    return js_optim
    

@register_RPC(validation_type='nonanonymous user')    
def get_optim_info(project_id):

    print('Getting optimization info...')
    proj = load_project(project_id, raise_exception=True)
    
    optim_summaries = []
    for py_optim in proj.optims.values():
        js_optim = py_to_js_optim(py_optim, proj.dataset().prog_names())
        optim_summaries.append(js_optim)
    
    print('JavaScript optimization info:')
    print(optim_summaries)

    return optim_summaries


@register_RPC(validation_type='nonanonymous user')    
def get_default_optim(project_id):

    print('Getting default optimization...')
    proj = load_project(project_id, raise_exception=True)
    
    py_optim = proj.default_optims(doadd=False)[0]
    js_optim = py_to_js_optim(py_optim, proj.dataset().prog_names())
    js_optim['objective_options'] = ['thrive', 'child_deaths', 'stunting_prev', 'wasting_prev', 'anaemia_prev'] # WARNING, stick allowable optimization options here
    
    print('Created default JavaScript optimization:')
    print(js_optim)
    return js_optim



@register_RPC(validation_type='nonanonymous user')    
def set_optim_info(project_id, optim_summaries):

    print('Setting optimization info...')
    proj = load_project(project_id, raise_exception=True)
    proj.optims.clear()
    
    for j,js_optim in enumerate(optim_summaries):
        print('Setting optimization %s of %s...' % (j+1, len(optim_summaries)))
        json = sc.odict()
        for attr in ['name', 'mults', 'add_funds', 'objs']: # Copy these directly -- WARNING, copy-pasted
            json[attr] = js_optim[attr]
        json['name'] = js_optim['name']
        vals = js_optim['mults'].split(',')
        json['mults'] = sanitize(vals, skip=True)
        json['add_funds'] = sanitize(js_optim['add_funds'])
        json['prog_set'] = [] # These require more TLC
        for js_spec in js_optim['spec']:
            if js_spec['included']:
                json['prog_set'].append(js_spec['name'])
        
        print('Python optimization info for optimization %s:' % (j+1))
        print(json)
        
        proj.add_optim(json=json)
    
    print('Saving project...')
    save_project(proj)   
    
    return None


@register_RPC(validation_type='nonanonymous user')    
def run_optim(project_id, optim_name):
    
    print('Running optimization...')
    proj = load_project(project_id, raise_exception=True)
    
    proj.run_optim(key=optim_name)
    figs = proj.plot(toplot=['alloc']) # Only plot allocation
    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = mpld3.fig_to_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    
    print('Saving project...')
    save_project(proj)    
    return {'graphs':graphs}