import nutrition.ui as nu
import pytest
import sciris as sc

inputdir = nu.ONpath/'inputs'
testdir = nu.ONpath/'tests'
tempdir = testdir/'temp'

# Test locale workflow
def test_translation_workflow():


    P = nu.Project('eg')

    # Check that loading a databook sets the project locale
    P.load_data(inputspath=inputdir/'fr'/'demo_demo_input.xlsx')
    assert P.locale == 'fr'

    # Once data is loaded, check that further data must have the same locale
    # This is to avoid mixing program names in different languages across regions
    with pytest.raises(Exception):
        P.load_data(inputspath=inputdir / 'en' / 'demo_region1_input.xlsx')

    # Check that we can continue loading the correct locale
    P.load_data(inputspath=inputdir/'fr'/'demo_region1_input.xlsx')



if __name__ == '__main__':
    test_translation_workflow()
