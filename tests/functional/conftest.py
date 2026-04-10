from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import xdist

from tests.functional.utils import DEPTRY_WHEEL_DIRECTORY
from tests.utils import PDMVenvFactory, PipVenvFactory, PoetryVenvFactory, UvVenvFactory


def pytest_sessionstart(session: pytest.Session) -> None:
    # When running the tests on multiple workers with pytest-xdist, the hook will be run several times:
    # - once from "master" node, when test suite starts
    # - X times (where X is the number of workers), when tests start in each worker
    # We only want to run the hook once, so we explicitly skip the hook if running on a pytest-xdist worker.
    if xdist.is_xdist_worker(session):
        return None

    deptry_wheel_path = Path(DEPTRY_WHEEL_DIRECTORY)

    print(f"Building `deptry` wheel in {deptry_wheel_path} to use it on functional tests...")  # noqa: T201

    for stale_wheel in deptry_wheel_path.glob("*.whl"):
        stale_wheel.unlink()

    try:
        result = subprocess.run(
            shlex.split(f"uv build --verbose --wheel --out-dir {deptry_wheel_path}", posix=sys.platform != "win32"),
            capture_output=True,
            check=True,
            encoding="utf-8",
        )
        print(f"uv build output: {result.stdout}")  # noqa: T201
        print(f"uv build errors: {result.stderr}")  # noqa: T201
    except subprocess.CalledProcessError as e:
        print(f"Output: {e.output}")  # noqa: T201
        print(f"Errors: {e.stderr}")  # noqa: T201
        raise


@pytest.fixture(scope="session")
def pdm_venv_factory(tmp_path_factory: pytest.TempPathFactory) -> PDMVenvFactory:
    return PDMVenvFactory(tmp_path_factory.getbasetemp() / "venvs")


@pytest.fixture(scope="session")
def uv_venv_factory(tmp_path_factory: pytest.TempPathFactory) -> UvVenvFactory:
    return UvVenvFactory(tmp_path_factory.getbasetemp() / "venvs")


@pytest.fixture(scope="session")
def poetry_venv_factory(tmp_path_factory: pytest.TempPathFactory) -> PoetryVenvFactory:
    return PoetryVenvFactory(tmp_path_factory.getbasetemp() / "venvs")


@pytest.fixture(scope="session")
def pip_venv_factory(tmp_path_factory: pytest.TempPathFactory) -> PipVenvFactory:
    return PipVenvFactory(tmp_path_factory.getbasetemp() / "venvs")
