import xlwings as xw
import pandas as pd
from pathlib import Path
import shutil
import os
import win32com.client
from pathlib import Path
import polib
import nutrition.ui as nu

# Load translations from Excel
source = "en"
translations = pd.read_csv("translations.csv", index_col=source)
translations = translations.drop(['notes'], axis=1, errors='ignore')
assert not translations.index.duplicated().any()

def translate_databook(target):

    source_dir = Path(source)
    dest = Path(target)
    for source_file in source_dir.iterdir():
        if not source_file.suffix == ".xlsx":
            continue

        wb = excel.Workbooks.Add(str(source_file.resolve()))

        print(source_file.name)

        for sheet in wb.Sheets:
            print("\t" + sheet.Name)

            sheet.Activate()
            sheet.Unprotect("nick")  # Need to unprotect, otherwise it will not replace cell values correctly

            rg = sheet.UsedRange

            for a, b in translations[target].dropna().items():
                print(f"\t\t'{a}' -> '{b}'")

                # Translate the sheet name
                if sheet.Name == a:
                    sheet.Name = b

                # Substitute cell content
                rg.Replace(a, b, LookAt=1) # LookAt=1 is equivalent to "xlWhole" i.e. match entire cell. Otherwise functions get overwritten

            sheet.Protect("nick")  # Need to unprotect, otherwise it will not replace cell values correctly

        for property in wb.BuiltinDocumentProperties:
            if property.name == "Keywords":
                property.value = f"lang={target}"
                break

        wb.Worksheets(1).Activate()  # Leave the first sheet open

        # save as
        dest_file = (dest / source_file.name).resolve()
        if dest_file.exists():
            os.remove(dest_file)
        wb.SaveAs(str(dest_file))
        wb.Close(True)


def update_messages(target):
    # Update the .po files with translations from the CSV list, if the English text matches the message ID
    target_po = polib.pofile((nu.ONpath / "nutrition" / "locale" / target / "LC_MESSAGES" / "nutrition.po"))

    target_translations = translations[target].dropna()

    for entry in target_po:
        if entry.msgid in target_translations.index:
            entry.msgstr = target_translations[entry.msgid]
    target_po.save()


excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = True


for target in translations.columns:
    # translate_databook(target)
    update_messages(target)


excel.Quit()
