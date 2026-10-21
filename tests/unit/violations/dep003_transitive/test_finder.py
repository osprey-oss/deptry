from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from deptry.imports.location import Location
from deptry.module import Module, ModuleBuilder, ModuleLocations
from deptry.violations import DEP003TransitiveDependenciesFinder
from deptry.violations.dep003_transitive.violation import DEP003TransitiveDependencyViolation


def test_simple() -> None:
    module = ModuleBuilder("foo", set(), frozenset()).build()

    with patch.object(module, "package", return_value="foo"):
        issues = DEP003TransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
        ).find()

    assert issues == [
        DEP003TransitiveDependencyViolation(
            issue=module,
            location=Location(
                file=Path("foo.py"),
                line=1,
                column=2,
            ),
        ),
    ]


def test_simple_with_ignore() -> None:
    module = ModuleBuilder("foo", set(), frozenset()).build()

    with patch.object(module, "package", return_value="foo"):
        issues = DEP003TransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
            [],
            frozenset(),
            ignored_modules=("foo",),
        ).find()

    assert issues == []


def test_simple_with_standard_library() -> None:
    module = ModuleBuilder("foo", set(), standard_library_modules=frozenset(["foo"])).build()

    with patch.object(module, "package", return_value="foo"):
        issues = DEP003TransitiveDependenciesFinder(
            [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])], [], frozenset()
        ).find()

    assert issues == []


def test_workspace_sibling_module() -> None:
    """A module provided by a workspace sibling is reported by DEP101, not DEP003."""
    module = Module("bar", package="bar-pkg")

    issues = DEP003TransitiveDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_module_names=frozenset(["bar"]),
    ).find()

    assert issues == []


def test_workspace_sibling_dependency_top_level() -> None:
    """A module provided by a dependency of a workspace sibling is reported by DEP102, not DEP003, even if the name of
    its package does not match the name of the dependency."""
    module = Module("yaml", package="yaml")

    issues = DEP003TransitiveDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_dep_names=frozenset(["pyyaml"]),
        workspace_sibling_dep_top_levels=frozenset(["yaml"]),
    ).find()

    assert issues == []


def test_workspace_sibling_dependency() -> None:
    """A module whose package is declared by a workspace sibling is reported by DEP102, not DEP003."""
    module = Module("bar", package="bar-pkg")

    issues = DEP003TransitiveDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_dep_names=frozenset(["bar-pkg"]),
    ).find()

    assert issues == []


def test_not_declared_by_workspace_sibling() -> None:
    """A transitive dependency that no workspace sibling provides or declares is still reported by DEP003."""
    module = Module("foo", package="foo-pkg")

    issues = DEP003TransitiveDependenciesFinder(
        [ModuleLocations(module, [Location(Path("foo.py"), 1, 2)])],
        [],
        frozenset(),
        workspace_sibling_module_names=frozenset(["bar"]),
        workspace_sibling_dep_names=frozenset(["bar-pkg"]),
    ).find()

    assert issues == [
        DEP003TransitiveDependencyViolation(
            issue=module,
            location=Location(file=Path("foo.py"), line=1, column=2),
        ),
    ]
