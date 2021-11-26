import nutrition.ui as nu
import pytest
import sciris as sc
import matplotlib.pyplot as plt

testdir = nu.ONpath / "tests"
tempdir = testdir / "temp"

if not tempdir.exists():
    tempdir.mkdir(exist_ok=True, parents=True)

@pytest.fixture(scope="module", params=nu.available_locales)
def project(request):
    return nu.demo(scens=True, optims=True, geos=True, locale=request.param)


def test_uncertainty(project):
    P = sc.dcp(project)
    P.run_scens(n_samples=5)
    P.plot()
    plt.close('all')
    P.write_results(tempdir/f"{P.locale}_uncertainty_results.xlsx")


if __name__ == "__main__":
    for locale in nu.available_locales:
        project = nu.demo(scens=True, locale=locale)
        test_uncertainty(project)
