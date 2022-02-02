# Copy translations from databook.po into the backend nutrition.po
#
# This ensures that the backend code has translations that match the databook

from pathlib import Path
import polib
import nutrition.ui as nu

# Load translations from Excel
rootdir = Path(__file__).parent


def update_messages(source_po, target_po):
    # Update the .po files with translations from the CSV list, if the English text matches the message ID
    # This requires that the backend po files have already been updated from the backend source
    # This prevents strings that only appear in the databook from cluttering the backend translation
    # source_po = polib.pofile(source_po_file)
    # target_po = polib.pofile(target_po_file)

    source_entries = {x.msgid: x for x in source_po}
    for entry in target_po:
        if entry.msgid in source_entries:
            entry.msgstr = source_entries[entry.msgid].msgstr

    target_po.save()


locales = [x.parent.stem for x in rootdir.glob("**/*.po")]  # List of all locales (folders containing a `.po` file) e.g. ['fr']

for locale in locales:
    print(f"{locale}: Syncing databook -> backend")
    source_po = polib.pofile(rootdir / locale / "databook.po")
    target_po = polib.pofile(nu.ONpath / "nutrition" / "locale" / locale / "LC_MESSAGES" / "nutrition.po")
    update_messages(source_po, target_po)

    print(f"{locale}: Syncing databook -> frontend")
    source_po = polib.pofile(rootdir / locale / "databook.po")
    target_po = polib.pofile(nu.ONpath / "client" / "src" / "locales" / f"client_{locale}.po")
    update_messages(source_po, target_po)

    print(f"{locale}: Syncing backend -> frontend")
    source_po = polib.pofile(nu.ONpath / "nutrition" / "locale" / locale / "LC_MESSAGES" / "nutrition.po")
    target_po = polib.pofile(nu.ONpath / "client" / "src" / "locales" / f"client_{locale}.po")
    update_messages(source_po, target_po)
