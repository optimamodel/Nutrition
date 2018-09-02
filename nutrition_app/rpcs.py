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


# Dictionary to hold all of the registered RPCs in this module.
RPC_dict = {}

# RPC registration decorator factory created using call to make_RPC().
RPC = sw.makeRPCtag(RPC_dict)


        
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


def get_path(filename):
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    fullpath = '%s%s%s' % (dirname, os.sep, filename) # Generate the full file name with path.
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
                sanival = float(val)
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

def load_project(project_id, raise_exception=True, online=True):
    """
    Return the Nutrition Project object, given a project UID, or None if no 
    ID match is found.
    """ 
    
    # If running offline, just return the project
    if not online: 
        return project_id
    
    # Load the project record matching the ID passed in.
    project_record = load_project_record(project_id, raise_exception=raise_exception)
    
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
    
    # Load the project record matching the UID of the project passed in.
    project_record = load_project_record(proj.uid)
    
    # Copy the project, only save what we want...
    new_project = sc.dcp(proj)
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
    """
    Return the projects associated with the Sciris Demo user.
    """
    
    # Get the user UID for the _ScirisDemo user.
    user_id = sw.get_scirisdemo_user()
   
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

@RPC()
def load_project_summary(project_id):
    """
    Return the project summary, given the Project UID.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_entry = load_project_record(project_id)
    
    # Return a project summary from the accessed prj.ProjectSO entry.
    return load_project_summary_from_project_record(project_entry)


@RPC()
def load_current_user_project_summaries():
    """
    Return project summaries for all projects the user has to the client.
    """ 
    
    return load_current_user_project_summaries2()


@RPC()                
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
            
@RPC()    
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

@RPC(call_type='download', validation='named')   
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

@RPC(call_type='download', validation='named')   
def download_databook(project_id):
    """
    Download databook
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s_databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.dataset().demo_data.spreadsheet.save(full_file_name)
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download', validation='named')   
def download_defaults(project_id):
    """
    Download defaults
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s_defaults.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.dataset().default_params.spreadsheet.save(full_file_name)
    print(">> download_defaults %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download', validation='named')
def load_zip_of_prj_files(project_ids):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    prjs = [load_project_record(id).save_as_file(dirname) for id in project_ids] # Build a list of prj.ProjectSO objects for each of the selected projects, saving each of them in separate .prj files.
    zip_fname = '%s.zip' % str(sc.uuid()) # Make the zip file name and the full server file path version of the same.
    server_zip_fname = os.path.join(dirname, sc.sanitizefilename(zip_fname))
    with ZipFile(server_zip_fname, 'w') as zipfile: # Create the zip file, putting all of the .prj files in a projects directory.
        for project in prjs:
            zipfile.write(os.path.join(dirname, project), 'projects/{}'.format(project))
    print(">> load_zip_of_prj_files %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.

@RPC()
def add_demo_project(user_id):
    """
    Add a demo Optima Nutrition project
    """
    new_proj_name = get_unique_name('Demo project', other_names=None) # Get a unique name for the project to be added.
    proj = nu.demo(scens=True, optims=True)  # Create the project, loading in the desired spreadsheets.
    proj.name = new_proj_name
    print(">> add_demo_project %s" % (proj.name)) # Display the call information.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='download', validation='named')
def create_new_project(user_id, proj_name):
    """
    Create a new Optima Nutrition project.
    """
    template_name = 'template_input.xlsx'
    new_proj_name = get_unique_name(proj_name, other_names=None) # Get a unique name for the project to be added.
    proj = nu.Project(name=new_proj_name) # Create the project
    print(">> create_new_project %s" % (proj.name))     # Display the call information.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    databook_path = sc.makefilepath(filename=template_name, folder=nu.ONpath('applications'))
    file_name = '%s databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name)
    copyfile(databook_path, full_file_name)
    print(">> download_databook %s" % (full_file_name))
    return full_file_name


@RPC(call_type='upload', validation='named')
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
    """
    Given the passed in project summary, update the underlying project 
    accordingly.
    """ 
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
    new_project.name = get_unique_name(proj.name, other_names=None) # Just change the project name, and we have the new version of the Project object to be saved as a copy.
    user_id = current_user.get_id() # Set the user UID for the new projects record to be the current user.
    print(">> copy_project %s" % (new_project.name))  # Display the call information.
    save_project_as_new(new_project, user_id) # Save a DataStore projects record for the copy project.
    copy_project_id = new_project.uid # Remember the new project UID (created in save_project_as_new()).
    return { 'projectId': copy_project_id } # Return the UID for the new projects record.


@RPC(call_type='upload', validation='named')
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
    proj.name = get_unique_name(proj.name, other_names=None) # Reset the project name to a new project name that is unique.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='download', validation='named')
def export_results(project_id):
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s outputs.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.write_results(full_file_name, keys=-1)
    print(">> export_results %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.



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
        if this_spec['included']:
            count += 1
            try:
                this_spec['vals'] = py_scen.vals[count]
            except:
                this_spec['vals'] = [None]
            while len(this_spec['vals']) < settings.n_years: # Ensure it's the right length
                this_spec['vals'].append(None)
        else:
            this_spec['vals'] = [None]*settings.n_years # WARNING, kludgy way to extract the number of years
        if js_scen['scen_type'] == 'coverage': # Convert to percentage
            for y in range(len(this_spec['vals'])):
                if this_spec['vals'][y] is not None:
                    this_spec['vals'][y] = round(100*this_spec['vals'][y]) # Enter to the nearest percentage
        this_spec['base_cov'] = round(program.base_cov*100) # Convert to percentage
        this_spec['base_spend'] = round(program.base_spend)
        js_scen['progvals'].append(this_spec)
        js_scen['t'] = settings.t
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


@RPC()    
def run_scens(project_id, online=True):
    
    print('Running scenarios...')
    proj = load_project(project_id, raise_exception=True, online=online)
    
    proj.results.clear() # Remove any existing results
    proj.run_scens()
    figs = proj.plot('scens')

    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = mpld3.fig_to_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    
    print('Saving project...')
    save_project(proj, online=online)    
    return {'graphs':graphs}




##################################################################################
### Optimization functions and RPCs
##################################################################################

def objective_mapping():
    output = [
        'Number of child deaths',
        'Number of stunted children',
        'Wasting prevalence',
        'Stunting prevalence',
        'Child anaemia prevalence',
        'Maternal anaemia prevalence',
        'Maternal deaths',
        'Child mortality rate',
        'Maternal mortality rate',
        '<Placeholder>',
        ]
    return output


def py_to_js_optim(py_optim, proj, key=None, default_included=False):
    ''' Convert a Python to JSON representation of an optimization '''
    prog_names = proj.dataset().prog_names()
    js_optim = {}
    attrs = ['name', 'model_name', 'mults', 'add_funds', 'fix_curr', 'filter_progs']
    for attr in attrs:
        js_optim[attr] = getattr(py_optim, attr) # Copy the attributes into a dictionary
    weightslist = [{'label':item[0], 'weight':item[1]} for item in zip(objective_mapping(), py_optim.weights)]
    js_optim['weightslist'] = weightslist
    js_optim['spec'] = []
    for prog_name in prog_names:
        program = proj.model(key).prog_info.programs[prog_name]
        this_spec = {}
        this_spec['name'] = prog_name
        this_spec['included'] = is_included(py_optim.prog_set, program, default_included)
        js_optim['spec'].append(this_spec)
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
    js_optim['objective_options'] = objective_mapping()
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