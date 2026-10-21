from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from deptry.config import Config
from deptry.dependency import Dependency
from deptry.dependency_getter.base import DependenciesExtract
from deptry.scanners import ProjectScanner
from tests.utils import create_files, run_within_dir


def _make_config(**overrides: Any) -> Config:
    defaults: dict[str, Any] = {
        "root": (Path(),),
        "config": Path("pyproject.toml"),
        "no_ansi": False,
        "per_rule_ignores": {},
        "ignore": (),
        "exclude": (),
        "extend_exclude": (),
        "using_default_exclude": True,
        "ignore_notebooks": False,
        "requirements_files": (),
        "requirements_files_dev": (),
        "known_first_party": (),
        "json_output": "",
        "package_module_name_map": {},
        "optional_dependencies_dev_groups": (),
        "non_dev_dependency_groups": (),
        "using_default_requirements_files": True,
        "experimental_namespace_package": False,
        "github_output": False,
        "github_warning_errors": (),
        "enforce_posix_paths": False,
    }
    defaults.update(overrides)
    return Config(**defaults)


def _make_scanner(**config_overrides: Any) -> ProjectScanner:
    return ProjectScanner(_make_config(**config_overrides), DependenciesExtract([], []))


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
def test__get_local_modules(
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
            _make_scanner(
                root=(tmp_path / root_suffix,),
                known_first_party=known_first_party,
                experimental_namespace_package=experimental_namespace_package,
            )._get_local_modules()
            == expected
        )


def test__get_stdlib_packages_with_stdlib_module_names() -> None:
    assert ProjectScanner._get_standard_library_modules() == sys.stdlib_module_names


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
        assert ProjectScanner._get_standard_library_modules() == sys.stdlib_module_names


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
        ProjectScanner._log_dependencies(DependenciesExtract(dependencies, dev_dependencies))

    assert caplog.messages == expected_logs
