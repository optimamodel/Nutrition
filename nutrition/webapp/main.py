"""
main.py -- main module for HealthPrior webapp.
    
Last update: 6/1/18 (gchadder3)
"""

import hptool as hp
import sciris.web as sw
import sciris.core as sc


def make_app():
	# Create the ScirisApp object.  NOTE: app.config will thereafter contain all 
	# of the configuration parameters, including for Flask.
	app = sw.ScirisApp(__file__, app_config=hp.webapp.config)

	# RPC definitions
	@app.register_RPC()
	def get_version_info():
		''' Return the information about the project. '''
		gitinfo = sc.gitinfo(__file__)
		version_info = {
	        'version':   hp.version,
	        'date':      hp.versiondate,
	        'gitbranch': gitinfo['branch'],
	        'githash':   gitinfo['hash'],
	        'gitdate':   gitinfo['date'],
		}
		return version_info

	# Register the RPCs in the project.py module.
	app.add_RPC_dict(hp.webapp.api.RPC_dict)

	return app


def run():

	# Make the app
	app = make_app()
	
	# Initialize the projects.
	hp.webapp.api.init_projects(app)

	# Run the client page with Flask and a Twisted server.
	app.run_server()
	return None


if __name__ == 'main':
	run()
