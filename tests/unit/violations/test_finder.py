from __future__ import annotations

from pathlib import Path

from deptry.imports.location import Location
from deptry.module import Module, ModuleLocations
from deptry.violations import (
    DEP001MissingDependencyViolation,
    DEP003TransitiveDependencyViolation,
    DEP004MisplacedDevDependencyViolation,
    DEP101MissingWorkspaceDependencyViolation,
    DEP102WorkspaceLeakedDependencyViolation,
)
from deptry.violations.finder import _filter_inline_ignored_violations, _get_sorted_violations, find_violations


def test__get_sorted_violations() -> None:
    violations = [
        DEP004MisplacedDevDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 2, 0)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("bar.py"), 3, 1)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("bar.py"), 2, 1)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("bar.py"), 3, 0)),
    ]

    assert _get_sorted_violations(violations) == [
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("bar.py"), 2, 1)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("bar.py"), 3, 0)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("bar.py"), 3, 1)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0)),
        DEP004MisplacedDevDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0)),
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 2, 0)),
    ]


def test__filter_inline_ignored_violations_no_ignored_codes() -> None:
    violations = [
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0)),
        DEP001MissingDependencyViolation(Module("bar"), Location(Path("bar.py"), 2, 0)),
    ]

    assert _filter_inline_ignored_violations(violations) == violations


def test__filter_inline_ignored_violations_with_matching_code() -> None:
    violations = [
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0, ignored_rule_codes=("DEP001",))),
        DEP001MissingDependencyViolation(Module("bar"), Location(Path("bar.py"), 2, 0)),
    ]

    assert _filter_inline_ignored_violations(violations) == [
        DEP001MissingDependencyViolation(Module("bar"), Location(Path("bar.py"), 2, 0)),
    ]


def test__filter_inline_ignored_violations_with_non_matching_code() -> None:
    violations = [
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0, ignored_rule_codes=("DEP004",))),
    ]

    assert _filter_inline_ignored_violations(violations) == violations


def test__filter_inline_ignored_violations_with_bare_ignore() -> None:
    violations = [
        DEP001MissingDependencyViolation(Module("foo"), Location(Path("foo.py"), 1, 0, ignored_rule_codes=("ALL",))),
        DEP004MisplacedDevDependencyViolation(
            Module("bar"), Location(Path("bar.py"), 2, 0, ignored_rule_codes=("ALL",))
        ),
    ]

    assert _filter_inline_ignored_violations(violations) == []


def test__filter_inline_ignored_violations_with_multiple_codes() -> None:
    violations = [
        DEP001MissingDependencyViolation(
            Module("foo"), Location(Path("foo.py"), 1, 0, ignored_rule_codes=("DEP001", "DEP004"))
        ),
        DEP004MisplacedDevDependencyViolation(
            Module("bar"), Location(Path("bar.py"), 2, 0, ignored_rule_codes=("DEP001", "DEP004"))
        ),
    ]

    assert _filter_inline_ignored_violations(violations) == []


def test_find_violations_workspace_sibling_module_only_reports_dep101() -> None:
    """An undeclared import of a workspace sibling is reported once, as DEP101, and not also as DEP003 or DEP102."""
    module = Module("bar", package="bar")
    location = Location(Path("foo.py"), 1, 0)

    violations = find_violations(
        [ModuleLocations(module, [location])],
        [],
        (),
        {},
        frozenset(),
        workspace_sibling_module_names=frozenset(["bar"]),
        # A sibling may itself be declared as a dependency by a third workspace member.
        workspace_sibling_dep_names=frozenset(["bar"]),
    )

    assert violations == [DEP101MissingWorkspaceDependencyViolation(module, location)]


def test_find_violations_workspace_sibling_dependency_only_reports_dep102() -> None:
    """An undeclared import of a package declared by a workspace sibling is reported once, as DEP102, and not also as
    DEP003."""
    module = Module("pandas", package="pandas")
    location = Location(Path("foo.py"), 1, 0)

    violations = find_violations(
        [ModuleLocations(module, [location])],
        [],
        (),
        {},
        frozenset(),
        workspace_sibling_module_names=frozenset(["bar"]),
        workspace_sibling_dep_names=frozenset(["pandas"]),
    )

    assert violations == [DEP102WorkspaceLeakedDependencyViolation(module, location)]


def test_find_violations_known_limitation_transitive_dependency_of_workspace_sibling_reports_dep003() -> None:
    """Known limitation, not desired behaviour.

    A workspace member without any declared dependency imports `numpy`. `numpy` is only installed because a sibling
    declares `pandas`, which depends on it. `numpy` is therefore neither a sibling module nor a dependency declared by
    a sibling, and deptry does not walk the dependency trees of the siblings. As a result, DEP102 does not fire and the
    import is reported as DEP003, even though the importing member has no dependency path to `numpy`.

    If this test fails because the import is now reported as DEP102, the limitation has been lifted: update this test
    and the documentation.
    """
    module = Module("numpy", package="numpy")
    location = Location(Path("foo.py"), 1, 0)

    violations = find_violations(
        [ModuleLocations(module, [location])],
        [],
        (),
        {},
        frozenset(),
        workspace_sibling_module_names=frozenset(["bar"]),
        workspace_sibling_dep_names=frozenset(["pandas"]),
    )

    assert violations == [DEP003TransitiveDependencyViolation(module, location)]
