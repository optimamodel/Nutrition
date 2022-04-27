# Convert JSON to PO
# This will ensure that every JSON item has a corresponding PO entry
# but will NOT copy over any translations
# After running vue-i18n-extract, the JSON files will contain all of the keys that
# need to be translated

import polib
import json
import pathlib

rootdir = pathlib.Path(__file__).parent

def flatten(d, out, prefix=()):
    for k, v in d.items():
        if isinstance(v, dict):
            flatten(v, out, prefix + (k,))
        else:
            out[prefix + (k,)] = v


for locale in rootdir.iterdir():
    if locale.suffix != ".json":
        continue

    with open(locale, encoding="utf-8") as f:
        d = json.load(f)

    out = {}  # These are the strings defined in the json file
    flatten(d, out)

    # Produce a temporary pot file
    pot = polib.POFile()
    for k, v in out.items():
        entry = polib.POEntry(
            msgid=k[-1],
            msgstr="",
            msgctxt=".".join(k[:-1]) if k[:-1] else None,
        )
        pot.append(entry)

    # Merge it with the existing po file
    po_fname = rootdir / f"client_{locale.stem}.po"
    if po_fname.exists():
        po = polib.pofile(po_fname)
    else:
        po = polib.POFile()
    po.merge(pot)
    po.save(po_fname)

