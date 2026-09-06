from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any

from deptry.dependency import Dependency
from deptry.dependency_getter.pep621.base import PEP621DependencyGetter
from deptry.utils import load_pyproject_toml


@dataclass
class PoetryDependencyGetter(PEP621DependencyGetter):
    """
    Class that retrieves dependencies from a project that uses Poetry, either through PEP 621 syntax, Poetry specific
    syntax, or a mix of both.
    """

    def _get_dependencies(self) -> list[Dependency]:
        """
        Retrieve dependencies from either:
        - `[project.dependencies]` defined by PEP 621
        - `[tool.poetry.dependencies]` which is specific to Poetry

        If dependencies are set in `[project.dependencies]`, then assume that the project uses PEP 621 format to define
        dependencies. Even if `[tool.poetry.dependencies]` is populated, having entries in `[project.dependencies]`
        means that `[tool.poetry.dependencies]` is only used to enrich existing dependencies, and cannot be used to
        define additional ones.

        If no dependencies are found in `[project.dependencies]`, then extract dependencies present in
        `[tool.poetry.dependencies]`.
        """
        if dependencies := super()._get_dependencies():
            return dependencies

        pyproject_data = load_pyproject_toml(self.config)
        return self._extract_poetry_dependencies(pyproject_data["tool"]["poetry"].get("dependencies", {}))

    def _get_dependency_groups_dependencies(self) -> dict[str, list[Dependency]]:
        """
        In addition to `[dependency-groups]` defined by PEP 735, Poetry has its own dependency groups, defined under
        `[tool.poetry.group.<group>.dependencies]`. Both kinds are returned, so that groups listed in
        `non_dev_dependency_groups` are extracted as regular dependencies whichever syntax declares them.
        """
        pyproject_data = load_pyproject_toml(self.config)

        dependency_groups = super()._get_dependency_groups_dependencies()

        for group, group_values in pyproject_data.get("tool", {}).get("poetry", {}).get("group", {}).items():
            dependency_groups[group] = [
                *dependency_groups.get(group, []),
                *self._extract_poetry_dependencies(group_values.get("dependencies", {})),
            ]

        return dependency_groups

    def _get_dev_dependencies(
        self,
        dev_dependencies_from_optional: list[Dependency],
        dev_dependencies_from_dependency_groups: list[Dependency],
    ) -> list[Dependency]:
        """
        In addition to the dependency groups handled by `_get_dependency_groups_dependencies`, Poetry supports legacy
        development dependencies under `[tool.poetry.dev-dependencies]`.
        """
        dev_dependencies = super()._get_dev_dependencies(
            dev_dependencies_from_optional, dev_dependencies_from_dependency_groups
        )

        pyproject_data = load_pyproject_toml(self.config)
        poetry_dev_dependencies: dict[str, str] = {}

        with contextlib.suppress(KeyError):
            poetry_dev_dependencies = {
                **poetry_dev_dependencies,
                **pyproject_data["tool"]["poetry"]["dev-dependencies"],
            }

        return [*self._extract_poetry_dependencies(poetry_dev_dependencies), *dev_dependencies]

    def _extract_poetry_dependencies(self, poetry_dependencies: dict[str, Any]) -> list[Dependency]:
        return [
            Dependency(dep, self.config, module_names=self.package_module_name_map.get(dep))
            for dep in poetry_dependencies
            if dep != "python"
        ]
