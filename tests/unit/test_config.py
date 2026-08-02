from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import click
import pytest
from click import Argument

from deptry.config import read_configuration_from_pyproject_toml
from deptry.exceptions import InvalidPyprojectTOMLOptionsError
from tests.utils import run_within_dir

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


click_command = click.Command(
    "",
    params=[
        Argument(param_decls=["exclude"]),
        Argument(param_decls=["extend_exclude"]),
        Argument(param_decls=["per_rule_ignores"]),
        Argument(param_decls=["ignore"]),
        Argument(param_decls=["ignore_notebooks"]),
        Argument(param_decls=["requirements_files"]),
        Argument(param_decls=["requirements_files_dev"]),
    ],
)


def test_read_configuration_from_pyproject_toml_exists(tmp_path: Path) -> None:
    click_context = click.Context(
        click_command,
        default_map={
            "exclude": ["bar"],
            "extend_exclude": ["foo"],
            "per_rule_ignores": {
                "DEP002": ["baz", "bar"],
            },
            "ignore": [],
            "requirements_files": "requirements.txt",
            "requirements_files_dev": ["requirements-dev.txt"],
        },
    )

    pyproject_toml_content = """
        [tool.deptry]
        exclude = ["foo", "bar"]
        extend_exclude = ["bar", "foo"]
        ignore_notebooks = true
        ignore = ["DEP001", "DEP002", "DEP003", "DEP004"]
        requirements_files = "foo.txt"
        requirements_files_dev = ["dev.txt", "tests.txt"]

        [tool.deptry.per_rule_ignores]
        DEP001 = ["baz", "foobar"]
        DEP002 = ["foo"]
        DEP003 = ["foobaz"]
        DEP004 = ["barfoo"]
    """

    with run_within_dir(tmp_path):
        pyproject_toml_path = Path("pyproject.toml")

        with pyproject_toml_path.open("w") as f:
            f.write(pyproject_toml_content)

        assert (
            read_configuration_from_pyproject_toml(click_context, click.Argument(["foo"]), pyproject_toml_path)
            == pyproject_toml_path
        )

    assert click_context.default_map == {
        "exclude": ["foo", "bar"],
        "extend_exclude": ["bar", "foo"],
        "ignore_notebooks": True,
        "per_rule_ignores": {
            "DEP001": ["baz", "foobar"],
            "DEP002": ["foo"],
            "DEP003": ["foobaz"],
            "DEP004": ["barfoo"],
        },
        "ignore": ["DEP001", "DEP002", "DEP003", "DEP004"],
        "requirements_files": "foo.txt",
        "requirements_files_dev": ["dev.txt", "tests.txt"],
    }


def test_read_configuration_from_pyproject_toml_file_not_found(caplog: LogCaptureFixture) -> None:
    pyproject_toml_path = Path("a_non_existent_pyproject.toml")

    with caplog.at_level(logging.DEBUG):
        assert (
            read_configuration_from_pyproject_toml(
                click.Context(click_command), click.Argument(["foo"]), pyproject_toml_path
            )
            == pyproject_toml_path
        )

    assert "No pyproject.toml file to read configuration from." in caplog.text


def test_read_configuration_from_pyproject_toml_file_without_deptry_section(
    caplog: LogCaptureFixture, tmp_path: Path
) -> None:
    pyproject_toml_content = """
        [tool.something]
        exclude = ["foo", "bar"]
    """

    with run_within_dir(tmp_path):
        pyproject_toml_path = Path("pyproject.toml")

        with pyproject_toml_path.open("w") as f:
            f.write(pyproject_toml_content)

        with caplog.at_level(logging.DEBUG):
            assert read_configuration_from_pyproject_toml(
                click.Context(click_command), click.Argument(["foo"]), pyproject_toml_path
            ) == Path("pyproject.toml")

    assert "No configuration for deptry was found in pyproject.toml." in caplog.text


def test_read_configuration_from_pyproject_toml_file_with_invalid_options(
    caplog: LogCaptureFixture, tmp_path: Path
) -> None:
    pyproject_toml_content = """
        [tool.deptry]
        exclude = ["foo", "bar"]
        invalid_option = "nope"
        another_invalid_option = "still nope"
        extend_exclude = ["bar", "foo"]
    """

    with run_within_dir(tmp_path):
        pyproject_toml_path = Path("pyproject.toml")

        with pyproject_toml_path.open("w") as f:
            f.write(pyproject_toml_content)

        with pytest.raises(InvalidPyprojectTOMLOptionsError):
            assert read_configuration_from_pyproject_toml(
                click.Context(click_command), click.Argument(["foo"]), pyproject_toml_path
            ) == Path("pyproject.toml")
