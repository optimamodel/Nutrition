import nutrition.ui as nu
import pytest

inputdir = nu.ONpath / "inputs"
testdir = nu.ONpath / "tests"
tempdir = testdir / "temp"

excel_files = list((inputdir).glob("**/*.xlsx"))  # List of all databooks
excel_files = [x for x in excel_files if 'template' not in x.stem and not x.stem.startswith('~')]

@pytest.mark.parametrize('path', excel_files)
def test_databook(path):
    P = nu.Project("test")
    P.load_data(inputspath=path)
    print(f"Successfully loaded {path}")


if __name__ == "__main__":
    for path in excel_files:
        test_databook(path)
