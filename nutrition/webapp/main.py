"""
main.py -- main module for the Optima Nutrition webapp.
    
Last update: 2018jun04 by cliffk
"""

import nutrition as on
import sciris.web as sw
import sciris.core as sc


def make_app():
	# Create the ScirisApp object.  NOTE: app.config will thereafter contain all 
	# of the configuration parameters, including for Flask.
	app = sw.ScirisApp(__file__, app_config=on.webapp.config)

	# RPC definitions
	@app.register_RPC()
	def get_version_info():
		''' Return the information about the project. '''
		gitinfo = sc.gitinfo(__file__)
		version_info = {
	        'version':   on.version,
	        'date':      on.versiondate,
	        'gitbranch': gitinfo['branch'],
	        'githash':   gitinfo['hash'],
	        'gitdate':   gitinfo['date'],
		}
		return version_info

	# Register the RPCs in the project.py module.
	app.add_RPC_dict(on.webapp.api.RPC_dict)

	return app


def run():

	# Make the app
	app = make_app()
	
	# Initialize the projects.
	on.webapp.api.init_projects(app)

	# Run the client page with Flask and a Twisted server.
	app.run_server()
	return None


if __name__ == '__main__':
	run()
