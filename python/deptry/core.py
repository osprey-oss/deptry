from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.dependency_getter.builder import DependencyGetterBuilder
from deptry.imports.extract import get_imported_modules_from_list_of_files
from deptry.module import ModuleBuilder, ModuleLocations
from deptry.python_file_finder import get_all_python_files_in
from deptry.reporters import GithubReporter, JSONReporter, TextReporter
from deptry.violations.finder import find_violations

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from deptry.dependency_getter.base import DependenciesExtract
    from deptry.violations import Violation


@dataclass
class Core:
    root: tuple[Path, ...]
    config: Path
    no_ansi: bool
    per_rule_ignores: Mapping[str, tuple[str, ...]]
    ignore: tuple[str, ...]
    exclude: tuple[str, ...]
    extend_exclude: tuple[str, ...]
    using_default_exclude: bool
    ignore_notebooks: bool
    requirements_files: tuple[str, ...]
    using_default_requirements_files: bool
    requirements_files_dev: tuple[str, ...]
    known_first_party: tuple[str, ...]
    json_output: str
    package_module_name_map: Mapping[str, tuple[str, ...]]
    optional_dependencies_dev_groups: tuple[str, ...]
    non_dev_dependency_groups: tuple[str, ...]
    experimental_namespace_package: bool
    enforce_posix_paths: bool
    github_output: bool
    github_warning_errors: tuple[str, ...]

    def run(self) -> None:
        self._log_config()

        dependency_getter = DependencyGetterBuilder(
            self.config,
            self.package_module_name_map,
            self.optional_dependencies_dev_groups,
            self.non_dev_dependency_groups,
            self.requirements_files,
            self.using_default_requirements_files,
            self.requirements_files_dev,
        ).build()

        dependencies_extract = dependency_getter.get()

        self._log_dependencies(dependencies_extract)

        python_files = self._find_python_files()
        local_modules = self._get_local_modules()
        standard_library_modules = self._get_standard_library_modules()

        imported_modules_with_locations = [
            ModuleLocations(
                ModuleBuilder(
                    module,
                    local_modules,
                    standard_library_modules,
                    dependencies_extract.dependencies,
                    dependencies_extract.dev_dependencies,
                ).build(),
                locations,
            )
            for module, locations in get_imported_modules_from_list_of_files(python_files).items()
        ]

        violations = find_violations(
            imported_modules_with_locations,
            dependencies_extract.dependencies,
            self.ignore,
            self.per_rule_ignores,
            standard_library_modules,
        )
        TextReporter(violations, enforce_posix_paths=self.enforce_posix_paths, use_ansi=not self.no_ansi).report()

        if self.json_output:
            JSONReporter(
                violations, enforce_posix_paths=self.enforce_posix_paths, json_output=self.json_output
            ).report()

        if self.github_output:
            GithubReporter(
                violations, enforce_posix_paths=self.enforce_posix_paths, warning_ids=self.github_warning_errors
            ).report()

        self._exit(violations)

    def _find_python_files(self) -> list[Path]:
        logging.debug("Collecting Python files to scan...")

        python_files = get_all_python_files_in(
            self.root, self.exclude, self.extend_exclude, self.using_default_exclude, self.ignore_notebooks
        )

        logging.debug(
            "Python files to scan for imports:\n%s\n", "\n".join(str(python_file) for python_file in python_files)
        )

        return python_files

    def _get_local_modules(self) -> set[str]:
        """
        Get all local Python modules from the source paths and `known_first_party` list.
        A module is considered a local Python module if it matches at least one of those conditions:
        - it is a directory that contains at least one Python file
        - it is a Python file that is not named `__init__.py` (since it is a special case)
        - it is set in the `known_first_party` list

        Source paths can be either directories (which are searched for modules) or individual
        Python files (whose stem is used as the module name).
        """
        guessed_local_modules: set[str] = set()

        for source in self.root:
            if source.is_file():  # likely a single file program
                if source.suffix == ".py" and source.name != "__init__.py":
                    guessed_local_modules.add(source.stem)
                continue

            for path in source.iterdir():
                if self._is_local_module(path):
                    guessed_local_modules.add(path.stem)

        return guessed_local_modules | set(self.known_first_party)

    def _is_local_module(self, path: Path) -> bool:
        """Guess if a module is a local Python module."""
        return bool(
            (path.is_file() and path.name != "__init__.py" and path.suffix == ".py")
            or (path.is_dir() and self._directory_has_python_files(path))
        )

    def _directory_has_python_files(self, path: Path) -> bool:
        """Check if there is any Python file in the current directory. If experimental support for namespace packages
        (PEP 420) is enabled, also search for Python files in subdirectories."""
        if self.experimental_namespace_package:
            for _root, _dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        return True
            return False

        return bool(list(path.glob("*.py")))

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

    @staticmethod
    def _exit(violations: list[Violation]) -> None:
        sys.exit(bool(violations))
