# Bin folder

This folder contains the executable files for various tasks. On Mac/Linux, files have executable permission, so you can just type `./the-file.py`; you don't need to type `python the-file.py` (although that works too).

## Setup scripts

* `install_client.py` installs the node modules; it's simply a link to `npm install` in the client folder.

* `build_client.py` builds the client; it's a link to `npm run build` in the client folder.

## Run scripts

* `start_server.py` starts the main server. Note, this will only work after `build_client.py` has been run.

## Other

* `reset_database.py` deletes all data from the database: all users, projects, blobs, etc.

## Updating Athena

* Log in with root privileges.
* Make sure Sciris is up to date: `cd ~/tools/sciris; gp` (`gp` is aliased to `git pull`)
* Make sure Nutrition is up to date: `cd ~/tools/nutrition; gp` (NB, make sure you're on `develop` and/or change to whatever branch you need)
* If needed, install the client (only if new node_modules have been added): `cd client; ./install_client.py`
* Build the client (assuming you're already in the `client` folder): `./build_client`
* Restart the server: `sudo service nutrition restart`
* Restart Celery (the task manager): `sudo service nutritioncelery restart`
* You should be good to go!
