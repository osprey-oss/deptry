from __future__ import annotations

import logging
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from deptry.dependency_getter.pep621.base import PEP621DependencyGetter

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("selection", "expected_dev"),
    [(None, {"dev-tool"}), ((), set()), (("docs",), {"docs-tool"})],
)
def test_dev_extra_default_and_explicit_selection(
    tmp_path: Path, selection: tuple[str, ...] | None, expected_dev: set[str]
) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text(
        '[project]\nname = "example"\ndependencies = ["runtime-library"]\n'
        '[project.optional-dependencies]\ndev = ["dev-tool"]\ndocs = ["docs-tool"]\n'
    )

    getter = PEP621DependencyGetter(config=config)
    if selection is not None:
        getter.optional_dependencies_dev_groups = selection
    result = getter.get()

    assert {dependency.name for dependency in result.dev_dependencies} == expected_dev
    assert {dependency.name for dependency in result.dependencies} == {
        "runtime-library",
        "dev-tool",
        "docs-tool",
    } - expected_dev


def test_missing_default_group_does_not_warn(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text('[project]\nname = "example"\n[project.optional-dependencies]\ntest = ["dev-tool"]\n')

    with caplog.at_level(logging.WARNING):
        result = PEP621DependencyGetter(config=config).get()

    assert [dependency.name for dependency in result.dependencies] == ["dev-tool"]
    assert not result.dev_dependencies
    assert "groups were not found" not in caplog.text


@pytest.mark.parametrize("disable_default", [False, True])
def test_cli_default_and_empty_configuration(tmp_path: Path, disable_default: bool) -> None:
    config = (
        '[project]\nname = "example"\nversion = "0.0.1"\ndependencies = []\n'
        '[project.optional-dependencies]\ndev = ["dev-tool"]\n'
    )
    if disable_default:
        config += "[tool.deptry]\noptional_dependencies_dev_groups = []\n"
    (tmp_path / "pyproject.toml").write_text(config)
    (tmp_path / "main.py").write_text("import os\n")

    result = subprocess.run(
        [sys.executable, "-m", "deptry", "."], cwd=tmp_path, capture_output=True, text=True, check=False
    )

    assert result.returncode == int(disable_default), result.stderr
    assert ("DEP002" in result.stderr) is disable_default
