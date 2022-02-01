import concurrent.futures
import os
from pathlib import Path
import polib
import win32com.client

# Load translations from Excel
rootdir = Path(__file__).parent
source = "en"

if __name__ != '__main__':
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = True

def translate(x):
    """
    Translate all Excel files from source to target locale

    :param source: Path to English databook (including xlsx extension)
    :param dest: Path to write translated databook to (including xlsx extension)
    :param target_locale: A string like 'fr'

    :return: None - translated Excel files are written directly

    """

    source, dest, target_locale = x

    po = polib.pofile(rootdir / target_locale / "databook.po")

    wb = excel.Workbooks.Add(str(source.resolve()))

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
            rg.Replace(a, b, LookAt=1, MatchCase=True)  # LookAt=1 is equivalent to "xlWhole" i.e. match entire cell. Otherwise functions get overwritten

        sheet.Protect("nick")  # Restore protection
        sheet.Visible = visible

    for property in wb.BuiltinDocumentProperties:
        if property.name == "Keywords":
            property.value = f"lang={target_locale}"
            break

    wb.Worksheets(1).Activate()  # Leave the first sheet open

    # save as
    if dest.exists():
        os.remove(dest)
    wb.SaveAs(str(dest.resolve()))
    wb.Close(True)

    # excel.Quit()



if __name__ == '__main__':

    excel_files = list((rootdir/'en').glob("**/*.xlsx")) # List of all databooks
    locales = [x.parent.stem for x in rootdir.glob("**/*.po")]  # List of all locales (folders containing a `.po` file) e.g. ['fr']

    # Assemble arguments
    to_translate = []
    for locale in locales:
        for f in excel_files:
            to_translate.append((f, rootdir/locale/f.relative_to(rootdir/'en'), locale)) # List of tuples ('en/databook.xlsx','fr/databook.xlsx', 'fr')

    # Dispatch to workers
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(translate, to_translate)
