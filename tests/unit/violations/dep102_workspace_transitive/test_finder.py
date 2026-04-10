from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from deptry.imports.location import Location
from deptry.module import ModuleBuilder, ModuleLocations
from deptry.violations.dep102_workspace_transitive.finder import DEP102WorkspaceTransitiveDependenciesFinder
from deptry.violations.dep102_workspace_transitive.violation import DEP102WorkspaceTransitiveDependencyViolation


def test_simple() -> None:
    """A module whose package is only declared by a workspace sibling fires DEP102."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "package", "bar-pkg"):
        issues = DEP102WorkspaceTransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            workspace_sibling_dep_names=frozenset(["bar-pkg"]),
        ).find()

    assert issues == [
        DEP102WorkspaceTransitiveDependencyViolation(
            issue=module,
            location=Location(file=Path("foo.py"), line=1, column=2),
        ),
    ]


def test_package_not_declared_by_sibling() -> None:
    """A module whose package is not declared by any workspace sibling is not flagged by DEP102."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "package", "bar-pkg"):
        issues = DEP102WorkspaceTransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            workspace_sibling_dep_names=frozenset(),
        ).find()

    assert issues == []


def test_provided_by_dependency() -> None:
    """A module that is also provided by a direct dependency does not fire DEP102."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "package", "bar-pkg"), patch.object(module, "is_provided_by_dependency", True):
        issues = DEP102WorkspaceTransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            workspace_sibling_dep_names=frozenset(["bar-pkg"]),
        ).find()

    assert issues == []


def test_provided_by_dev_dependency() -> None:
    """A module that is also provided by a dev dependency does not fire DEP102."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "package", "bar-pkg"), patch.object(module, "is_provided_by_dev_dependency", True):
        issues = DEP102WorkspaceTransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            workspace_sibling_dep_names=frozenset(["bar-pkg"]),
        ).find()

    assert issues == []


def test_is_workspace_sibling_module() -> None:
    """A module that is itself a workspace sibling is reported by DEP101, not DEP102."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "package", "bar-pkg"):
        issues = DEP102WorkspaceTransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            workspace_sibling_module_names=frozenset(["bar"]),
            workspace_sibling_dep_names=frozenset(["bar-pkg"]),
        ).find()

    assert issues == []


def test_local_module() -> None:
    """A local module is never flagged by DEP102."""
    module = ModuleBuilder("bar", {"bar"}, frozenset()).build()

    issues = DEP102WorkspaceTransitiveDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_dep_names=frozenset(["bar-pkg"]),
    ).find()

    assert issues == []


def test_with_ignore() -> None:
    """A module in ignored_modules is not flagged even if only a workspace sibling declares its package."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "package", "bar-pkg"):
        issues = DEP102WorkspaceTransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            ignored_modules=("bar",),
            workspace_sibling_dep_names=frozenset(["bar-pkg"]),
        ).find()

    assert issues == []


def test_standard_library_skipped() -> None:
    """Standard library modules are never flagged."""
    module = ModuleBuilder("os", set(), standard_library_modules=frozenset(["os"])).build()

    issues = DEP102WorkspaceTransitiveDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_dep_names=frozenset(["os"]),
    ).find()

    assert issues == []
