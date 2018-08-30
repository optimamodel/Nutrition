# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima Nutrition can be used as

import nutrition as on

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

Version: 2018jun26 by cliffk
"""


#####################################################################################################################
### Load Optima Nutrition functions and classes
#####################################################################################################################

# Core functions
from .version import version as __version__, versiondate as __versiondate__ # Specify the version, for the purposes of figuring out which version was used to create a project
from . import utils
from . import populations
from . import data
from . import settings
from . import programs
from . import scenarios
from . import optimization
from . import project
from . import plotting
from . import results
from . import ui
