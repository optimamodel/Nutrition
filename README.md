# Optima Nutrition

Welcome to Optima Nutrition. Documentation is currently in progress.

## Installation

Run `python setup.py develop` in the root folder.

## Usage

Run `python tests/testdemo.py` to test.

## Localization

To update strings (after adding new strings in code). This creates `nutrition/locale/nutrition.pot`

    python setup.py extract_messages
    python setup.py update_catalog

To set up a new locale e.g. `en`. This creates `nutrition/locale/en/LC_MESSAGES/nutrition.po`

    python setup.py init_catalog -l en

To update translations (after modifying translated text)

    python setup.py compile_catalog

