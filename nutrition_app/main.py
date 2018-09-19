"""
main.py -- main module for the Optima Nutrition webapp.
    
Last update: 2018jul30
"""

import scirisweb as sw
from . import config, projects, rpcs, apptasks # analysis:ignore

def make_app():
    app = sw.ScirisApp(name='Optima Nutrition', filepath=__file__, config=config) # Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    app.add_RPC_dict(rpcs.RPC_dict) # Register the RPCs.
    return app

def run():
    app = make_app() # Make the app
    app.run() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
