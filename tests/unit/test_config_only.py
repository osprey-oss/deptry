from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def shared_configuration(tmp_path: Path) -> tuple[Path, Path]:
    shared = tmp_path / "pyproject.toml"
    shared.write_text(
        '[project]\nname = "shared"\nversion = "0.0.1"\n'
        'dependencies = ["shared-unused-dependency"]\n'
        '[tool.deptry]\nignore = ["DEP001"]\n'
    )
    project = tmp_path / "package"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "example"\nversion = "0.0.1"\n'
        'dependencies = ["local-declared-dependency"]\n'
        '[tool.deptry]\nignore = ["DEP002"]\n'
    )
    (project / "main.py").write_text("import local_declared_dependency\nimport missing_dependency\n")
    return project, shared


def run_deptry(project: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "deptry", *arguments],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("absolute", [False, True])
def test_shared_settings_with_local_dependencies(shared_configuration: tuple[Path, Path], absolute: bool) -> None:
    project, shared = shared_configuration
    result = run_deptry(project, [".", "--config-only", str(shared) if absolute else "../pyproject.toml"])

    assert result.returncode == 0, result.stderr
    assert "Success!" in result.stderr


def test_command_line_overrides_shared_settings(shared_configuration: tuple[Path, Path]) -> None:
    project, shared = shared_configuration
    result = run_deptry(project, ["--config-only", str(shared), ".", "--ignore", "DEP002"])

    assert result.returncode == 1
    assert "DEP001" in result.stderr
    assert "missing_dependency" in result.stderr
    assert "local_declared_dependency' imported but missing" not in result.stderr


def test_shared_settings_without_project_metadata(shared_configuration: tuple[Path, Path]) -> None:
    project, shared = shared_configuration
    shared.write_text('[tool.deptry]\nignore = ["DEP001"]\n')

    result = run_deptry(project, [".", "--config-only", str(shared)])

    assert result.returncode == 0, result.stderr


def test_shared_settings_with_requirements_file(shared_configuration: tuple[Path, Path]) -> None:
    project, shared = shared_configuration
    (project / "pyproject.toml").unlink()
    (project / "requirements.txt").write_text("local-declared-dependency\n")

    result = run_deptry(project, [".", "--config-only", str(shared)])

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("config_first", [False, True])
def test_config_options_are_mutually_exclusive(shared_configuration: tuple[Path, Path], config_first: bool) -> None:
    project, shared = shared_configuration
    options = [["--config", str(shared)], ["--config-only", str(shared)]]
    if not config_first:
        options.reverse()

    result = run_deptry(project, [".", *options[0], *options[1]])

    assert result.returncode == 2
    assert "Cannot use both --config and --config-only" in result.stderr


def test_config_still_reads_settings_and_dependencies(shared_configuration: tuple[Path, Path]) -> None:
    project, shared = shared_configuration
    result = run_deptry(project, [".", "--config", str(shared)])

    assert result.returncode == 1
    assert "DEP002" in result.stderr
    assert "shared-unused-dependency" in result.stderr


def test_missing_shared_config_reports_usage_error(shared_configuration: tuple[Path, Path]) -> None:
    project, shared = shared_configuration
    result = run_deptry(project, [".", "--config-only", str(shared.with_name("missing.toml"))])

    assert result.returncode == 2
    assert "does not exist" in result.stderr
    assert "Traceback" not in result.stderr
