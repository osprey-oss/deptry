from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep102_workspace_leaked.violation import DEP102WorkspaceLeakedDependencyViolation

if TYPE_CHECKING:
    from deptry.module import Module
    from deptry.violations import Violation


@dataclass
class DEP102WorkspaceLeakedDependenciesFinder(ViolationsFinder):
    """
    Given a list of imported modules, determine which ones are leaked from another uv workspace member: the package
    is a direct dependency of a sibling member, but the current member does not declare it itself.

    The import only works because uv installs the dependencies of all workspace members into a shared environment.
    This is distinct from DEP003 (transitive dependencies): here, the package is installed because a sibling declares
    it, and the current member may have no dependency path to it at all.
    """

    violation = DEP102WorkspaceLeakedDependencyViolation

    def find(self) -> list[Violation]:
        logging.debug("\nScanning for workspace leaked dependencies...")
        leaked_dependencies: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)

            if self._is_workspace_leaked(module):
                for location in module_with_locations.locations:
                    leaked_dependencies.append(self.violation(module, location))

        return leaked_dependencies

    def _is_workspace_leaked(self, module: Module) -> bool:
        if not self._is_provided_by_workspace_sibling_dependency(module):
            return False

        if any([
            module.is_provided_by_dependency,
            module.is_provided_by_dev_dependency,
            module.local_module,
            module.name in self.workspace_sibling_module_names,
        ]):
            return False

        if module.name in self.ignored_modules:
            logging.debug("Dependency '%s' found to be a workspace leaked dependency, but ignoring.", module.package)
            return False

        logging.debug("Dependency '%s' marked as a workspace leaked dependency.", module.package)
        return True
