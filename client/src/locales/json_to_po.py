import polib
import json
import pathlib

rootdir = pathlib.Path(__file__).parent

def flatten(d,out,prefix=()):
    for k,v in d.items():
        if isinstance(v, dict):
            flatten(v, out, prefix + (k,))
        else:
            out[prefix + (k,)] = v

for locale in rootdir.iterdir():
    if locale.suffix != '.json':
        continue

    with open(locale, encoding='utf-8') as f:
        d = json.load(f)

    out = {}
    flatten(d, out)

    po = polib.POFile()

    # po.metadata = {
    #     'Project-Id-Version': '1.0',
    #     'Report-Msgid-Bugs-To': 'you@example.com',
    #     'POT-Creation-Date': '2007-10-18 14:00+0100',
    #     'PO-Revision-Date': '2007-10-18 14:00+0100',
    #     'Last-Translator': 'you <you@example.com>',
    #     'Language-Team': 'English <yourteam@example.com>',
    #     'MIME-Version': '1.0',
    #     'Content-Type': 'text/plain; charset=utf-8',
    #     'Content-Transfer-Encoding': '8bit',
    # }

    for k,v in out.items():
        entry = polib.POEntry(
            msgid = k[-1],
            msgstr = v,
            msgctxt = '.'.join(k[:-1]),
        )
        po.append(entry)

    po.save(rootdir/f'{locale.stem}.po')




