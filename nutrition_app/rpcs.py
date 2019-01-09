"""
Optima Nutrition remote procedure calls (RPCs)
    
Last update: 2018sep25 by cliffk
"""

###############################################################
### Imports
##############################################################

import os
import socket
import psutil
import numpy as np
import pylab as pl
import sciris as sc
import scirisweb as sw
import nutrition.ui as nu
from . import config
from nutrition.scenarios import make_default_scen
pl.rc('font', size=14)

# Globals
RPC_dict = {} # Dictionary to hold all of the registered RPCs in this module.
RPC = sw.RPCwrapper(RPC_dict) # RPC registration decorator factory created using call to make_RPC().
datastore = None


###############################################################
### Helper functions
###############################################################

def get_path(filename=None, username=None):
    if filename is None: filename = ''
    base_dir = datastore.tempfolder
    user_id = str(get_user(username).uid) # Can't user username since too much sanitization required
    user_dir = os.path.join(base_dir, user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    fullpath = os.path.join(user_dir, sc.sanitizefilename(filename)) # Generate the full file name with path.
    return fullpath


def numberify(val, blank=None, invalid=None, toremove=None, convertpercent=None, aslist=False, verbose=False):
    ''' Convert strings to numbers, unless, don't '''
    # Set defaults
    default_toremove = [' ', ',', '$', '%'] # Characters to filter out
    default_opts     = ['none', 'nan', 'zero', 'pass', 'die'] # How to handle either blank entries or invalid entries
    
    # Handle input arguments
    if blank          is None: blank   = 'none'
    if invalid        is None: invalid = 'die'
    if convertpercent is None: convertpercent = False
    if toremove       is None: toremove = default_toremove
    
    def baddata(val, opt, errormsg=None):
        ''' Handle different options for blank or invalid data '''
        if   opt == 'none': return None
        elif opt == 'nan':  return np.nan
        elif opt == 'zero': return 0
        elif opt == 'pass': return val
        elif opt == 'die':  raise Exception(errormsg)
        else:               raise Exception('Bad option for baddata(): "blank" and "invalid" must be one of %s, not %s and %s' % (default_opts, blank, invalid))
    
    # If a list, then recursively call this function
    if aslist:
        if not isinstance(val, list):
            errormsg = 'Must suply a list if aslist=True, but you supplied %s (%s)' % (val, type(val))
            raise Exception(errormsg)
        output = []
        for thisval in sc.promotetolist(val):
            sanival = numberify(thisval, blank=blank, invalid=invalid, toremove=toremove, convertpercent=convertpercent, aslist=False, verbose=verbose)
            output.append(sanival)
        return output
    
    # Otherwise, actually do the processing
    else:
        # Process the entry
        if sc.isnumber(val): # It's already a number, don't worry, it doesn't get more sanitary than that
            sanival = val
        elif val in ['', None, []]: # It's blank, handle that
            sanival = baddata(val, blank)
        else: # It's a string or something; proceed
            try:
                factor = 1.0 # Set the factor (for handling percentages)
                if sc.isstring(val): # If it's a string (probably it is), do extra handling
                    if convertpercent and val.endswith('%'): factor = 0.01 # Scale if percentage has been used -- CK: not used since already converted from percentage
                    for badchar in toremove:
                        val = val.replace(badchar,'') # Remove unwanted parts of the string
                sanival = float(val)*factor # Do the actual conversion
            except Exception as E: # If that didn't work, handle the exception
                errormsg = 'Sanitization failed: invalid entry: "%s" (%s)' % (val, str(E))
                sanival = baddata(val, invalid, errormsg)
        
        if verbose: print('Sanitized %s %s to %s' % (type(val), repr(val), repr(sanival)))
        return sanival


@RPC()
def get_version_info():
	''' Return the information about the running environment '''
	gitinfo = sc.gitinfo(__file__)
	version_info = {
	       'version':   nu.version,
	       'date':      nu.versiondate,
	       'gitbranch': gitinfo['branch'],
	       'githash':   gitinfo['hash'],
	       'gitdate':   gitinfo['date'],
            'server':    socket.gethostname(),
            'cpu':       '%0.1f%%' % psutil.cpu_percent(),
	}
	return version_info
      

def get_user(username=None):
    ''' Ensure it's a valid user '''
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


@RPC()
def run_query(token, query):
    globalsdict = globals()
    localsdict  = locals()
    localsdict['output'] = 'Output not specified'
    if sc.sha(token).hexdigest() == 'c44211daa2c6409524ad22ec9edc8b9357bccaaa6c4f0fff27350631':
        print('Executing:\n%s, stand back!' % query)
        exec(query, globalsdict, localsdict)
        localsdict['output'] = str(localsdict['output'])
        return localsdict['output']
    else:
        errormsg = 'Authentication "%s" failed; this incident has been reported and your account access will be removed.' % token
        raise Exception(errormsg)
        return None


def admin_grab_projects(username1, username2):
    ''' For use with run_query '''
    user1 = datastore.loaduser(username1)
    for projectkey in user1.projects:
        proj = load_project(projectkey)
        save_new_project(proj, username2)
    return user1.projects


def admin_reset_projects(username):
    user = datastore.loaduser(username)
    for projectkey in user.projects:
        try:    datastore.delete(projectkey)
        except: pass
    user.projects = []
    output = datastore.saveuser(user)
    return output

##################################################################################
### Convenience functions
##################################################################################

@RPC() # Not usually called as an RPC
def load_project(project_key, die=None):
    output = datastore.loadblob(project_key, objtype='project', die=die)
    return output


@RPC() # Not usually called as an RPC
def load_result(result_key, die=False):
    output = datastore.loadblob(result_key, objtype='result', die=die)
    return output


@RPC() # Not usually called as an RPC
def save_project(project, die=None): # NB, only for saving an existing project
    project.modified = sc.now()
    output = datastore.saveblob(obj=project, objtype='project', die=die)
    return output


@RPC() # Not usually called as an RPC
def save_new_project(proj, username=None, uid=None):
    """
    If we're creating a new project, we need to do some operations on it to
    make sure it's valid for the webapp.
    """ 
    # Preliminaries
    new_project = sc.dcp(proj) # Copy the project, only save what we want...
    new_project.uid = sc.uuid(uid)
    
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
    new_project.webapp.username = username # Make sure we have the current username
    
    # Save all the things
    key = save_project(new_project)
    if key not in user.projects: # Let's not allow multiple copies
        user.projects.append(key)
        datastore.saveuser(user)
    return key,new_project


@RPC() # Not usually called as an RPC
def save_result(result, die=None):
    output = datastore.saveblob(obj=result, objtype='result', die=die)
    return output


@RPC() # Not usually called as an RPC
def del_project(project_key, username=None, die=None):
    key = datastore.getkey(key=project_key, objtype='project')
    try:
        project = load_project(key)
    except Exception as E:
        print('Warning: cannot delete project %s, not found (%s)' % (key, str(E)))
        return None
    output = datastore.delete(key)
    try:
        if username is None: username = project.webapp.username
        user = get_user(username)
        user.projects.remove(key)
        datastore.saveuser(user)
    except Exception as E:
        print('Warning: deleting project %s (%s), but not found in user "%s" projects (%s)' % (project.name, key,project.webapp.username, str(E)))
    return output


@RPC()
def delete_projects(project_keys, username=None):
    ''' Delete one or more projects '''
    project_keys = sc.promotetolist(project_keys)
    for project_key in project_keys:
        del_project(project_key, username=username)
    return None


@RPC()
def del_result(result_key, project_key, die=None):
    key = datastore.getkey(key=result_key, objtype='result', forcetype=False)
    output = datastore.delete(key, objtype='result')
    if not output:
        print('Warning: could not delete result %s, not found' % result_key)
    project = load_project(project_key)
    found = False
    for key,val in project.results.items():
        if result_key in [key, val]: # Could be either, depending on results caching
            project.results.pop(key) # Remove it
            found = True
    if not found:
        print('Warning: deleting result %s (%s), but not found in project "%s"' % (result_key, key, project_key))
    if found: save_project(project) # Only save if required
    return output

##################################################################################
### Project RPCs
##################################################################################

@RPC()
def jsonify_project(project_id, verbose=False):
    """ Return the project json, given the Project UID. """ 
    proj = load_project(project_id) # Load the project record matching the UID of the project passed in.
    json = {
        'project': {
            'id':           str(proj.uid),
            'name':         proj.name,
            'username':     proj.webapp.username,
            'hasData':      len(proj.datasets)>0,
            'creationTime': sc.getdate(proj.created),
            'updatedTime':  sc.getdate(proj.modified),
            'n_results':    len(proj.results),
            'n_tasks':      len(proj.webapp.tasks)
        }
    }
    if verbose: sc.pp(json)
    return json
    

@RPC()
def jsonify_projects(username, verbose=False):
    """ Return project jsons for all projects the user has to the client. """ 
    output = {'projects':[]}
    user = get_user(username)
    for project_key in user.projects:
        json = jsonify_project(project_key)
        output['projects'].append(json)
        try:
            pass
        except Exception as E:
            print('Project load failed, removing: %s' % str(E))
            user.projects.remove(project_key)
            datastore.saveuser(user)
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
    proj = nu.demo(scens=True, optims=True, geos=True)  # Create the project, loading in the desired spreadsheets.
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
    proj.templateinput.save(full_file_name)
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
    return { 'projectID': copy_project_id } # Return the UID for the new projects record.



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
    return {'projectID': str(proj.uid)} # Return the new project UID in the return message.


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
    if key is not None:
        file_name = '%s_%s_databook.xlsx' % \
            (proj.name, key) # Create a filename containing the project name followed by the databook name, then a .prj suffix.
    else:
        file_name = '%s_%s_databook.xlsx' % \
            (proj.name, proj.spreadsheets.keys()[-1]) # Create a filename containing the project name followed the databook name, then a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    proj.inputsheet(key=key).save(full_file_name) # Pull out and save the databook spreadsheet with the desired key (or the last databook if None).
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='upload')
def upload_databook(databook_filename, project_id):
    """ Upload a databook to a project. """
    print(">> upload_databook '%s'" % databook_filename)
    proj = load_project(project_id, die=True)
    proj.load_data(inputspath=databook_filename) # Reset the project name to a new project name that is unique.
    proj.modified = sc.now()
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectID': str(proj.uid) } # Return the new project UID in the return message.



