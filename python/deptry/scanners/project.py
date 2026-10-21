from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.imports.extract import get_imported_modules_from_list_of_files
from deptry.module import ModuleBuilder, ModuleLocations
from deptry.python_file_finder import get_all_python_files_in
from deptry.violations.finder import find_violations

if TYPE_CHECKING:
    from pathlib import Path

    from deptry.config import Config
    from deptry.dependency_getter.base import DependenciesExtract
    from deptry.violations import Violation


def is_local_module(path: Path, experimental_namespace_package: bool) -> bool:
    """Guess if a module is a local Python module."""
    return bool(
        (path.is_file() and path.name != "__init__.py" and path.suffix == ".py")
        or (path.is_dir() and _directory_has_python_files(path, experimental_namespace_package))
    )


def _directory_has_python_files(path: Path, experimental_namespace_package: bool) -> bool:
    """Check if there is any Python file in the current directory. If experimental support for namespace packages
    (PEP 420) is enabled, also search for Python files in subdirectories."""
    if experimental_namespace_package:
        for _root, _dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    return True
        return False

    return bool(list(path.glob("*.py")))


@dataclass
class ProjectScanner:
    config: Config
    dependencies_extract: DependenciesExtract
    workspace_sibling_module_names: frozenset[str] = frozenset()
    workspace_sibling_dep_names: frozenset[str] = frozenset()
    workspace_sibling_dep_top_levels: frozenset[str] = frozenset()

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
            self.workspace_sibling_dep_top_levels,
        )

    def _find_python_files(self) -> list[Path]:
        logging.debug("Collecting Python files to scan...")

        python_files = get_all_python_files_in(
            self.config.root,
            self.config.exclude,
            self.config.extend_exclude,
            self.config.using_default_exclude,
            self.config.ignore_notebooks,
        )

        logging.debug(
            "Python files to scan for imports:\n%s\n", "\n".join(str(python_file) for python_file in python_files)
        )

        return python_files

    def _get_local_modules(self) -> set[str]:
        """
        Get all local Python modules from the source directories and `known_first_party` list.
        A module is considered a local Python module if it matches at least one of those conditions:
        - it is a directory that contains at least one Python file
        - it is a Python file that is not named `__init__.py` (since it is a special case)
        - it is set in the `known_first_party` list
        """
        guessed_local_modules = {
            path.stem
            for source in self.config.root
            for path in source.iterdir()
            if is_local_module(path, self.config.experimental_namespace_package)
        }

        # A directory that holds another member of a uv workspace is not a module of the scanned project.
        return (guessed_local_modules - self.workspace_sibling_module_names) | set(self.config.known_first_party)

    @staticmethod
    def _get_standard_library_modules() -> frozenset[str]:
        return sys.stdlib_module_names

    def _log_config(self) -> None:
        logging.debug("Running with the following configuration:")
        for key, value in vars(self).items():
            logging.debug("%s: %s", key, value)
        logging.debug("")

    @staticmethod
    def _log_dependencies(dependencies_extract: DependenciesExtract) -> None:
        if dependencies_extract.dependencies:
            logging.debug("The project contains the following dependencies:")
            for dependency in dependencies_extract.dependencies:
                logging.debug(dependency)
            logging.debug("")

        if dependencies_extract.dev_dependencies:
            logging.debug("The project contains the following dev dependencies:")
            for dependency in dependencies_extract.dev_dependencies:
                logging.debug(dependency)
            logging.debug("")
