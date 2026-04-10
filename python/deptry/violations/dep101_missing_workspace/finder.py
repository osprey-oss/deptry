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
    Given a list of imported modules, determine which ones are uv workspace siblings that are not
    declared as dependencies of the current workspace member.

    Workspace siblings are available in the shared venv because uv installs all workspace members,
    but each member must still explicitly declare the siblings it imports.
    """

    violation = DEP101MissingWorkspaceDependencyViolation

    def find(self) -> list[Violation]:
        logging.debug("\nScanning for missing workspace dependencies...")
        missing: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)

            if self._is_missing_workspace_dep(module):
                for location in module_with_locations.locations:
                    missing.append(self.violation(module, location))

        return missing

    def _is_missing_workspace_dep(self, module: Module) -> bool:
        if module.name not in self.workspace_sibling_module_names:
            return False

        if any([
            module.is_provided_by_dependency,
            module.is_provided_by_dev_dependency,
            module.local_module,
        ]):
            return False

        if module.name in self.ignored_modules:
            logging.debug("Module '%s' is an undeclared workspace sibling, but ignoring.", module.name)
            return False

        logging.debug("Module '%s' is a workspace sibling not declared as a dependency.", module.name)
        return True
