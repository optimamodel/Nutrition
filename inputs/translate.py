import xlwings as xw
import pandas as pd
from pathlib import Path
import shutil
import os
import win32com.client
from pathlib import Path


excel = win32com.client.Dispatch('Excel.Application')
excel.Visible = True

translations = pd.read_excel('translations.xlsx',index_col='Message_code')

# Here, translate from Message_En to
source = 'Message_En'
target = 'Message_Fr'
target_locale = 'fr'

source_dir = Path('en')
dest = Path(target_locale)
for source_file in source_dir.iterdir():
    if not source_file.suffix=='.xlsx':
        continue

    wb = excel.Workbooks.Add(str(source_file.resolve()))

    print(source_file.name)

    for sheet in wb.Sheets:
        print('\t'+sheet.Name)

        sheet.Activate()
        sheet.Unprotect('nick') # Need to unprotect, otherwise it will not replace cell values correctly

        rg = sheet.UsedRange

        for a, b in translations[[source, target]].values:

            # Translate the sheet name
            if sheet.Name == a:
                sheet.Name = b

            # Substitute cell content
            rg.Replace(a, b)


        sheet.Protect('nick') # Need to unprotect, otherwise it will not replace cell values correctly

    for property in wb.BuiltinDocumentProperties:
        if property.name == 'Keywords':
            property.value = f'lang={target_locale}'
            break

    wb.Worksheets(1).Activate() # Leave the first sheet open


    # save as
    dest_file = (dest/source_file.name).resolve()
    if dest_file.exists():
        os.remove(dest_file)
    wb.SaveAs(str(dest_file))
    wb.Close(True)

excel.Quit()
