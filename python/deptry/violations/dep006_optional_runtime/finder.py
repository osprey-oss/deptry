from __future__ import annotations

import logging
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep006_optional_runtime.violation import DEP006OptionalDependencyPlacementViolation

if TYPE_CHECKING:
    from collections.abc import Sequence

    from deptry.dependency import Dependency
    from deptry.imports.location import Location
    from deptry.module import Module
    from deptry.violations import Violation


@dataclass
class DEP006OptionalDependencyPlacementFinder(ViolationsFinder):
    """
    Flag imports of extra-only dependencies outside the modules mapped to that extra.

    Optional extras stay regular dependencies unless `optional_dependencies_runtime` maps them to
    source modules. This finder does not require those imports to be ImportError-guarded.
    """

    violation = DEP006OptionalDependencyPlacementViolation

    def find(self) -> list[Violation]:
        if not self.optional_dependencies_runtime:
            return []

        logging.debug("\nScanning for optional extra imports used outside their mapped modules...")
        self._warn_missing_runtime_groups()

        violations: list[Violation] = []
        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module
            if module.standard_library or module.local_module:
                continue

            providing_groups = self._providing_runtime_groups(module)
            if not providing_groups:
                continue

            if self._is_provided_by(module, self.project_dependencies):
                continue

            if self._is_ignored(module, providing_groups):
                continue

            for location in module_with_locations.locations:
                matching_groups = [
                    group for group in providing_groups if self._location_matches_group(location, group)
                ]
                if matching_groups:
                    continue
                group_label = "', '".join(providing_groups)
                for group in providing_groups:
                    logging.debug(
                        "Module %s imported outside mapped extra %s at %s.",
                        module.name,
                        group,
                        location.file,
                    )
                violations.append(self.violation(module, location, group=group_label))

        return violations

    def _warn_missing_runtime_groups(self) -> None:
        missing_groups = set(self.optional_dependencies_runtime) - set(self.optional_group_dependencies)
        if missing_groups:
            logging.warning(
                "Warning: Trying to map optional extras %s to source modules, but the following groups were not found: %s",
                list(self.optional_dependencies_runtime),
                list(missing_groups),
            )

    def _providing_runtime_groups(self, module: Module) -> list[str]:
        groups: list[str] = []
        for group, patterns in self.optional_dependencies_runtime.items():
            if not patterns:
                continue
            dependencies = self.optional_group_dependencies.get(group, ())
            if self._is_provided_by(module, dependencies):
                groups.append(group)
        return groups

    def _is_ignored(self, module: Module, providing_groups: Sequence[str]) -> bool:
        candidates = {module.name, *providing_groups}
        if module.package:
            candidates.add(module.package)
        if candidates.intersection(self.ignored_modules):
            logging.debug("Optional extra import '%s' found outside its mapped modules, but ignoring.", module.name)
            return True
        return False

    def _location_matches_group(self, location: Location, group: str) -> bool:
        module_name = _module_name_from_file(location.file, self.source_roots)
        return any(_module_matches_pattern(module_name, pattern) for pattern in self.optional_dependencies_runtime[group])

    @staticmethod
    def _is_provided_by(module: Module, dependencies: Sequence[Dependency]) -> bool:
        if not dependencies:
            return False
        names = {dependency.name for dependency in dependencies}
        if module.package and module.package in names:
            return True
        return any(module.name in dependency.top_levels for dependency in dependencies)


def _module_name_from_file(file: Path, source_roots: tuple[Path, ...]) -> str:
    resolved = file.resolve()
    roots = [root.resolve() for root in source_roots]
    cwd = Path.cwd().resolve()
    if cwd not in roots:
        roots.append(cwd)
    for root in roots:
        with suppress(ValueError):
            return _relative_path_to_module(resolved.relative_to(root))
    return _relative_path_to_module(Path(file.name))


def _relative_path_to_module(relative: Path) -> str:
    parts = list(relative.parts)
    if parts and Path(parts[-1]).suffix in {".py", ".pyi", ".ipynb"}:
        parts[-1] = Path(parts[-1]).stem
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _module_matches_pattern(module_name: str, pattern: str) -> bool:
    names = _module_name_and_suffixes(module_name)
    if pattern.endswith(".**") or pattern.endswith(".*"):
        base = pattern[: pattern.rfind(".")]
        return any(name == base or name.startswith(base + ".") for name in names)
    return any(name == pattern for name in names)


def _module_name_and_suffixes(module_name: str) -> list[str]:
    parts = module_name.split(".")
    return [".".join(parts[i:]) for i in range(len(parts))]
