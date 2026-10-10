from __future__ import annotations

from pathlib import Path

from deptry.dependency import Dependency
from deptry.imports.location import Location
from deptry.module import ModuleBuilder, ModuleLocations
from deptry.violations import DEP001MissingDependenciesFinder, DEP001MissingDependencyViolation


def test_simple() -> None:
    dependencies: list[Dependency] = []

    module_foobar_locations = [Location(Path("foo.py"), 1, 2), Location(Path("bar.py"), 3, 4)]
    module_foobar = ModuleBuilder("foobar", {"foo"}, frozenset(), dependencies).build()

    modules_locations = [ModuleLocations(module_foobar, module_foobar_locations)]

    assert DEP001MissingDependenciesFinder(modules_locations, dependencies, frozenset()).find() == [
        DEP001MissingDependencyViolation(module_foobar, location) for location in module_foobar_locations
    ]


def test_local_module() -> None:
    dependencies: list[Dependency] = []
    modules_locations = [
        ModuleLocations(
            ModuleBuilder("foobar", {"foo", "foobar"}, frozenset(), dependencies).build(),
            [Location(Path("foo.py"), 1, 2)],
        )
    ]

    assert DEP001MissingDependenciesFinder(modules_locations, dependencies, frozenset()).find() == []


def test_simple_with_ignore() -> None:
    dependencies: list[Dependency] = []
    modules_locations = [
        ModuleLocations(
            ModuleBuilder("foobar", {"foo", "bar"}, frozenset(), dependencies).build(), [Location(Path("foo.py"), 1, 2)]
        )
    ]

    assert (
        DEP001MissingDependenciesFinder(
            modules_locations, dependencies, frozenset(), ignored_modules=("foobar",)
        ).find()
        == []
    )


def test_simple_with_standard_library() -> None:
    dependencies: list[Dependency] = []
    standard_library_modules = frozenset(["foobar"])
    modules_locations = [
        ModuleLocations(
            ModuleBuilder("foobar", set(), standard_library_modules, dependencies).build(),
            [Location(Path("foo.py"), 1, 2)],
        )
    ]

    assert DEP001MissingDependenciesFinder(modules_locations, dependencies, frozenset()).find() == []


def test_no_error() -> None:
    """
    This should run without an error, even though `foo` is not installed.
    """

    dependencies = [Dependency("foo", Path("pyproject.toml"))]
    modules_locations = [
        ModuleLocations(
            ModuleBuilder("foo", {"bar"}, frozenset(), dependencies).build(),
            [Location(Path("foo.py"), 1, 2)],
        )
    ]

    assert DEP001MissingDependenciesFinder(modules_locations, dependencies, frozenset()).find() == []


def test_workspace_sibling_module() -> None:
    """A module provided by a workspace sibling is reported by DEP101, not DEP001."""
    dependencies: list[Dependency] = []
    module_foobar = ModuleBuilder("foobar", {"foo"}, frozenset(), dependencies).build()

    assert (
        DEP001MissingDependenciesFinder(
            [ModuleLocations(module_foobar, [Location(Path("foo.py"), 1, 2)])],
            dependencies,
            frozenset(),
            workspace_sibling_module_names=frozenset(["foobar"]),
        ).find()
        == []
    )
