from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep101_missing_workspace.violation import DEP101MissingWorkspaceDependencyViolation

if TYPE_CHECKING:
    from deptry.module import Module
    from deptry.violations import Violation


@dataclass
class DEP101MissingWorkspaceDependenciesFinder(ViolationsFinder):
    """
    Given a list of imported modules, determine which ones are provided by another uv workspace member that the
    current member does not declare as a dependency.

    The import only works because uv installs all workspace members into a shared environment, but each member must
    still explicitly declare the siblings it imports.
    """

    violation = DEP101MissingWorkspaceDependencyViolation

    def find(self) -> list[Violation]:
        logging.debug("\nScanning for missing workspace dependencies...")
        missing_workspace_dependencies: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)

            if self._is_missing_workspace_dependency(module):
                for location in module_with_locations.locations:
                    missing_workspace_dependencies.append(self.violation(module, location))

        return missing_workspace_dependencies

    def _is_missing_workspace_dependency(self, module: Module) -> bool:
        if module.name not in self.workspace_sibling_module_names:
            return False

        if any([
            module.is_provided_by_dependency,
            module.is_provided_by_dev_dependency,
            module.local_module,
        ]):
            return False

        if module.name in self.ignored_modules:
            logging.debug("Identified module '%s' as a missing workspace dependency, but ignoring.", module.name)
            return False

        logging.debug("Module '%s' marked as a missing workspace dependency.", module.name)
        return True
