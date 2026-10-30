from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.dependency import parse_pep_508_dependency
from deptry.dependency_getter.base import DependenciesExtract, DependencyGetter
from deptry.dependency_getter.requirements_files import get_dependencies_from_requirements_files
from deptry.utils import load_pyproject_toml

if TYPE_CHECKING:
    from typing import Any

    from deptry.dependency import Dependency


@dataclass
class PEP621DependencyGetter(DependencyGetter):
    """
    Class to extract dependencies from a pyproject.toml file in which dependencies are specified according to PEP 621. For example:

        [project]
        ...
        dependencies = [
            "httpx",
            "gidgethub[httpx]>4.0.0",
            "django>2.1; os_name != 'nt'",
            "django>2.0; os_name == 'nt'"
        ]

        [project.optional-dependencies]
        test = [
            "pytest < 5.0.0",
            "pytest-cov[all]"
        ]

    Note that by default both dependencies and optional-dependencies are extracted as regular dependencies, since PEP-621 does not specify
    a recommended way to extract development dependencies. However, if a value is passed for the `optional_dependencies_dev_groups`
    argument, all dependencies from groups in that argument are considered to be development dependencies. e.g. in the example above, when
    `optional_dependencies_dev_groups=(test,)`, both `pytest` and `pytest-cov` are returned as development dependencies.
    """

    optional_dependencies_dev_groups: tuple[str, ...] = ()
    non_dev_dependency_groups: tuple[str, ...] = ()

    def get(self) -> DependenciesExtract:
        dependencies = self._get_dependencies()
        optional_dependencies = self._get_optional_dependencies()
        dependency_groups_dependencies = self._get_dependency_groups_dependencies()

        dev_dependencies_from_optional, remaining_optional_dependencies = (
            self._split_development_dependencies_from_optional_dependencies(optional_dependencies)
        )
        dev_dependencies_from_dependency_groups, remaining_dependency_groups_dependencies = (
            self._split_development_dependencies_from_dependency_groups(dependency_groups_dependencies)
        )
        return DependenciesExtract(
            [*dependencies, *remaining_optional_dependencies, *remaining_dependency_groups_dependencies],
            self._get_dev_dependencies(dev_dependencies_from_optional, dev_dependencies_from_dependency_groups),
            optional_group_dependencies={
                group: tuple(group_dependencies)
                for group, group_dependencies in optional_dependencies.items()
                if group not in self.optional_dependencies_dev_groups
            },
            project_dependencies=tuple(dependencies),
        )

    def _get_dependencies(self) -> list[Dependency]:
        """Extract dependencies from `[project.dependencies]` (https://packaging.python.org/en/latest/specifications/pyproject-toml/#dependencies-optional-dependencies)."""
        pyproject_data = load_pyproject_toml(self.config)

        if self._project_uses_setuptools(pyproject_data) and "dependencies" in pyproject_data.get("project", {}).get(
            "dynamic", {}
        ):
            dependencies_files = pyproject_data["tool"]["setuptools"]["dynamic"]["dependencies"]["file"]
            if isinstance(dependencies_files, str):
                dependencies_files = [dependencies_files]

            return get_dependencies_from_requirements_files(dependencies_files, self.package_module_name_map)

        dependency_strings: list[str] = pyproject_data.get("project", {}).get("dependencies", [])
        return self._extract_pep_508_dependencies(dependency_strings)

    def _get_optional_dependencies(self) -> dict[str, list[Dependency]]:
        """Extract dependencies from `[project.optional-dependencies]` (https://packaging.python.org/en/latest/specifications/pyproject-toml/#dependencies-optional-dependencies)."""
        pyproject_data = load_pyproject_toml(self.config)

        if self._project_uses_setuptools(pyproject_data) and "optional-dependencies" in pyproject_data.get(
            "project", {}
        ).get("dynamic", {}):
            return {
                group: get_dependencies_from_requirements_files(
                    [specification["file"]] if isinstance(specification["file"], str) else specification["file"],
                    self.package_module_name_map,
                )
                for group, specification in pyproject_data["tool"]["setuptools"]["dynamic"]
                .get("optional-dependencies", {})
                .items()
            }

        return {
            group: self._extract_pep_508_dependencies(dependencies)
            for group, dependencies in pyproject_data.get("project", {}).get("optional-dependencies", {}).items()
        }

    def _get_dependency_groups_dependencies(self) -> dict[str, list[Dependency]]:
        """Extract dependencies from `[dependency-groups]` (https://peps.python.org/pep-0735/)."""
        pyproject_data = load_pyproject_toml(self.config)

        return {
            # PEP 735 supports maps in dependency groups, to for instance extend existing
            # groups (https://peps.python.org/pep-0735/#dependency-group-include). Since we do not need to treat group
            # extension right now, and there are no other existing key, we want to filter out non-string items.
            group: self._extract_pep_508_dependencies(list(filter(lambda x: isinstance(x, str), dependencies)))
            for group, dependencies in pyproject_data.get("dependency-groups", {}).items()
        }

    def _get_dev_dependencies(
        self,
        dev_dependencies_from_optional: list[Dependency],
        dev_dependencies_from_dependency_groups: list[Dependency],
    ) -> list[Dependency]:
        return [*dev_dependencies_from_optional, *dev_dependencies_from_dependency_groups]

    @staticmethod
    def _project_uses_setuptools(pyproject_toml: dict[str, Any]) -> bool:
        try:
            if pyproject_toml["build-system"]["build-backend"] == "setuptools.build_meta":
                logging.debug(
                    "pyproject.toml has the entry build-system.build-backend == 'setuptools.build_meta', so setuptools"
                    "is used to specify the project's dependencies."
                )
                return True
            else:
                logging.debug(
                    "pyproject.toml does not have build-system.build-backend == 'setuptools.build_meta', so setuptools "
                    "is not used to specify the project's dependencies."
                )
                return False
        except KeyError:
            logging.debug(
                "pyproject.toml does not contain a build-system.build-backend entry, so setuptools is not used to "
                "specify the project's dependencies."
            )
            return False

    def _split_development_dependencies_from_optional_dependencies(
        self, optional_dependencies: dict[str, list[Dependency]]
    ) -> tuple[list[Dependency], list[Dependency]]:
        """
        Split the optional dependencies into optional dependencies and development dependencies based on the `optional_dependencies_dev_groups`
        parameter. Return a tuple with two values: a list of the development dependencies and a list of the remaining 'true' optional dependencies.
        """
        dev_dependencies: list[Dependency] = []
        regular_dependencies: list[Dependency] = []

        if self.optional_dependencies_dev_groups and (
            missing_groups := set(self.optional_dependencies_dev_groups) - set(optional_dependencies.keys())
        ):
            logging.warning(
                "Warning: Trying to extract the dependencies from the optional dependency groups %s as development dependencies, "
                "but the following groups were not found: %s",
                list(self.optional_dependencies_dev_groups),
                list(missing_groups),
            )

        for group, dependencies in optional_dependencies.items():
            if group in self.optional_dependencies_dev_groups:
                dev_dependencies.extend(dependencies)
            else:
                regular_dependencies.extend(dependencies)

        return dev_dependencies, regular_dependencies

    def _split_development_dependencies_from_dependency_groups(
        self, dependency_groups: dict[str, list[Dependency]]
    ) -> tuple[list[Dependency], list[Dependency]]:
        dev_dependencies: list[Dependency] = []
        regular_dependencies: list[Dependency] = []

        if self.non_dev_dependency_groups and (
            missing_groups := set(self.non_dev_dependency_groups) - set(dependency_groups.keys())
        ):
            logging.warning(
                "Warning: Trying to extract the dependencies from the dependency groups %s as regular dependencies, "
                "but the following groups were not found: %s",
                list(self.non_dev_dependency_groups),
                list(missing_groups),
            )

        for group, dependencies in dependency_groups.items():
            if group in self.non_dev_dependency_groups:
                regular_dependencies.extend(dependencies)
            else:
                dev_dependencies.extend(dependencies)

        return dev_dependencies, regular_dependencies

    def _extract_pep_508_dependencies(self, dependencies: list[str]) -> list[Dependency]:
        """
        Given a list of dependency specifications (e.g. "django>2.1; os_name != 'nt'"), convert them to Dependency objects.
        """
        extracted_dependencies: list[Dependency] = []

        for dependency in dependencies:
            if extracted_dependency := parse_pep_508_dependency(dependency, self.config, self.package_module_name_map):
                extracted_dependencies.append(extracted_dependency)

        return extracted_dependencies
