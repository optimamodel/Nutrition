from pathlib import Path
import polib
import nutrition.ui as nu

# Load translations from Excel
rootdir = Path(__file__).parent


def update_messages(target_locale):
    # Update the .po files with translations from the CSV list, if the English text matches the message ID
    # This requires that the backend po files have already been updated from the backend source
    # This prevents strings that only appear in the databook from cluttering the backend translation
    source_po = polib.pofile(rootdir/target_locale/'databook.po')
    target_po = polib.pofile((nu.ONpath / "nutrition" / "locale" / target_locale / "LC_MESSAGES" / "nutrition.po"))

    source_entries = {x.msgid:x for x in source_po}
    for entry in target_po:
        if entry.msgid in source_entries:
            entry.msgstr = source_entries[entry.msgid].msgstr
            entry.msgctxt = 'databook'

    target_po.save()


locales = [x.parent.stem for x in rootdir.glob('**/*.po')] # List of all locales (folders containing a `.po` file) e.g. ['fr']

for locale in locales:
    update_messages(locale)
