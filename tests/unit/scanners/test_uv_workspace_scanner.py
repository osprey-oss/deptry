from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from deptry.config import Config
from deptry.core import UvWorkspaceConfig
from deptry.dependency import Dependency
from deptry.dependency_getter.base import DependenciesExtract
from deptry.scanners.uv_workspace import UvWorkspaceScanner
from tests.utils import create_files


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


# ---------------------------------------------------------------------------
# _collect_top_level_modules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        # Package with __init__.py
        (
            [Path("mypkg/__init__.py"), Path("mypkg/module.py")],
            ("mypkg",),
        ),
        # Single-file module
        (
            [Path("script.py")],
            ("script",),
        ),
        # Directory without __init__.py is excluded
        (
            [Path("no_init/module.py"), Path("real/__init__.py")],
            ("real",),
        ),
        # __init__.py at root level is excluded
        (
            [Path("__init__.py"), Path("mypkg/__init__.py")],
            ("mypkg",),
        ),
        # Hidden directories are excluded
        (
            [Path(".hidden/__init__.py"), Path("visible/__init__.py")],
            ("visible",),
        ),
        # Empty source root
        (
            [],
            (),
        ),
    ],
)
def test__collect_top_level_modules(
    tmp_path: Path,
    files: list[Path],
    expected: tuple[str, ...],
) -> None:
    create_files([tmp_path / f for f in files])
    assert UvWorkspaceScanner._collect_top_level_modules(tmp_path) == expected


# ---------------------------------------------------------------------------
# _get_sibling_context
# ---------------------------------------------------------------------------


def test__get_sibling_context_excludes_own_modules() -> None:
    members = {
        Path("packages/foo"): DependenciesExtract([Dependency("numpy", Path("packages/foo/pyproject.toml"))], []),
        Path("packages/bar"): DependenciesExtract([Dependency("pandas", Path("packages/bar/pyproject.toml"))], []),
    }
    package_module_name_map: dict[str, tuple[str, ...]] = {
        "foo": ("foo",),
        "bar": ("bar2",),
    }
    # Scanning "foo": own modules are {"foo"}
    member_module_names = frozenset({"foo"})

    sibling_modules, sibling_deps = UvWorkspaceScanner._get_sibling_context(
        Path("packages/foo"),
        package_module_name_map,
        member_module_names,
        members,
    )

    assert sibling_modules == frozenset({"bar2"})
    assert sibling_deps == frozenset({"pandas"})


def test__get_sibling_context_includes_sibling_dev_dependencies() -> None:
    members = {
        Path("packages/foo"): DependenciesExtract([], [Dependency("pytest", Path("packages/foo/pyproject.toml"))]),
        Path("packages/bar"): DependenciesExtract([Dependency("requests", Path("packages/bar/pyproject.toml"))], []),
    }
    package_module_name_map: dict[str, tuple[str, ...]] = {}
    member_module_names: frozenset[str] = frozenset()

    _sibling_modules, sibling_deps = UvWorkspaceScanner._get_sibling_context(
        Path("packages/bar"),
        package_module_name_map,
        member_module_names,
        members,
    )

    # "requests" belongs to bar itself, "pytest" belongs to foo — only foo's deps are siblings
    assert sibling_deps == frozenset({"pytest"})


def test__get_sibling_context_no_siblings() -> None:
    members = {
        Path("packages/only"): DependenciesExtract([Dependency("requests", Path("packages/only/pyproject.toml"))], []),
    }
    package_module_name_map: dict[str, tuple[str, ...]] = {"only": ("only",)}
    member_module_names = frozenset({"only"})

    sibling_modules, sibling_deps = UvWorkspaceScanner._get_sibling_context(
        Path("packages/only"),
        package_module_name_map,
        member_module_names,
        members,
    )

    assert sibling_modules == frozenset()
    assert sibling_deps == frozenset()


# ---------------------------------------------------------------------------
# _build_member_base_config
# ---------------------------------------------------------------------------


def test__build_member_base_config_applies_member_deptry_overrides(tmp_path: Path) -> None:
    member = tmp_path / "packages" / "foo"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text('[tool.deptry]\nignore = ["DEP001"]\n', encoding="utf-8")

    base_config = _make_config(root=(tmp_path,), config=tmp_path / "pyproject.toml")
    scanner = UvWorkspaceScanner(
        config=base_config,
        uv_workspace_config=UvWorkspaceConfig(members=(member,)),
    )

    result = scanner._build_member_base_config(member)

    assert result.root == (member,)
    assert result.config == member / "pyproject.toml"
    assert list(result.ignore) == ["DEP001"]


def test__build_member_base_config_no_deptry_section(tmp_path: Path) -> None:
    member = tmp_path / "packages" / "bar"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text('[project]\nname = "bar"\n', encoding="utf-8")

    base_config = _make_config(ignore=("DEP002",), root=(tmp_path,), config=tmp_path / "pyproject.toml")
    scanner = UvWorkspaceScanner(
        config=base_config,
        uv_workspace_config=UvWorkspaceConfig(members=(member,)),
    )

    result = scanner._build_member_base_config(member)

    # No [tool.deptry] in member, so base config values are preserved
    assert result.ignore == ("DEP002",)
    assert result.root == (member,)


def test__build_member_base_config_missing_pyproject(tmp_path: Path) -> None:
    member = tmp_path / "packages" / "ghost"
    member.mkdir(parents=True)
    # No pyproject.toml written

    base_config = _make_config(root=(tmp_path,), config=tmp_path / "pyproject.toml")
    scanner = UvWorkspaceScanner(
        config=base_config,
        uv_workspace_config=UvWorkspaceConfig(members=(member,)),
    )

    # Should not raise; falls back gracefully
    result = scanner._build_member_base_config(member)

    assert result.root == (member,)
