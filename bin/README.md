# Bin folder

This folder contains the executable files for various tasks. On Mac/Linux, files have executable permission, so you can just type `./the-file.py`; you don't need to type `python the-file.py` (although that works too).

## Quick start

* `run.py` includes the three steps required for a first (or subsequent) run: it installs the node modules, builds the client, and starts the server.

## Setup scripts

* `install_client.py` installs the node modules; it's simply a link to `npm install` in the client folder.

* `build_client.py` builds the client; it's a link to `npm run build` in the client folder.

## Run scripts

* `start_server.py` starts the main server. Note, this will only work after `build_client.py` has been run.

* `start_dev_client.py` and `start_dev_server.py` load the client and server in "development" mode, i.e. with hot reloading (so changes you make appear automatically). You need to run _both_ of these in order for the development version to run. Note that if you use development mode, you do _not_ need to run `build_client.py`.

* `linux_dev_run` executes `start_dev_client.py` and `start_dev_server.py` in new `gnome-terminal` windows, so you can start the development version with one command.

## Other

* `reset_database.py` deletes all data from the database: all users, projects, blobs, etc.
