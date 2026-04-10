from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from deptry.imports.location import Location
from deptry.module import ModuleBuilder, ModuleLocations
from deptry.violations.dep101_missing_workspace.finder import DEP101MissingWorkspaceDependenciesFinder
from deptry.violations.dep101_missing_workspace.violation import DEP101MissingWorkspaceDependencyViolation


def test_simple() -> None:
    """A module provided by a workspace sibling that is not declared fires DEP101."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    issues = DEP101MissingWorkspaceDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_module_names=frozenset(["bar"]),
    ).find()

    assert issues == [
        DEP101MissingWorkspaceDependencyViolation(
            issue=module,
            location=Location(file=Path("foo.py"), line=1, column=2),
        ),
    ]


def test_not_a_workspace_sibling() -> None:
    """A module that is not a workspace sibling is not flagged by DEP101."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    issues = DEP101MissingWorkspaceDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_module_names=frozenset(),
    ).find()

    assert issues == []


def test_provided_by_dependency() -> None:
    """A workspace sibling that IS declared as a dependency does not fire DEP101."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    with patch.object(module, "is_provided_by_dependency", True):
        issues = DEP101MissingWorkspaceDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            workspace_sibling_module_names=frozenset(["bar"]),
        ).find()

    assert issues == []


def test_with_ignore() -> None:
    """A module in ignored_modules is not flagged even if it is an undeclared workspace sibling."""
    module = ModuleBuilder("bar", set(), frozenset()).build()

    issues = DEP101MissingWorkspaceDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        ignored_modules=("bar",),
        workspace_sibling_module_names=frozenset(["bar"]),
    ).find()

    assert issues == []


def test_standard_library_skipped() -> None:
    """Standard library modules are never flagged."""
    module = ModuleBuilder("os", set(), standard_library_modules=frozenset(["os"])).build()

    issues = DEP101MissingWorkspaceDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_module_names=frozenset(["os"]),
    ).find()

    assert issues == []
