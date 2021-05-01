# Excel translations

The reference files are in `inputs/en`. Remaining files are automatically generated using `translate.py`. This script does the following for each file in `en`:

- Copy file to locale folder e.g. `fr`
- Finds and replaces all strings matched in `translations.xlsx`

Therefore, `translate.py` generated translated versions of the `en` files.

To preserve the files as precisely as possible, the translation is carried out by remote-controlling Microsoft Excel. Therefore, **this script can only be run on a Windows machine with Microsoft Excel installed**.
