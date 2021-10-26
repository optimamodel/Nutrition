import polib
import json
import pathlib
import sciris as sc

for locale in pathlib.Path('.').iterdir():
    if locale.suffix != '.po':
        continue

    d = {}

    po = polib.pofile(locale)
    for entry in po:
        k = entry.msgctxt.split('.') if entry.msgctxt else []
        k.append(entry.msgid)
        k = tuple(k)

        sc.setnested(d, k, entry.msgstr)

    with open(f'{locale.stem}_2.json','w', encoding='utf-8') as f:
        json.dump(d,f, indent=2, ensure_ascii=False)




