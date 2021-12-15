# Converts PO to JSON
# This will bring in any translations from the PO file
# Extraneous keys will be added back in
import polib
import json
import pathlib
import sciris as sc

rootdir = pathlib.Path(__file__).parent

for locale in rootdir.iterdir():
    if locale.suffix != '.po':
        continue

    d = {}

    po = polib.pofile(locale.resolve())
    for entry in po:
        k = entry.msgctxt.split('.') if entry.msgctxt else []
        k.append(entry.msgid)
        k = tuple(k)
        try:
            sc.setnested(d, k, entry.msgstr)
        except Exception as E:
            raise Exception(f'Could not set {entry} ({k}) ({entry.msgstr})') from E

    with open(rootdir/f'{locale.stem.replace("client_","")}.json','w', encoding='utf-8') as f:
        json.dump(d,f, indent=2, ensure_ascii=False)