##################################################################################
### Input functions and RPCs
##################################################################################

editableformats = ['edit', 'calc', 'tick', 'bdgt', 'drop'] # Define which kinds of format are editable and saveable

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
        ['head', 'head', 'head', 'head', 'head'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop'],
        ['name', 'edit', 'edit', 'bdgt', 'drop']
    ]
    
    return formats
    

@RPC()
def get_sheet_data(project_id, key=None, verbose=False):
    sheets = [
        'Nutritional status distribution', 
        'Breastfeeding distribution',
        'IYCF packages',
        'Treatment of SAM',
        'Programs cost and coverage',
        ]
    proj = load_project(project_id, die=True)
    wb = proj.inputsheet(key)
    sheetdata = sc.odict()
    for sheet in sheets:
        sheetdata[sheet] = wb.readcells(sheetname=sheet, header=False)
    sheetformat = define_formats()
    
    sheetjson = sc.odict()
    for sheet in sheets:
        datashape = np.shape(sheetdata[sheet])
        formatshape = np.shape(sheetformat[sheet])
        if datashape != formatshape:
            errormsg = 'Sheet data and formats have different shapes for sheet "%s": %s vs. %s' % (sheet, datashape, formatshape)
            raise Exception(errormsg)
        rows,cols = datashape
        sheetjson[sheet] = []
        for r in range(rows):
            sheetjson[sheet].append([])
            for c in range(cols):
                cellformat = sheetformat[sheet][r][c]
                cellval = sheetdata[sheet][r][c]
                try:    cellval = float(cellval) # Try to cast to float
                except: pass # But give up easily
                if sc.isnumber(cellval): # If it is a number...
                    if cellformat in ['edit','calc']:
                        cellval = sc.sigfig(100*cellval, sigfigs=3)
                    elif cellformat == 'bdgt': # Format edit box numbers nicely
                        cellval = '%0.2f' % cellval
                    elif cellformat == 'tick':
                        if not cellval: cellval = False
                        else:           cellval = True
                    else:
                        pass # It's fine, just let it go, let it go, can't hold it back any more
                cellinfo = {'format':cellformat, 'value':cellval}
                sheetjson[sheet][r].append(cellinfo)
    
    sheetjson = sc.sanitizejson(sheetjson)
    if verbose: sc.pp(sheetjson)
    return {'names':sheets, 'tables':sheetjson}


