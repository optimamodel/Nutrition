import concurrent.futures
import os
from pathlib import Path
import polib
import win32com.client
import pywintypes
import win32api

# Load translations from Excel
rootdir = Path(__file__).parent
source = "en"

if __name__ != '__main__':
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = True

def validate_sheet_names(wb, pofile):
    po = polib.pofile(pofile)

    translations = {x.msgid:x.msgstr for x in po}
    sheets = {sheet.Name:translations[sheet.Name] if sheet.Name in translations else sheet.Name for sheet in wb.Sheets}
    failed = False
    for a,b in sheets.items():
        if len(b) > 31:
            print(f'Invalid sheet name: "{a}"->"{b}"')
            failed = True
    if failed:
        for sheet in sheets:
            for entry in po:
                if sheet == entry.msgid:
                    entry.comment = 'Translation must be 31 characters or less in length'
        po.save(pofile)
        raise Exception('Invalid sheet names detected')

def reprotect(x):
    source, dest, target_locale = x
    wb = excel.Workbooks.Add(str(source.resolve()))
    wb.Unprotect("nick")

    print(source)
    for sheet in wb.Sheets:
        print("\t" + sheet.Name)
        visible = sheet.Visible
        sheet.Activate()
        try:
            sheet.Unprotect("nick")  # Need to unprotect, otherwise it will not replace cell values correctly
        except:
            sheet.Unprotect("NICK")  # Need to unprotect, otherwise it will not replace cell values correctly
        sheet.Protect("nick")  # Restore protection
    wb.Worksheets(1).Activate()  # Leave the first sheet open
    wb.SaveAs(str(source.resolve()))
    wb.Close(True)


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

    pofile =  rootdir / target_locale / "databook.po"
    validate_sheet_names(wb, pofile)

    print(source)
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
                    msg = f"Could not translate sheet name '{a}' -> '{b}'"

                    if isinstance(E, pywintypes.com_error):
                        try:
                            msg += f"(win32api error: '{win32api.FormatMessage(E.hresult).strip()}')"
                        except:
                            pass

                    raise Exception(msg) from E

            # Substitute cell content
            rg.Replace(a, b, 1, 1, True)  # LookAt=1 is equivalent to "xlWhole" i.e. match entire cell. Otherwise functions get overwritten

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

    # Use this block to translate databooks in subfolders e.g. LiST countries
    excel_files = list((rootdir/'en').glob("**/*.xlsx")) # List of all databooks
    locales = [x.parent.stem for x in rootdir.glob("**/*.po")]  # List of all locales (folders containing a `.po` file) e.g. ['fr']

    # Use this block to translate top level files only
    # excel_files = list((rootdir/'en').glob("*.xlsx")) # List of all databooks
    # locales = [x.parent.stem for x in rootdir.glob("**/*.po")]  # List of all locales (folders containing a `.po` file) e.g. ['fr']

    # Assemble arguments
    to_translate = []
    for locale in locales:
        for f in excel_files:
            to_translate.append((f, rootdir/locale/f.relative_to(rootdir/'en'), locale)) # List of tuples ('en/databook.xlsx','fr/databook.xlsx', 'fr')

    # Dispatch to workers
    # WARNING - Must be run directly in a Windows command prompt, NOT in PyCharm
    with concurrent.futures.ProcessPoolExecutor(max_workers=6) as executor:
        executor.map(translate, to_translate)

    # # ...or run debug
    # excel = win32com.client.DispatchEx("Excel.Application")
    # excel.Visible = True
    # for x in to_translate:
    #     translate(x)