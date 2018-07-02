# Import only the functions that are actually needed for the user
from .version import version, versiondate # analysis:ignore
from .project import Project, demo # analysis:ignore


#####################################################################################################################
### Define debugging and exception functions/classes
#####################################################################################################################

# Tool path
def ONpath(subdir=None, trailingsep=True):
    ''' Returns the parent path of the Optima Nutrition module. If subdir is not None, include it in the path '''
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        tojoin = [path, subdir]
        if trailingsep: tojoin.append('') # This ensures it ends with a separator
        path = os.path.join(*tojoin) # e.g. ['/home/optima', 'tests', '']
    return path


# Debugging information
def debuginfo(output=False):
    import sciris.core as sc
    outstr = '\nOptima Nutrition debugging info:\n'
    outstr += '   Version: %s\n' % version
    outstr += '   Branch:  %s\n' % sc.gitinfo()['branch']
    outstr += '   SHA:     %s\n' % sc.gitinfo()['hash']
    outstr += '   Date:    %s\n' % sc.gitinfo()['date']
    outstr += '   Path:    %s\n' % ONpath()
    if output:
        return outstr
    else: 
        print(outstr)
        return None

class ONException(Exception):
    ''' A tiny class to allow for Optima-specific exceptions -- define this here to allow for Optima-specific info '''
    
    def __init__(self, errormsg, *args, **kwargs):
        if isinstance(errormsg, basestring): errormsg = errormsg+debuginfo(dooutput=True) # If it's not a string, not sure what it is, but don't bother with this
        Exception.__init__(self, errormsg, *args, **kwargs)