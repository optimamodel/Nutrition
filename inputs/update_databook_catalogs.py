# Synchronize the po files with translations.txt
#
# If any new translations are required, add the English string to translations.txt
# then run this file, and add the translation to databook.po for relevant locales

import polib
import pathlib

rootdir = pathlib.Path(__file__).parent

# Run this file if `translations.txt` changes

# # Update the pot file
with open(rootdir / 'translations.txt') as f:
    pot = polib.POFile()
    for s in f:
        entry = polib.POEntry(msgid = s.strip())
        pot.append(entry)
    pot.save(rootdir / f'databook.pot')

locales = ['fr'] # Locales for translation
for locale in locales:
    pathlib.Path(rootdir/locale).mkdir(parents=True, exist_ok=True)
    po_fname = rootdir/locale/f'databook.po'
    if po_fname.exists():
        po = polib.pofile(po_fname)
    else:
        po = polib.POFile()
    po.merge(pot)
    po.save(po_fname)


