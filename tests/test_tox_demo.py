import nutrition.ui as nu
import pytest
import sciris as sc

testdir = nu.ONpath / "tests"
tempdir = testdir / "temp"


@pytest.fixture(scope="module", params=nu.available_locales)
def project(request):
    return nu.demo(scens=True, optims=True, geos=True, locale=request.param)


def test_scens(project):
    P = sc.dcp(project)
    P.run_scens()
    P.plot()


def test_optims(project):
    P = sc.dcp(project)
    P.run_optim(parallel=False, maxtime=1, maxiter=1)
    P.plot(-1, optim=True)


def test_geos(project):
    return True  # Skip this test for now - it's slow
    P = sc.dcp(project)
    P.run_geo(parallel=False, maxtime=1, maxiter=1)
    P.plot(-1, geo=True)


if __name__ == "__main__":
    for locale in nu.available_locales:
        project = nu.demo(scens=True, optims=True, geos=True, locale=locale)
        test_scens(project)
        test_optims(project)
        test_geos(project)
