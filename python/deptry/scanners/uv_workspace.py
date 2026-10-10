from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from packaging.utils import canonicalize_name

from deptry.dependency_getter.pep621.uv import UvDependencyGetter
from deptry.exceptions import PyprojectFileNotFoundError
from deptry.scanners.project import ProjectScanner, is_local_module
from deptry.utils import load_pyproject_toml

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from deptry.config import Config
    from deptry.dependency_getter.base import DependenciesExtract
    from deptry.violations import Violation


@dataclass(frozen=True)
class UvWorkspaceConfig:
    members: tuple[Path, ...]


def get_uv_workspace_config(config: Path) -> UvWorkspaceConfig | None:
    """
    Get the members of the uv workspace defined in `[tool.uv.workspace]`, or `None` if the given `pyproject.toml` is
    not the root of a uv workspace. Like in uv, a path matched by `members` is only a member if it is a directory that
    contains a `pyproject.toml`, and if it is not matched by `exclude`.
    """
    try:
        pyproject_data = load_pyproject_toml(config)
    except PyprojectFileNotFoundError:
        return None

    workspace = pyproject_data.get("tool", {}).get("uv", {}).get("workspace")
    if not workspace:
        return None

    root = config.parent
    excluded = {path for glob_pattern in workspace.get("exclude", []) for path in root.glob(glob_pattern)}

    # A dictionary is used to drop members matched by several patterns, while keeping them ordered.
    members = tuple(
        dict.fromkeys(
            path
            for glob_pattern in workspace.get("members", [])
            for path in sorted(root.glob(glob_pattern))
            if path not in excluded and (path / "pyproject.toml").is_file()
        )
    )
    logging.debug("Found %d uv workspace member(s):", len(members))
    for member in members:
        logging.debug("  - %s", member)

    return UvWorkspaceConfig(members=members)


