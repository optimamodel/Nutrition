#!/bin/bash

# Run this script if
# - Any new strings have been added to translations.txt
# - Any new strings have been added to the codebase
# - Any new strings have been added to the frontend
# - Any changes have been made to any `.po` files (except those relating to the backend)

python setup.py extract_messages # Read the backend source code and build the pot file
python inputs/sync_backend_pot.py # Set the databook msgctxt flags before merging
python setup.py update_catalog # Update the backend catalogs with translation entries
python inputs/sync_backend_po.py # Pre-populate translations from the databook to ensure consistency
python setup.py compile_catalog # Compile the catalog into mo files

# TODO - the frontend translations are a bit messier because json_to_po recreates the entire file
# therefore making it hard to repeatedly run it
#(cd client && npm run translate ) # vue->json
#python client/src/locales/json_to_po.py # json -> po
#python client/src/locales/po_to_json.py # update client jsons