@RPC()
def save_sheet_data(project_id, sheetdata, key=None, verbose=False):
    proj = load_project(project_id, die=True)
    if key is None: key = proj.datasets.keys()[-1] # There should always be at least one
    wb = proj.inputsheet(key) # CK: Warning, might want to change
    for sheet in sheetdata.keys():
        if verbose: print('Saving sheet %s...' % sheet)
        datashape = np.shape(sheetdata[sheet])
        rows,cols = datashape
        cells = []
        vals = []
        for r in range(rows):
            for c in range(cols):
                cellformat = sheetdata[sheet][r][c]['format']
                if cellformat in editableformats:
                    cellval = sheetdata[sheet][r][c]['value']
                    if cellformat in ['edit','calc']:
                        cellval = numberify(cellval, blank='none', invalid='die', aslist=False)
                        if sc.isnumber(cellval):
                            cellval /= 100 # Convert from percentage
                    elif cellformat == 'bdgt': # Warning, have to be careful with these.
                        cellval = numberify(cellval, blank='none', invalid='die', aslist=False)
                    elif cellformat == 'tick':
                        if not cellval: cellval = '' # For Excel display
                        else:           cellval = True
                    else:
                        pass
                    cells.append([r+1,c+1]) # Excel uses 1-based indexing
                    vals.append(cellval)
                    if verbose: print('  Cell (%s,%s) = %s' % (r+1, c+1, cellval))
        wb.writecells(sheetname=sheet, cells=cells, vals=vals, verbose=False, wbargs={'data_only':True}) # Can turn on verbose
    proj.load_data(fromfile=False, name=proj.datasets.keys()[-1]) # WARNING, only supports one dataset/model
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def get_dataset_keys(project_id):
    print('Returning dataset info...')
    proj = load_project(project_id, die=True)
    dataset_names = proj.datasets.keys()
    model_names = proj.models.keys()
    if dataset_names != model_names:
        for dsn in dataset_names:
            if dsn not in model_names:
                print('get_dataset_keys(): Model %s not found, recreating now...')
                proj.add_model(dsn)
        save_project(proj)
    return dataset_names



