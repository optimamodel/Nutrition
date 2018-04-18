from hptool import odict, uuid, today, version, gitinfo, objrepr, getdate
from hptool import printv, makefilepath, saveobj, dcp
from hptool import Burden, Interventions


#######################################################################################################
## Project class -- this contains everything else!
#######################################################################################################

class Project(object):
    """
    PROJECT

    The main HealthPrior project class. Almost all functionality is provided by this class.

    An HP project is based around 4 major lists:
        1. burdens -- an odict of burden data
        2. intervs -- an odict of program sets
        3. optims -- an odict of optimization structures
        4. results -- an odict of results associated with the choices above


    Methods for structure lists:
        1. add -- add a new structure to the odict
        2. remove -- remove a structure from the odict
        3. copy -- copy a structure in the odict
        4. rename -- rename a structure in the odict

    Version: 2017oct30
    """



    #######################################################################################################
    ### Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################

    def __init__(self, name='default', burdenfile=None, interventionsfile=None, country=None, verbose=2, **kwargs):
        ''' Initialize the project '''

        ## Define the structure sets
        self.burdensets  = odict()
        self.intersets   = odict()
        self.optims      = odict()
        self.results     = odict()

        ## Define other quantities
        self.name = name
        self.country = country
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        self.version = version
        self.gitinfo = gitinfo(__file__)
        self.filename = None # File path, only present if self.save() is used
        self.warnings = None # Place to store information about warnings (mostly used during migrations)

        ## Load burden spreadsheet, if available
        if burdenfile:
            burden = Burden(project=self)
            burden.loaddata(filename=burdenfile)
            self.burdensets['default'] = burden
        
        ## Load interventions spreadsheet, if available
        if interventionsfile:
            interventions = Interventions(project=self)
            interventions.loaddata(filename=interventionsfile)
            self.intersets['default'] = interventions

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = objrepr(self)
        output += '      Project name: %s\n'    % self.name
        output += '           Country: %s\n'    % self.country
        output += '\n'
        output += '       Burden sets: %i\n'    % len(self.burdensets)
        output += ' Intervention sets: %i\n'    % len(self.intersets)
        output += '     Optimizations: %i\n'    % len(self.optims)
        output += '      Results sets: %i\n'    % len(self.results)
        output += '\n'
        output += '        HP version: %s\n'    % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '        Git branch: %s\n'    % self.gitinfo['branch']
        output += '          Git hash: %s\n'    % self.gitinfo['hash']
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
#        output += self.getwarnings(doprint=False) # Don't print since print later
        return output
    
    
    def getinfo(self):
        ''' Return an odict with basic information about the project'''
        info = odict()
        for attr in ['name', 'version', 'created', 'modified', 'gitbranch', 'gitversion', 'uid']:
            info[attr] = getattr(self, attr) # Populate the dictionary
#        info['parsetkeys'] = self.parsets.keys()
#        info['progsetkeys'] = self.parsets.keys()
        return info
    
    
    def addwarning(self, message=None, **kwargs):
        ''' Add a warning to the project, which is printed when migrated or loaded '''
        if not hasattr(self, 'warnings') or type(self.warnings)!=str: # If no warnings attribute, create it
            self.warnings = ''
        self.warnings += '\n'*3+str(message) # # Add this warning
        return None


    def getwarnings(self, doprint=True):
        ''' Tiny method to print the warnings in the project, if any '''
        if hasattr(self, 'warnings') and self.warnings: # There are warnings
            output = '\nWARNING: This project contains the following warnings:'
            output += str(self.warnings)
        else: # There are no warnings
            output = ''
        if output and doprint: # Print warnings if requested
            print(output)
        return output
    
    
    def save(self, filename=None, folder=None, saveresults=False, verbose=2):
        ''' Save the current project, by default using its name, and without results '''
        fullpath = makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext='prj', sanitize=True)
        self.filename = fullpath # Store file path
        if saveresults:
            saveobj(fullpath, self, verbose=verbose)
        else:
            tmpproject = dcp(self) # Need to do this so we don't clobber the existing results
#            tmpproject.restorelinks() # Make sure links are restored
            tmpproject.cleanresults() # Get rid of all results
            saveobj(fullpath, tmpproject, verbose=verbose) # Save it to file
            del tmpproject # Don't need it hanging around any more
        return fullpath


    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def burden(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active burden set, i.e. self.burdensets[-1] '''
        try:    return self.burdensets[key]
        except: return printv('Warning, burden set not found!', 1, verbose) # Returns None
    
    def inter(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active interventions set, i.e. self.intersets[-1] '''
        try:    return self.intersets[key]
        except: return printv('Warning, interventions set not found!', 1, verbose) # Returns None
    
    def cleanresults(self):
        ''' Remove all results '''
        for key,result in self.results.items():
            self.results.pop(key)
        return None
        

