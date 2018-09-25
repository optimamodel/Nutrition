# Bin folder

This folder contains the executable files for various tasks. On Mac/Linux, files have executable permission, so you can just type `./the-file.py`; you don't need to type `python the-file.py` (although that works too).

## Setup scripts

* `install_client.py` installs the node modules; it's simply a link to `npm install` in the client folder.

* `build_client.py` builds the client; it's a link to `npm run build` in the client folder.

* `dev_client.py` can be used instead of `build_client.py` to have a client that will rebuild automatically if source files are changed.

## Run scripts

* `run.py` runs the main server. Note, this will only work after `build_client.py` has been run (or while `dev_client.py` is running).

* `worker.py` starts the Celery task worker (used for optimizations).

## Other

* `reset_database.py` deletes all data from the database: all users, projects, blobs, etc.