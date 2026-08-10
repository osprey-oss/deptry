from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep001_missing.violation import DEP001MissingDependencyViolation

if TYPE_CHECKING:
    from deptry.module import Module
    from deptry.violations.base import Violation


@dataclass
class DEP001MissingDependenciesFinder(ViolationsFinder):
    """
    Given a list of imported modules and a list of project dependencies, determine which ones are missing.
    """

    violation = DEP001MissingDependencyViolation

    def find(self) -> list[Violation]:
        logging.debug("\nScanning for missing dependencies...")
        missing_dependencies: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)

            if self._is_missing(module):
                missing_dependencies.extend(
                    self.violation(module, location) for location in module_with_locations.locations
                )

        return missing_dependencies

    def _is_missing(self, module: Module) -> bool:
        if any([
            module.package is not None,
            module.is_provided_by_dependency,
            module.is_provided_by_dev_dependency,
            module.local_module,
        ]):
            return False

        if module.name in self.ignored_modules:
            logging.debug("Identified module '%s' as a missing dependency, but ignoring.", module.name)
            return False

        logging.debug("No package found to import module '%s' from. Marked as a missing dependency.", module.name)
        return True