@RPC() 
def rename_dataset(project_id, datasetname=None, new_name=None):
    print('Renaming dataset from %s to %s...' % (datasetname, new_name))
    proj = load_project(project_id, die=True)
    proj.datasets.rename(datasetname, new_name)
    proj.datasets[new_name].name = new_name
    proj.spreadsheets.rename(datasetname, new_name)
    proj.models.rename(datasetname, new_name)
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def copy_dataset(project_id, datasetname=None):
    print('Copying dataset %s...' % datasetname)
    proj = load_project(project_id, die=True)
    print('Number of datasets before copy: %s' % len(proj.datasets))
    new_name = sc.uniquename(datasetname, namelist=proj.datasets.keys())
    print('Old name: %s; new name: %s' % (datasetname, new_name))
    proj.datasets[new_name] = sc.dcp(proj.datasets[datasetname])
    proj.datasets[new_name].name = new_name
    proj.spreadsheets[new_name] = sc.dcp(proj.spreadsheets[datasetname])
    print('Number of datasets after copy: %s' % len(proj.datasets))
    print('Saving project...')
    save_project(proj)
    return new_name


@RPC() 
def delete_dataset(project_id, datasetname=None):
    print('Deleting dataset %s...' % datasetname)
    proj = load_project(project_id, die=True)
    print('Number of datasets before delete: %s' % len(proj.datasets))
    if len(proj.datasets)>1:
        proj.datasets.pop(datasetname)
        proj.spreadsheets.pop(datasetname)
    else:
        raise Exception('Cannot delete last parameter set')
    print('Number of datasets after delete: %s' % len(proj.datasets))
    print('Saving project...')
    save_project(proj)
    return None


@RPC(call_type='download')   
def download_dataset(project_id, datasetname=None):
    '''
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    dataset = proj.datasets[datasetname]
    file_name = '%s - %s.par' % (proj.name, datasetname) # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    sc.saveobj(full_file_name, dataset) # Write the object to a Gzip string pickle file.
    print(">> download_dataset %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.
    
    
@RPC(call_type='upload')   
def upload_dataset(dataset_filename, project_id):
    '''
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    dataset = sc.loadobj(dataset_filename)
    datasetname = sc.uniquename(dataset.name, namelist=proj.datasets.keys())
    dataset.name = datasetname # Reset the name
    proj.datasets[datasetname] = dataset
    save_project(proj) # Save the new project in the DataStore.
    return datasetname # Return the new project UID in the return message.


