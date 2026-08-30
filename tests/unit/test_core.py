from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from deptry.core import Core
from deptry.dependency import Dependency
from deptry.dependency_getter.base import DependenciesExtract
from deptry.imports.location import Location
from deptry.module import Module
from deptry.violations import (
    DEP001MissingDependencyViolation,
    DEP002UnusedDependencyViolation,
    DEP003TransitiveDependencyViolation,
    DEP004MisplacedDevDependencyViolation,
)
from tests.utils import create_files, run_within_dir


@pytest.mark.parametrize(
    ("known_first_party", "root_suffix", "experimental_namespace_package", "expected"),
    [
        (
            (),
            "",
            False,
            {
                "local_file",
                "module_with_init",
                "module_without_init",
            },
        ),
        (
            ("module_with_init", "module_without_init"),
            "",
            False,
            {
                "local_file",
                "module_with_init",
                "module_without_init",
            },
        ),
        (
            ("module_without_init",),
            "module_with_init",
            False,
            {
                "foo",
                "module_without_init",
                "subdirectory",
            },
        ),
        (
            (),
            "",
            True,
            {
                "local_file",
                "module_using_namespace",
                "module_with_init",
                "module_without_init",
            },
        ),
        (
            ("module_with_init", "module_without_init"),
            "",
            True,
            {
                "local_file",
                "module_using_namespace",
                "module_with_init",
                "module_without_init",
            },
        ),
        (
            ("module_without_init",),
            "module_with_init",
            True,
            {
                "foo",
                "module_without_init",
                "subdirectory",
            },
        ),
    ],
)
def test__get_local_modules_with_directories(
    tmp_path: Path,
    known_first_party: tuple[str, ...],
    root_suffix: str,
    experimental_namespace_package: bool,
    expected: set[str],
) -> None:
    with run_within_dir(tmp_path):
        create_files([
            Path("directory_without_python_files/foo.txt"),
            Path("module_using_namespace/subdirectory_namespace/foo.py"),
            Path("module_with_init/__init__.py"),
            Path("module_with_init/foo.py"),
            Path("module_with_init/subdirectory/__init__.py"),
            Path("module_with_init/subdirectory/foo.py"),
            Path("module_without_init/bar.py"),
            Path("local_file.py"),
        ])

        assert (
            Core(
                root=(tmp_path / root_suffix,),
                config=Path("pyproject.toml"),
                no_ansi=False,
                per_rule_ignores={},
                ignore=(),
                exclude=(),
                extend_exclude=(),
                using_default_exclude=True,
                ignore_notebooks=False,
                requirements_files=(),
                requirements_files_dev=(),
                known_first_party=known_first_party,
                json_output="",
                package_module_name_map={},
                optional_dependencies_dev_groups=(),
                non_dev_dependency_groups=(),
                using_default_requirements_files=True,
                experimental_namespace_package=experimental_namespace_package,
                github_output=False,
                github_warning_errors=(),
                enforce_posix_paths=False,
            )._get_local_modules()
            == expected
        )


def test__get_local_modules_with_single_file(tmp_path: Path) -> None:
    """Test that _get_local_modules works with a single Python file."""
    with run_within_dir(tmp_path):
        create_files([
            Path("app.py"),
            Path("other.py"),
        ])

        result = Core(
            root=(tmp_path / "app.py",),
            config=Path("pyproject.toml"),
            no_ansi=False,
            per_rule_ignores={},
            ignore=(),
            exclude=(),
            extend_exclude=(),
            using_default_exclude=True,
            ignore_notebooks=False,
            requirements_files=(),
            requirements_files_dev=(),
            known_first_party=(),
            json_output="",
            package_module_name_map={},
            optional_dependencies_dev_groups=(),
            using_default_requirements_files=True,
            experimental_namespace_package=False,
            github_output=False,
            github_warning_errors=(),
        )._get_local_modules()

        assert result == {"app"}


def test__get_local_modules_ignores_init_file(tmp_path: Path) -> None:
    """Test that __init__.py files are not treated as modules."""
    with run_within_dir(tmp_path):
        create_files([Path("__init__.py")])

        result = Core(
            root=(tmp_path / "__init__.py",),
            config=Path("pyproject.toml"),
            no_ansi=False,
            per_rule_ignores={},
            ignore=(),
            exclude=(),
            extend_exclude=(),
            using_default_exclude=True,
            ignore_notebooks=False,
            requirements_files=(),
            requirements_files_dev=(),
            known_first_party=(),
            json_output="",
            package_module_name_map={},
            optional_dependencies_dev_groups=(),
            using_default_requirements_files=True,
            experimental_namespace_package=False,
            github_output=False,
            github_warning_errors=(),
        )._get_local_modules()

        assert result == set()


def test__get_stdlib_packages_with_stdlib_module_names() -> None:
    assert Core._get_standard_library_modules() == sys.stdlib_module_names


