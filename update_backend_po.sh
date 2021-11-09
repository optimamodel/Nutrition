#!/bin/bash

# Run this script if
# - Any new strings have been added to translations.txt
# - Any new strings have been added to the codebase
# - Any new strings have been added to the frontend
# - Any changes have been made to any `.po` files

python setup.py extract_messages # Read the backend source code and build the pot file
python setup.py update_catalog # Update the backend po files with new entries from the pot file
python inputs/sync_backend_po.py # Merge translations from the databook po files to ensure consistency
python setup.py compile_catalog --use-fuzzy # Compile the catalog into mo files

(cd client && npm run translate ) # vue->json
python client/src/locales/json_to_po.py # json -> po (this will add any new strings in the FE to the po file)
python client/src/locales/po_to_json.py # update client jsons (this will add any translations in the po file back to the json)