##################################################################################
### Scenario functions and RPCs
##################################################################################

def is_included(prog_set, program, default_included):
    if (program.name in prog_set) or (program.base_cov and default_included and 'WASH' not in program.name):
        answer = True
    else:
        answer = False
    return answer
    

def py_to_js_scen(py_scen, proj, key=None, default_included=False):
    ''' Convert a Python to JSON representation of a scenario '''
    prog_names = proj.dataset().prog_names()
    scen_years = proj.dataset().t[1] - proj.dataset().t[0] # First year is baseline
    attrs = ['name', 'active', 'scen_type', 'model_name']
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
        
        # Calculate values
        if this_spec['included']:
            count += 1
            try:
                this_spec['vals'] = list(py_scen.vals[count]) # Ensure it's a list
            except:
                this_spec['vals'] = [None]
            while len(this_spec['vals']) < scen_years: # Ensure it's the right length
                this_spec['vals'].append(None)
        else:
            this_spec['vals'] = [None]*scen_years # WARNING, kludgy way to extract the number of years
        
        # Add formatting
        for y in range(len(this_spec['vals'])):
            try:
                if this_spec['vals'][y] in [None, '', 'nan'] or sc.isnumber(this_spec['vals'][y], isnan=True): # It's None or Nan
                    this_spec['vals'][y] = None
                else:
                    
                    if js_scen['scen_type'] == 'coverage': # Convert to percentage
                        this_spec['vals'][y] = str(round(100*this_spec['vals'][y])) # Enter to the nearest percentage
                    elif js_scen['scen_type'] == 'budget': # Add commas
                        this_spec['vals'][y] = format(int(round(this_spec['vals'][y])), ',') # Add commas
                    else:
                        errormsg = 'Could not recognize scenario type %s, must be budget or coverage' % js_scen['scen_type']
                        raise Exception(errormsg)
            except Exception as E:
                this_spec['vals'][y] = str(E) # If all else fails, set it to the error message
        this_spec['base_cov'] = str(round(program.base_cov*100)) # Convert to percentage -- this should never be None or Nan
        this_spec['base_spend'] = format(int(round(program.base_spend)), ',')
        js_scen['progvals'].append(this_spec)
        js_scen['t'] = [proj.dataset().t[0]+1, proj.dataset().t[1]] # First year is baseline year
    return js_scen
    
    
def js_to_py_scen(js_scen):
    ''' Convert a JSON to Python representation of a scenario '''
    py_json = sc.odict()
    for attr in ['name', 'scen_type', 'model_name', 'active']: # Copy these directly
        py_json[attr] = js_scen[attr]
    py_json['progvals'] = sc.odict() # These require more TLC
    for js_spec in js_scen['progvals']:
        if js_spec['included']:
            py_json['progvals'][js_spec['name']] = []
            vals = []
            for y in range(len(js_spec['vals'])):
                try:
                    val = numberify(js_spec['vals'][y], blank='nan', invalid='die', aslist=False)
                    vals.append(val)
                except:
                    errormsg = 'Value "%s" for "%s" could not be converted to a number' % (js_spec['vals'][y], js_spec['name'])
                    raise Exception(errormsg)
                if js_scen['scen_type'] == 'coverage': # Convert from percentage
                        if vals[y] is not None:
                            if sc.isnumber(vals[y], isnan=False) and not (vals[y]>=0 and vals[y]<=100):
                                errormsg = 'Value "%s" for "%s" should be a percentage (between 0 and 100)' % (vals[y], js_spec['name'])
                                raise Exception(errormsg)
                            vals[y] = vals[y]/100. # Convert from percentage
            py_json['progvals'][js_spec['name']] += vals
    return py_json
    

