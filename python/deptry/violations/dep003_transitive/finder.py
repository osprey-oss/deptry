from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep003_transitive.violation import DEP003TransitiveDependencyViolation

if TYPE_CHECKING:
    from deptry.module import Module
    from deptry.violations import Violation


@dataclass
class DEP003TransitiveDependenciesFinder(ViolationsFinder):
    """
    Given a list of imported modules and a list of project dependencies, determine which ones are transitive.
    This is done by elimination; if a module uses an installed package but the package is;
    - not a local directory
    - not in standard library
    - not a dependency
    - not a dev dependency

    Then it must be a transitive dependency.
    """

    violation = DEP003TransitiveDependencyViolation

    def find(self) -> list[Violation]:
        logging.debug("\nScanning for transitive dependencies...")
        transitive_dependencies: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)

            if self._is_transitive(module):
                # `self._is_transitive` only returns `True` if the package is not None.
                for location in module_with_locations.locations:
                    transitive_dependencies.append(self.violation(module, location))

        return transitive_dependencies

    def _is_transitive(self, module: Module) -> bool:
        if any([
            module.package is None,
            module.is_provided_by_dependency,
            module.is_provided_by_dev_dependency,
            module.local_module,
            module.name in self.workspace_sibling_module_names,
            module.package in self.workspace_sibling_dep_names,
        ]):
            return False

        if module.name in self.ignored_modules:
            logging.debug("Dependency '%s' found to be a transitive dependency, but ignoring.", module.package)
            return False

        logging.debug("Dependency '%s' marked as a transitive dependency.", module.package)
        return True
