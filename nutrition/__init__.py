# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so HealthPrior (HP) can be used either as

from hptool import Project
or
import hptool as hp
or
from hptool import *

Now, the legal part:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Version: 2018jun04 by cliffk
"""

# Specify the version, for the purposes of figuring out which version was used to create a project
from .version import version, versiondate

# Print the license
ONlicense = 'Optima Nutrition %s (%s)' % (version, versiondate)
print(ONlicense)


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
    outstr += '   Path:    %s\n' % HPpath()
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



#####################################################################################################################
### Load Optima Nutrition functions and classes
#####################################################################################################################

# Core functions
from . import project
from . import scenarios
from . import data
from . import plotting
from . import settings

# Import webapp
import webapp



