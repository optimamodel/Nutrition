"""
main.py -- main module for the Optima Nutrition webapp.
    
Last update: 2018sep19
"""

import scirisweb as sw
from . import config, rpcs, apptasks # analysis:ignore

def make_app():
    app = sw.ScirisApp(name='Optima Nutrition', filepath=__file__, config=config, RPC_dict=rpcs.RPC_dict) # Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    sw.make_default_users(app)
    return app

def run():
    app = make_app() # Make the app
    app.run() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
