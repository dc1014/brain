import pytest
from System.tools.forge import operate_forge, bootstrap_project


@pytest.fixture
def mock_forge(mocker, tmp_path):
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.is_safe_path", return_value=True)
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.wrap_with_apoptosis",
        return_value="engine.py",
    )
    return tmp_path


def test_operate_forge_success(mocker, mock_forge):
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "1"})
    studio = mock_forge / "Studio" / "app"
    studio.mkdir(parents=True)
    (studio / "orchestrator.py").touch()

    mock_run = mocker.patch("System.tools.forge.subprocess.run")
    mock_run.return_value.returncode = 0

    res = operate_forge("app", "build it")
    assert res.success is True
    assert "FORGE EXECUTION COMPLETE" in res.output


def test_operate_forge_no_engine(mocker, mock_forge):
    res = operate_forge("ghost", "build it")
    assert res.success is False
    assert "Forge engine not found" in res.output


def test_operate_forge_user_denies(mocker, mock_forge):
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "0"})
    mocker.patch("builtins.input", return_value="n")
    studio = mock_forge / "Studio" / "app"
    studio.mkdir(parents=True)
    (studio / "orchestrator.py").touch()

    res = operate_forge("app", "build it")
    assert res.success is False
    assert "User explicitly denied" in res.output


def test_bootstrap_project(mocker, mock_forge):
    mock_run = mocker.patch("System.tools.forge.subprocess.run")
    mock_run.return_value.returncode = 0
    mocker.patch("System.tools.forge.shutil.which", return_value=None)

    res = bootstrap_project("new_app")
    assert res.success is True
    assert "Bootstrapped and hydrated" in res.output


def test_bootstrap_project_exists(mock_forge):
    app = mock_forge / "Studio" / "existing"
    app.mkdir(parents=True)

    res = bootstrap_project("existing")
    assert res.success is False
    assert "Directory exists" in res.output