@pytest.mark.parametrize(
    "version_info",
    [
        (sys.version_info[0], sys.version_info[1] + 1, 0),
        (sys.version_info[0], sys.version_info[1] + 1, 13),
        (sys.version_info[0] + 1, sys.version_info[1], 0),
        (sys.version_info[0], sys.version_info[1] + 1, 0, "beta", 1),
        (sys.version_info[0], sys.version_info[1] + 1, 0, "candidate", 1),
    ],
)
def test__get_stdlib_packages_with_stdlib_module_names_future_version(version_info: tuple[int | str, ...]) -> None:
    """Test that future versions of Python not yet tested on the CI will also work."""
    with mock.patch("sys.version_info", (sys.version_info[0], sys.version_info[1] + 1, 0)):
        assert Core._get_standard_library_modules() == sys.stdlib_module_names


@mock.patch("deptry.reporters.TextReporter.report")
@mock.patch("deptry.reporters.JSONReporter.report")
@mock.patch("deptry.reporters.GithubReporter.report")
def test_text_reporter_only(
    mock_github_reporter_report: Any, mock_json_reporter_report: Any, mock_text_reporter_report: Any
) -> None:
    with pytest.raises(SystemExit):
        Core(
            root=(Path(),),
            config=Path("pyproject.toml"),
            no_ansi=False,
            per_rule_ignores={},
            ignore=(),
            exclude=(),
            extend_exclude=(),
            using_default_exclude=True,
            ignore_notebooks=False,
            requirements_files=(),
            requirements_files_dev=(),
            known_first_party=(),
            json_output="",
            package_module_name_map={},
            optional_dependencies_dev_groups=(),
            non_dev_dependency_groups=(),
            using_default_requirements_files=True,
            experimental_namespace_package=False,
            github_output=False,
            github_warning_errors=(),
            enforce_posix_paths=False,
        ).run()

    mock_text_reporter_report.assert_called()
    mock_json_reporter_report.assert_not_called()
    mock_github_reporter_report.assert_not_called()


@mock.patch("deptry.reporters.TextReporter.report")
@mock.patch("deptry.reporters.JSONReporter.report")
@mock.patch("deptry.reporters.GithubReporter.report")
def test_all_reporters(
    mock_github_reporter_report: Any, mock_json_reporter_report: Any, mock_text_reporter_report: Any
) -> None:
    with pytest.raises(SystemExit):
        Core(
            root=(Path(),),
            config=Path("pyproject.toml"),
            no_ansi=False,
            per_rule_ignores={},
            ignore=(),
            exclude=(),
            extend_exclude=(),
            using_default_exclude=True,
            ignore_notebooks=False,
            requirements_files=(),
            requirements_files_dev=(),
            known_first_party=(),
            json_output="foo.json",
            package_module_name_map={},
            optional_dependencies_dev_groups=(),
            non_dev_dependency_groups=(),
            using_default_requirements_files=True,
            experimental_namespace_package=False,
            github_output=True,
            github_warning_errors=(),
            enforce_posix_paths=False,
        ).run()

    mock_text_reporter_report.assert_called()
    mock_json_reporter_report.assert_called()
    mock_github_reporter_report.assert_called()


def test__exit_with_violations() -> None:
    violations = [
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 2)),
        DEP002UnusedDependencyViolation(Dependency("foo", Path("pyproject.toml")), Location(Path("pyproject.toml"))),
        DEP003TransitiveDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 2)),
        DEP004MisplacedDevDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 2)),
    ]

    with pytest.raises(SystemExit) as e:
        Core._exit(violations)

    assert e.type is SystemExit
    assert e.value.code == 1


def test__exit_without_violations() -> None:
    with pytest.raises(SystemExit) as e:
        Core._exit([])

    assert e.type is SystemExit
    assert e.value.code == 0


@pytest.mark.parametrize(
    ("dependencies", "dev_dependencies", "expected_logs"),
    [
        (
            [],
            [],
            [],
        ),
        (
            [
                Dependency("foo", Path("pyproject.toml")),
                Dependency("bar", Path("pyproject.toml")),
            ],
            [
                Dependency("dev", Path("pyproject.toml")),
                Dependency("another-dev", Path("pyproject.toml")),
            ],
            [
                "The project contains the following dependencies:",
                "Dependency 'foo' with top-levels: {'foo'}.",
                "Dependency 'bar' with top-levels: {'bar'}.",
                "",
                "The project contains the following dev dependencies:",
                "Dependency 'dev' with top-levels: {'dev'}.",
                "Dependency 'another-dev' with top-levels: {'another_dev'}.",
                "",
            ],
        ),
    ],
)
def test__log_dependencies(
    dependencies: list[Dependency],
    dev_dependencies: list[Dependency],
    expected_logs: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        Core._log_dependencies(DependenciesExtract(dependencies, dev_dependencies))

    assert caplog.messages == expected_logs
