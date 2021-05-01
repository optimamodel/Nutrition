# Optima Nutrition

Welcome to Optima Nutrition. Documentation is currently in progress.

## Installation

Run `python setup.py develop` in the root folder.

## Usage

Run `python tests/testdemo.py` to test.

## Localization (Python)

To update strings (after adding new strings in code). This creates `nutrition/locale/nutrition.pot`

    python setup.py extract_messages
    python setup.py update_catalog

To set up a new locale e.g. `en`. This creates `nutrition/locale/en/LC_MESSAGES/nutrition.po`

    python setup.py init_catalog -l en

To update translations (after modifying translated text)

    python setup.py compile_catalog

Normal workflow would be

1. Add `_ = utils.get_translator(locale)` in the appropriate scope. `utils.locale` contains the fallback/default locale
2. Modify strings to be passed through `_` for translation
3. Run the extract messages and update catalog steps above
4. Edit the `.po` files to populate the translations
5. Compile the catalog
6. Commit all files

## Localization (Vue)

See client readme