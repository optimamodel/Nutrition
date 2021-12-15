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
rootdir = Path(__file__).parent
source = "en"

def translate_databook(target_locale: str):
    """

    Translate all Excel files from source to target locale
    :param target_locale: A string like 'fr'
    :return: None - translated Excel files are written directly

    """

    po = polib.pofile(rootdir/target_locale/'databook.po')

    source_dir = Path(source)
    dest = Path(target_locale)

    for source_file in source_dir.iterdir():
        if not source_file.suffix == ".xlsx":
            continue

        wb = excel.Workbooks.Add(str(source_file.resolve()))

        print(source_file.name)

        for sheet in wb.Sheets:
            print("\t" + sheet.Name)

            visible = sheet.Visible

            sheet.Activate()
            sheet.Unprotect("nick")  # Need to unprotect, otherwise it will not replace cell values correctly
            sheet.Visible = True

            rg = sheet.UsedRange

            for entry in po:
                a = entry.msgid
                b = entry.msgstr

                # print(f"\t\t'{a}' -> '{b}'")

                # Translate the sheet name
                if sheet.Name == a:
                    try:
                        sheet.Name = b
                    except Exception as E:
                        raise Exception(f"Could not translate sheet name '{a}' -> '{b}'")

                # Substitute cell content
                rg.Replace(a, b, LookAt=1, MatchCase=True) # LookAt=1 is equivalent to "xlWhole" i.e. match entire cell. Otherwise functions get overwritten

            sheet.Protect("nick")  # Restore protection
            sheet.Visible = visible

        for property in wb.BuiltinDocumentProperties:
            if property.name == "Keywords":
                property.value = f"lang={target_locale}"
                break

        wb.Worksheets(1).Activate()  # Leave the first sheet open

        # save as
        dest_file = (dest / source_file.name).resolve()
        if dest_file.exists():
            os.remove(dest_file)
        wb.SaveAs(str(dest_file))
        wb.Close(True)


locales = [x.parent.stem for x in rootdir.glob('**/*.po')] # List of all locales (folders containing a `.po` file) e.g. ['fr']

excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = True
for locale in locales:
    translate_databook(locale)
excel.Quit()

