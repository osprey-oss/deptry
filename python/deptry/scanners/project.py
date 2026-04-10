from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.imports.extract import get_imported_modules_from_list_of_files
from deptry.module import ModuleBuilder, ModuleLocations
from deptry.scanners.base import ProjectScannerBase
from deptry.violations.finder import find_violations

if TYPE_CHECKING:
    from deptry.dependency_getter.base import DependenciesExtract
    from deptry.violations import Violation


@dataclass
class ProjectScanner(ProjectScannerBase):
    dependencies_extract: DependenciesExtract
    workspace_sibling_module_names: frozenset[str] = frozenset()
    workspace_sibling_dep_names: frozenset[str] = frozenset()

    def scan(self) -> list[Violation]:
        self._log_config()
        self._log_dependencies(self.dependencies_extract)

        python_files = self._find_python_files()
        local_modules = self._get_local_modules()
        standard_library_modules = self._get_standard_library_modules()

        imported_modules_with_locations = [
            ModuleLocations(
                ModuleBuilder(
                    module,
                    local_modules,
                    standard_library_modules,
                    self.dependencies_extract.dependencies,
                    self.dependencies_extract.dev_dependencies,
                ).build(),
                locations,
            )
            for module, locations in get_imported_modules_from_list_of_files(python_files).items()
        ]

        return find_violations(
            imported_modules_with_locations,
            self.dependencies_extract.dependencies,
            self.config.ignore,
            self.config.per_rule_ignores,
            standard_library_modules,
            self.workspace_sibling_module_names,
            self.workspace_sibling_dep_names,
        )
