import polib
import json
import pathlib

rootdir = pathlib.Path(__file__).parent

# # Update the pot file
with open(rootdir / 'translations.txt') as f:
    pot = polib.POFile()
    for s in f:
        entry = polib.POEntry(msgid = s.strip(),msgctxt = 'databook')
        pot.append(entry)
    # pot.save(rootdir / f'databook.pot')


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

#
# import pandas as pd
# source = "en"
# translations = pd.read_csv("translations.csv", index_col=source)
# translations = translations.drop(['notes'], axis=1, errors='ignore')
# assert not translations.index.duplicated().any()
#
#
# po = polib.POFile()
# for a, b in translations[locale].dropna().items():
#     entry = polib.POEntry(msgid=a.strip(),msgstr=b.strip(), msgctxt='databook')
#     po.append(entry)
# po.save(po_fname)


#
# po_fname = rootdir / f'excel_{locale}.po'
#
#
#
# po_msgs = []
#
#
#
# locales = ['en','fr']
#
# for locale in locales:
#     pathlib.Path(rootdir/locale).mkdir(parents=True, exist_ok=True)
#     po_fname = rootdir/locale/f'excel_{locale}.po'
#     if exist(po_fname):
#         po = polib.pofile(po_fname)
#     else:
#         po = polib.POFile()
#
#     po_msgs = []
#
#     with open(rootdir / 'translations.txt') as f:
#         for s in f:
#             print(s)
#
#
#     po.save(rootdir/f'{locale.stem}.po')
#
#
#
#
#     po.save(po_fname)
#
# #
# #
# #
# #
# #
# # strs = .readlines()
# #
# # def flatten(d,out,prefix=()):
# #     for k,v in d.items():
# #         if isinstance(v, dict):
# #             flatten(v, out, prefix + (k,))
# #         else:
# #             out[prefix + (k,)] = v
# #
# # for locale in rootdir.iterdir():
# #     if locale.suffix != '.json':
# #         continue
# #
# #     with open(locale, encoding='utf-8') as f:
# #         d = json.load(f)
# #
# #     out = {}
# #     flatten(d, out)
# #
# #     po = polib.POFile()
# #
# #     # po.metadata = {
# #     #     'Project-Id-Version': '1.0',
# #     #     'Report-Msgid-Bugs-To': 'you@example.com',
# #     #     'POT-Creation-Date': '2007-10-18 14:00+0100',
# #     #     'PO-Revision-Date': '2007-10-18 14:00+0100',
# #     #     'Last-Translator': 'you <you@example.com>',
# #     #     'Language-Team': 'English <yourteam@example.com>',
# #     #     'MIME-Version': '1.0',
# #     #     'Content-Type': 'text/plain; charset=utf-8',
# #     #     'Content-Transfer-Encoding': '8bit',
# #     # }
# #
#
#


