from __future__ import annotations

import logging
import operator
from typing import TYPE_CHECKING

from deptry.violations import (
    DEP001MissingDependenciesFinder,
    DEP002UnusedDependenciesFinder,
    DEP003TransitiveDependenciesFinder,
    DEP004MisplacedDevDependenciesFinder,
    DEP005StandardLibraryDependenciesFinder,
    DEP101MissingWorkspaceDependenciesFinder,
    DEP102WorkspaceTransitiveDependenciesFinder,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from deptry.dependency import Dependency
    from deptry.module import ModuleLocations
    from deptry.violations import Violation, ViolationsFinder


_VIOLATIONS_FINDERS: tuple[type[ViolationsFinder], ...] = (
    DEP001MissingDependenciesFinder,
    DEP002UnusedDependenciesFinder,
    DEP003TransitiveDependenciesFinder,
    DEP004MisplacedDevDependenciesFinder,
    DEP005StandardLibraryDependenciesFinder,
    DEP101MissingWorkspaceDependenciesFinder,
    DEP102WorkspaceTransitiveDependenciesFinder,
)


def find_violations(
    imported_modules_with_locations: list[ModuleLocations],
    dependencies: list[Dependency],
    ignore: tuple[str, ...],
    per_rule_ignores: Mapping[str, tuple[str, ...]],
    standard_library_modules: frozenset[str],
    workspace_sibling_module_names: frozenset[str] = frozenset(),
    workspace_sibling_dep_names: frozenset[str] = frozenset(),
) -> list[Violation]:
    violations = []

    for violation_finder in _VIOLATIONS_FINDERS:
        if violation_finder.violation.error_code not in ignore:
            violations.extend(
                violation_finder(
                    imported_modules_with_locations=imported_modules_with_locations,
                    dependencies=dependencies,
                    ignored_modules=per_rule_ignores.get(violation_finder.violation.error_code, ()),
                    standard_library_modules=standard_library_modules,
                    workspace_sibling_module_names=workspace_sibling_module_names,
                    workspace_sibling_dep_names=workspace_sibling_dep_names,
                ).find()
            )
    return _get_sorted_violations(_filter_inline_ignored_violations(violations))


def _filter_inline_ignored_violations(violations: Sequence[Violation]) -> list[Violation]:
    filtered = []
    for violation in violations:
        ignored_rule_codes = violation.location.ignored_rule_codes
        if not ignored_rule_codes:
            filtered.append(violation)
        elif "ALL" in ignored_rule_codes or violation.error_code in ignored_rule_codes:
            logging.debug(
                "Ignoring violation %s at %s:%s due to inline ignore comment.",
                violation.error_code,
                violation.location.file,
                violation.location.line,
            )
        else:
            filtered.append(violation)
    return filtered


def _get_sorted_violations(violations: list[Violation]) -> list[Violation]:
    return sorted(
        violations, key=operator.attrgetter("location.file", "location.line", "location.column", "error_code")
    )
