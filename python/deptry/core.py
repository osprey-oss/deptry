from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.dependency_getter.builder import DependencyGetterBuilder
from deptry.exceptions import PyprojectFileNotFoundError
from deptry.reporters import GithubReporter, JSONReporter, TextReporter
from deptry.scanners.project import ProjectScanner
from deptry.scanners.uv_workspace import UvWorkspaceScanner
from deptry.utils import load_pyproject_toml

if TYPE_CHECKING:
    from pathlib import Path

    from deptry.config import Config


@dataclass
class UvWorkspaceConfig:
    members: tuple[Path, ...]


@dataclass
class Core:
    config: Config

    def run(self) -> None:
        uv_workspace_config = self._get_uv_workspace_config()
        if uv_workspace_config is None:
            dependency_getter = DependencyGetterBuilder(
                self.config.config,
                self.config.package_module_name_map,
                self.config.optional_dependencies_dev_groups,
                self.config.non_dev_dependency_groups,
                self.config.requirements_files,
                self.config.using_default_requirements_files,
                self.config.requirements_files_dev,
            ).build()
            violations = ProjectScanner(self.config, dependency_getter.get()).scan()
        else:
            violations = UvWorkspaceScanner(self.config, uv_workspace_config).scan()

        TextReporter(
            violations, enforce_posix_paths=self.config.enforce_posix_paths, use_ansi=not self.config.no_ansi
        ).report()

        if self.config.json_output:
            JSONReporter(
                violations, enforce_posix_paths=self.config.enforce_posix_paths, json_output=self.config.json_output
            ).report()

        if self.config.github_output:
            GithubReporter(
                violations,
                enforce_posix_paths=self.config.enforce_posix_paths,
                warning_ids=self.config.github_warning_errors,
            ).report()

        sys.exit(bool(violations))

    def _get_uv_workspace_config(self) -> UvWorkspaceConfig | None:
        try:
            pyproject_data = load_pyproject_toml(self.config.config)
        except PyprojectFileNotFoundError:
            return None

        workspace = pyproject_data.get("tool", {}).get("uv", {}).get("workspace")
        if not workspace:
            return None

        root = self.config.config.parent
        exclude_globs: list[str] = workspace.get("exclude", [])
        excluded = {path for glob_pattern in exclude_globs for path in root.glob(glob_pattern)}

        members = tuple(
            path
            for glob_pattern in workspace.get("members", [])
            for path in sorted(root.glob(glob_pattern))
            if path not in excluded
        )
        logging.debug("Found %d uv workspace member(s):", len(members))
        for member in members:
            logging.debug("  - %s", member)

        return UvWorkspaceConfig(members=members)
