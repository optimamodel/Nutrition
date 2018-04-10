#!/usr/bin/env python

# Load Sciris
from sciris.api import makeapp
from hptool.webapp import config

app = makeapp(config=config) # Create the app
app.run() # Run the server