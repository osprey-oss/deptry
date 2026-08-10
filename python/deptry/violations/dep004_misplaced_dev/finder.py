from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep004_misplaced_dev.violation import DEP004MisplacedDevDependencyViolation

if TYPE_CHECKING:
    from deptry.module import Module
    from deptry.violations import Violation

from dataclasses import dataclass


@dataclass
class DEP004MisplacedDevDependenciesFinder(ViolationsFinder):
    """
    Given a list of imported modules and a list of project dependencies, determine which development dependencies
    should actually be regular dependencies.

    This is the case for any development dependency encountered, since files solely used for development purposes should be excluded from scanning.
    """

    violation = DEP004MisplacedDevDependencyViolation

    def find(self) -> list[Violation]:
        """
        In this function, we use 'corresponding_package_name' instead of module.package, since it can happen that a
        development dependency is not installed, but it's still found to be used in the codebase, due to simple name
        matching. In that case, it's added under module.dev_top_levels. _get_package_name is added for these edge-cases.
        """
        logging.debug("\nScanning for incorrect development dependencies...")
        misplaced_dev_dependencies: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)
            corresponding_package_name = self._get_package_name(module)

            if corresponding_package_name and self._is_development_dependency(module, corresponding_package_name):
                misplaced_dev_dependencies.extend(
                    self.violation(module, location) for location in module_with_locations.locations
                )

        return misplaced_dev_dependencies

    def _is_development_dependency(self, module: Module, corresponding_package_name: str) -> bool:
        # Module can be provided both by a regular and by a development dependency.
        # Only continue if module is ONLY provided by a dev dependency.
        if not module.is_provided_by_dev_dependency or module.is_provided_by_dependency:
            return False

        if module.name in self.ignored_modules:
            logging.debug(
                "Dependency '%s' found to be a misplaced development dependency, but ignoring.",
                corresponding_package_name,
            )
            return False

        logging.debug("Dependency '%s' marked as a misplaced development dependency.", corresponding_package_name)
        return True

    def _get_package_name(self, module: Module) -> str | None:
        if module.package:
            return module.package
        if module.dev_top_levels:
            if len(module.dev_top_levels) > 1:
                logging.debug(
                    "Module %s is found in the top-level module names of multiple development dependencies. Skipping.",
                    module.name,
                )
            elif len(module.dev_top_levels) == 0:
                logging.debug(
                    "Module %s has no metadata and it is not found in any top-level module names. Skipping.",
                    module.name,
                )
            else:
                return module.dev_top_levels[0]
        return None
