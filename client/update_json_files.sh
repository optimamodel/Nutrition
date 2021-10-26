#!/bin/bash

npm run translate # vue->json
python src/locales/json_to_po.py # json -> po
