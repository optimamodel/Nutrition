# Set msgctxt in nutrition.pot based on databook.pot
# That is, flag in the template file which translations will come from the databook
from pathlib import Path
import polib
import nutrition.ui as nu

# Load translations from Excel
rootdir = Path(__file__).parent
source_po = polib.pofile(rootdir/'databook.pot')
target_po = polib.pofile(nu.ONpath / "nutrition" / "locale" / 'nutrition.pot')

source_entries = {x.msgid:x for x in source_po}
for entry in target_po:
    if entry.msgid in source_entries:
        entry.msgctxt = 'databook'
target_po.save()