@dataclass
class UvWorkspaceScanner:
    config: Config
    uv_workspace_config: UvWorkspaceConfig

    def scan(self) -> list[Violation]:
        members = self._get_members_to_scan()

        base_configs = {member: self._build_member_base_config(member, members) for member in members}
        package_names = {member: self._get_package_name(base_configs[member].config) for member in members}
        member_modules = {
            member: self._get_member_modules(member, members, base_configs[member].experimental_namespace_package)
            for member in members
        }
        for member in members:
            logging.debug("Workspace member %s: modules: %s", member, sorted(member_modules[member]))

        configs = {
            member: self._add_workspace_modules_to_config(member, base_configs[member], package_names, member_modules)
            for member in members
        }
        dependency_extracts = {
            member: UvDependencyGetter(
                config.config,
                config.package_module_name_map,
                config.optional_dependencies_dev_groups,
                config.non_dev_dependency_groups,
            ).get()
            for member, config in configs.items()
        }

        violations: list[Violation] = []
        for member in members:
            logging.debug("Scanning workspace member: %s", member)
            violations += ProjectScanner(
                configs[member],
                dependency_extracts[member],
                *self._get_sibling_context(member, member_modules, dependency_extracts),
            ).scan()
        return violations

    def _get_members_to_scan(self) -> tuple[Path, ...]:
        """Get the directories to scan. The workspace root is only one of them if it is a project itself, as opposed to
        a virtual root that only defines the workspace."""
        if "project" in load_pyproject_toml(self.config.config):
            return (self.config.config.parent, *self.uv_workspace_config.members)

        logging.debug("The workspace root has no [project] section, so only its members are scanned.")
        return self.uv_workspace_config.members

    def _build_member_base_config(self, member: Path, members: tuple[Path, ...]) -> Config:
        """Build a Config for a workspace member, without the context of the modules of the workspace.

        Directories of other members are excluded, so that their files are only scanned during their own scan. For the
        workspace root, the configuration is otherwise left untouched. For other members, any [tool.deptry] overrides
        from their pyproject.toml are applied, and their directory becomes the directory to scan."""
        other_members = [other_member for other_member in members if other_member != member]

        if member == self.config.config.parent:
            config = self.config
        else:
            member_deptry_config = load_pyproject_toml(member / "pyproject.toml").get("tool", {}).get("deptry", {})
            config = self.config.with_overrides({
                **member_deptry_config,
                "config": member / "pyproject.toml",
                "root": (member,),
            })
            # Exclusion patterns are matched from the start of paths that are prefixed with the scanned directory. For
            # patterns to behave like when running deptry from the member directory, also apply them from there.
            config = config.with_overrides({
                "exclude": (*config.exclude, *self._anchor_patterns_to(member, config.exclude)),
                "extend_exclude": (*config.extend_exclude, *self._anchor_patterns_to(member, config.extend_exclude)),
            })

        return config.with_overrides({
            "extend_exclude": (*config.extend_exclude, *self._get_member_exclude_patterns(config.root, other_members)),
        })

    @staticmethod
    def _anchor_patterns_to(directory: Path, patterns: Iterable[str]) -> tuple[str, ...]:
        prefix = re.escape(f"{directory.as_posix()}/")
        return tuple(f"{prefix}(?:{pattern})" for pattern in patterns)

    @staticmethod
    def _get_member_exclude_patterns(roots: Iterable[Path], members: Iterable[Path]) -> tuple[str, ...]:
        """Build the patterns that exclude the directories of the given members from a scan of the given roots.

        Patterns are matched from the start of paths that are prefixed with the root they are found in, exactly as it
        was passed, so each pattern is built from the root rather than from the member path. This makes them work for
        absolute roots too. Patterns end on a path separator or on the end of the path, to match whole path segments
        only (`packages/foo` must not exclude `packages/foobar`)."""
        patterns: list[str] = []
        for root in roots:
            resolved_root = root.resolve()
            for member in members:
                resolved_member = member.resolve()
                if resolved_member != resolved_root and resolved_member.is_relative_to(resolved_root):
                    member_in_root = root / resolved_member.relative_to(resolved_root)
                    patterns.append(f"{re.escape(member_in_root.as_posix())}(/|$)")
        return tuple(patterns)

    @staticmethod
    def _get_package_name(pyproject_toml: Path) -> str | None:
        """Read the distribution name from the member's pyproject.toml."""
        name = load_pyproject_toml(pyproject_toml).get("project", {}).get("name")
        return str(name) if name is not None else None

    @staticmethod
    def _get_member_modules(
        member: Path, members: Iterable[Path], experimental_namespace_package: bool
    ) -> frozenset[str]:
        """
        Get the top-level modules of a workspace member, by looking for local Python modules in its directory and in
        its `src` directory, if any. The `src` directory is not a module itself, and neither are directories that are
        or contain other workspace members (like `packages` in the workspace root), nor paths that cannot be imported.
        """
        source_roots = (member, member / "src")
        other_members = [other_member.resolve() for other_member in members if other_member != member]

        return frozenset(
            path.stem
            for source_root in source_roots
            if source_root.is_dir()
            for path in source_root.iterdir()
            if path not in source_roots
            and path.stem.isidentifier()
            and not any(other_member.is_relative_to(path.resolve()) for other_member in other_members)
            and is_local_module(path, experimental_namespace_package)
        )

    @staticmethod
    def _add_workspace_modules_to_config(
        member: Path,
        config: Config,
        package_names: Mapping[Path, str | None],
        member_modules: Mapping[Path, frozenset[str]],
    ) -> Config:
        """Make the member aware of its own modules, so that importing them is never a violation wherever they are
        located, and of the modules of its siblings, so that a sibling declared as a dependency is matched with the
        modules it provides even if they are not named after the package."""
        sibling_package_module_name_map = {
            canonicalize_name(package_name): tuple(sorted(modules))
            for sibling, modules in member_modules.items()
            if sibling != member and modules and (package_name := package_names[sibling]) is not None
        }

        return config.with_overrides({
            "known_first_party": (*config.known_first_party, *sorted(member_modules[member])),
            "package_module_name_map": {**sibling_package_module_name_map, **config.package_module_name_map},
        })

    @staticmethod
    def _get_sibling_context(
        member: Path,
        member_modules: Mapping[Path, frozenset[str]],
        dependency_extracts: Mapping[Path, DependenciesExtract],
    ) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
        """Compute the module names, the dependency names and the top-level modules of the dependencies from all sibling
        members. A module that the member also has itself is never a sibling module."""
        sibling_modules = frozenset(
            module for sibling, modules in member_modules.items() if sibling != member for module in modules
        )
        sibling_deps = [
            dep
            for sibling, extract in dependency_extracts.items()
            if sibling != member
            for dep in (*extract.dependencies, *extract.dev_dependencies)
        ]
        return (
            sibling_modules - member_modules[member],
            frozenset(canonicalize_name(dep.name) for dep in sibling_deps),
            frozenset(top_level for dep in sibling_deps for top_level in dep.top_levels),
        )
