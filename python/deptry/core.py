from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.dependency_getter.builder import DependencyGetterBuilder
from deptry.reporters import GithubReporter, JSONReporter, TextReporter
from deptry.scanners.project import ProjectScanner
from deptry.scanners.uv_workspace import UvWorkspaceScanner, get_uv_workspace_config

if TYPE_CHECKING:
    from deptry.config import Config


@dataclass
class Core:
    config: Config

    def run(self) -> None:
        uv_workspace_config = get_uv_workspace_config(self.config.config)
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