@RPC()
def get_scen_info(project_id, key=None, verbose=False):
    print('Getting scenario info...')
    proj = load_project(project_id, die=True)
    scenario_jsons = []
    for py_scen in proj.scens.values(): # Loop over all Scens in Project
        js_scen = py_to_js_scen(py_scen, proj, key=key)
        scenario_jsons.append(js_scen)
    if verbose:
        print('JavaScript scenario info:')
        sc.pp(scenario_jsons)
    return scenario_jsons


@RPC()
def set_scen_info(project_id, scenario_jsons, verbose=False):
    print('Setting scenario info...')
    proj = load_project(project_id, die=True)
    proj.scens.clear()
    for j,js_scen in enumerate(scenario_jsons):
        print('Setting scenario %s of %s...' % (j+1, len(scenario_jsons)))
        json = js_to_py_scen(js_scen)
        proj.add_scen(json=json)
        if verbose:
            print('Python scenario info for scenario %s:' % (j+1))
            sc.pp(json)
    print('Saving project...')
    save_project(proj)
    return None


@RPC()
def get_default_scen(project_id, scen_type=None, verbose=False):
    print('Creating default scenario...')
    if scen_type is None:
        scen_type = 'coverage'
    proj = load_project(project_id, die=True)
    py_scen = proj.demo_scens(doadd=False, default=True, scen_type=scen_type)
    py_scen.scen_type = scen_type # Set the scenario type -- Warning, is this needed?
    js_scen = py_to_js_scen(py_scen, proj, default_included=True)
    if verbose:
        print('Created default JavaScript scenario:')
        sc.pp(js_scen)
    return js_scen


@RPC()
def get_default_scen2(project_id, scen_type=None, model_name=None, verbose=False):
    print('Creating default scenario...')
    if scen_type is None:
        scen_type = 'coverage'
    proj = load_project(project_id, die=True)
    py_scen = make_default_scen(model_name, model=proj.model(model_name), scen_type=scen_type, basename='Default scenario (%s)' % scen_type)
    py_scen.scen_type = scen_type # Set the scenario type -- Warning, is this needed?
    js_scen = py_to_js_scen(py_scen, proj, default_included=True)
    if verbose:
        print('Created default JavaScript scenario:')
        sc.pp(js_scen)
    return js_scen


@RPC()
def convert_scen(project_id, scenkey=None):
    print('Converting scenario...')
    proj = load_project(project_id, die=True)
    proj.convert_scen(scenkey)
    save_project(proj)
    return None


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
    
    # Get cost-effectiveness table
    costeff = nu.get_costeff(project=proj, results=proj.result('scens'))
    table = reformat_costeff(costeff)
    
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
            val = numberify(item['weight'], blank='zero', invalid='die', aslist=False)
            json['weights'][key] = val
    except Exception as E:
        print('Unable to convert "%s" to weights' % js_optim['weightslist'])
        raise E
    jsm = js_optim['mults']
    if not jsm: jsm = 1.0
    if sc.isstring(jsm):
        jsm = jsm.split(',')
    vals = numberify(jsm, blank='die', invalid='die', aslist=True)
    json['mults'] = vals
    json['add_funds'] = numberify(js_optim['add_funds'], blank='zero', invalid='die', aslist=False)
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
def get_default_optim2(project_id):
    print('Getting default optimization...')
    proj = load_project(project_id, die=True)
    py_optim = proj.demo_optims(doadd=False)[0]
#    py_scen = make_default_scen(model_name, model=proj.model(model_name), scen_type=scen_type, basename='Baseline')
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
### Geospatial functions and RPCs
##################################################################################


def py_to_js_geo(py_geo, proj, key=None, default_included=False):
    ''' Convert a Python to JSON representation of an optimization '''
    obj_labels = nu.pretty_labels(direction=True).values()
    prog_names = proj.dataset().prog_names()
    js_geo = {}
    attrs = ['name', 'modelnames', 'mults', 'add_funds', 'fix_curr', 'fix_regionalspend', 'filter_progs']
    for attr in attrs:
        js_geo[attr] = getattr(py_geo, attr) # Copy the attributes into a dictionary
    weightslist = [{'label':item[0], 'weight':abs(item[1])} for item in zip(obj_labels, py_geo.weights)] # WARNING, ABS HACK
    js_geo['weightslist'] = weightslist
    js_geo['spec'] = []
    for prog_name in prog_names:
        program = proj.model(key).prog_info.programs[prog_name]
        this_spec = {}
        this_spec['name'] = prog_name
        this_spec['included'] = is_included(py_geo.prog_set, program, default_included)
        js_geo['spec'].append(this_spec)
    js_geo['objective_options'] = obj_labels # Not modified but used on the FE
    js_geo['dataset_selections'] = []
    for key in proj.datasets.keys():
        active = key in js_geo['modelnames']
        selection = {'name':key, 'active':active}
        js_geo['dataset_selections'].append(selection)
    return js_geo
    
    
