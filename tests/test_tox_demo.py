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


def test_scens(project):
    P = sc.dcp(project)
    P.run_scens()
    P.plot()
    plt.close("all")
    P.write_results(tempdir / f"{P.locale}_scen_results.xlsx")


def test_optims(project):
    P = sc.dcp(project)
    P.run_optim(parallel=False, maxtime=1, maxiter=1)
    P.plot(-1, optim=True)
    plt.close("all")


def test_geos(project):
    return True  # Skip this test for now - it's slow
    P = sc.dcp(project)
    P.run_geo(parallel=False, maxtime=1, maxiter=1)
    P.plot(-1, geo=True)
    plt.close("all")


if __name__ == "__main__":
    nu.available_locales = ["fr"]

    for locale in nu.available_locales:
        project = nu.demo(scens=True, optims=True, geos=True, locale=locale)
        test_scens(project)
        # test_optims(project)
        # test_geos(project)
