from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.violations.base import ViolationsFinder
from deptry.violations.dep102_workspace_transitive.violation import DEP102WorkspaceTransitiveDependencyViolation

if TYPE_CHECKING:
    from deptry.module import Module
    from deptry.violations import Violation


@dataclass
class DEP102WorkspaceTransitiveDependenciesFinder(ViolationsFinder):
    """
    Given a list of imported modules, determine which ones are available in the workspace
    environment only because another workspace member declares them as a direct dependency,
    without the current member declaring them itself.

    These are distinct from DEP003 (transitive dependencies of the current member's own deps):
    here the package is not reachable through the current member's dependency tree at all —
    it is solely present in the shared venv due to a sibling's declaration.
    """

    violation = DEP102WorkspaceTransitiveDependencyViolation

    def find(self) -> list[Violation]:
        logging.debug("\nScanning for workspace-propagated dependencies...")
        violations: list[Violation] = []

        for module_with_locations in self.imported_modules_with_locations:
            module = module_with_locations.module

            if module.standard_library:
                continue

            logging.debug("Scanning module %s...", module.name)

            if self._is_workspace_transitive(module):
                for location in module_with_locations.locations:
                    violations.append(self.violation(module, location))

        return violations

    def _is_workspace_transitive(self, module: Module) -> bool:
        if module.package not in self.workspace_sibling_dep_names:
            return False

        if any([
            module.is_provided_by_dependency,
            module.is_provided_by_dev_dependency,
            module.local_module,
            module.name in self.workspace_sibling_module_names,
        ]):
            return False

        if module.name in self.ignored_modules:
            logging.debug("Module '%s' is a workspace-propagated dependency, but ignoring.", module.name)
            return False

        logging.debug("Package '%s' is available only because a workspace sibling declares it.", module.package)
        return True