def js_to_py_geo(js_geo):
    ''' Convert a JSON to Python representation of an optimization '''
    obj_keys = nu.default_trackers()
    json = sc.odict()
    attrs = ['name', 'modelnames', 'fix_curr', 'fix_regionalspend', 'filter_progs']
    for attr in attrs:
        json[attr] = js_geo[attr]
    try:
        json['weights'] = sc.odict()
        for key,item in zip(obj_keys,js_geo['weightslist']):
            val = numberify(item['weight'], blank='zero', invalid='die', aslist=False)
            json['weights'][key] = val
    except Exception as E:
        print('Unable to convert "%s" to weights' % js_geo['weightslist'])
        raise E
    jsm = js_geo['mults']
    if not jsm: jsm = 1.0
    if sc.isstring(jsm):
        jsm = jsm.split(',')
    vals = numberify(jsm, blank='die', invalid='die', aslist=True)
    json['mults'] = vals
    json['add_funds'] = numberify(js_geo['add_funds'], blank='zero', invalid='die', aslist=False)
    json['prog_set'] = [] # These require more TLC
    for js_spec in js_geo['spec']:
        if js_spec['included']:
            json['prog_set'].append(js_spec['name']) 
    json['modelnames'] = []
    for item in js_geo['dataset_selections']:
        if item['active']: json['modelnames'].append(item['name'])
    return json
    

@RPC()
def get_geo_info(project_id):
    print('Getting optimization info...')
    proj = load_project(project_id, die=True)
    geo_jsons = []
    for py_geo in proj.geos.values():
        js_geo = py_to_js_geo(py_geo, proj)
        geo_jsons.append(js_geo)
    print('JavaScript optimization info:')
    sc.pp(geo_jsons)
    return geo_jsons


@RPC()
def set_geo_info(project_id, geo_jsons):
    print('Setting optimization info...')
    proj = load_project(project_id, die=True)
    proj.geos.clear()
    for j,js_geo in enumerate(geo_jsons):
        print('Setting optimization %s of %s...' % (j+1, len(geo_jsons)))
        json = js_to_py_geo(js_geo)
        print('Python optimization info for optimization %s:' % (j+1))
        print(json)
        proj.add_geo(json=json)
    print('Saving project...')
    save_project(proj)   
    return None
    

@RPC()
def get_default_geo(project_id):
    print('Getting default optimization...')
    proj = load_project(project_id, die=True)
    py_geo = proj.demo_geos(doadd=False)[0]
    js_geo = py_to_js_geo(py_geo, proj, default_included=True)
    print('Created default JavaScript optimization:')
    sc.pp(js_geo)
    return js_geo


@RPC()
def get_default_geo2(project_id):
    print('Getting default optimization...')
    proj = load_project(project_id, die=True)
    py_geo = proj.demo_geos(doadd=False)[0]
    #    py_scen = make_default_scen(model_name, model=proj.model(model_name), scen_type=scen_type, basename='Baseline')
    js_geo = py_to_js_geo(py_geo, proj, default_included=True)
    print('Created default JavaScript optimization:')
    sc.pp(js_geo)
    return js_geo


@RPC()
def plot_geospatial(project_id, cache_id):
    proj = load_project(project_id, die=True)
    proj = retrieve_results(proj)
    figs = proj.plot(key=cache_id, geo=True) # Only plot allocation
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
def export_results(project_id, cache_id):
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    proj = retrieve_results(proj)
    file_name = '%s outputs.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    proj.write_results(full_file_name, key=cache_id)
    print(">> export_results %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def export_graphs(project_id, cache_id):
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    proj = retrieve_results(proj)
    file_name = '%s graphs.pdf' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    figs = proj.plot(key=cache_id) # Generate the plots
    sc.savefigs(figs, filetype='singlepdf', filename=full_file_name)
    print(">> export_graphs %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.

