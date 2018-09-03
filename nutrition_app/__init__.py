import nutrition as on

from . import config
from . import projects
from . import rpcs
from . import main
#from . import apptasks # Don't import, since this creates the Celery worker

# Print the license
print('Optima Nutrition %s (%s)' % (on.__version__, on.__versiondate__))