from __future__ import annotations

import logging
import site
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import TYPE_CHECKING

from deptry.dependency_getter.base import DependenciesExtract
from deptry.dependency_getter.pep621.uv import UvDependencyGetter
from deptry.scanners.project import ProjectScanner
from deptry.utils import load_pyproject_toml

if TYPE_CHECKING:
    from importlib.metadata import Distribution

    from deptry.config import Config
    from deptry.core import UvWorkspaceConfig
    from deptry.violations import Violation


@dataclass
class UvWorkspaceScanner:
    config: Config
    uv_workspace_config: UvWorkspaceConfig

    def scan(self) -> list[Violation]:

        package_module_name_map = self._build_workspace_package_module_name_map(self.uv_workspace_config.members)
        logging.debug("Resolved package-to-module map from editable installs:")
        for package, modules in package_module_name_map.items():
            logging.debug("  %s -> %s", package, ", ".join(modules))

        root_extract = self._get_root_extract()

        # Pass 1: collect declared dependencies for every member upfront, so that each member
        # scan can receive the union of its siblings' direct dependencies.
        member_base_configs: dict[Path, Config] = {}
        member_dependencies_extracts: dict[Path, DependenciesExtract] = {}
        for member in self.uv_workspace_config.members:
            member_base_config = self._build_member_base_config(member)
            member_base_configs[member] = member_base_config
            member_dependencies_extract = UvDependencyGetter(
                member / "pyproject.toml",
                member_base_config.package_module_name_map,
                member_base_config.optional_dependencies_dev_groups,
                member_base_config.non_dev_dependency_groups,
            ).get()
            member_dependencies_extracts[member] = member_dependencies_extract

        # Pass 2: scan each member with full sibling context.
        violations: list[Violation] = []
        for member in self.uv_workspace_config.members:
            logging.debug("Scanning workspace member: %s", member)
            member_package_name = self._get_package_name(member)
            member_module_names = (
                frozenset(package_module_name_map.get(member_package_name, ())) if member_package_name else frozenset()
            )
            sibling_module_names, sibling_dep_names = self._get_sibling_context(
                member, package_module_name_map, member_module_names, member_dependencies_extracts
            )
            merged_extract = DependenciesExtract(
                dependencies=member_dependencies_extracts[member].dependencies,
                dev_dependencies=[
                    *member_dependencies_extracts[member].dev_dependencies,
                    *root_extract.dev_dependencies,
                ],
            )
            violations += ProjectScanner(
                member_base_configs[member],
                merged_extract,
                sibling_module_names,
                sibling_dep_names,
            ).scan()
        return violations

    @staticmethod
    def _get_sibling_context(
        member: Path,
        package_module_name_map: dict[str, tuple[str, ...]],
        member_module_names: frozenset[str],
        member_extracts: dict[Path, DependenciesExtract],
    ) -> tuple[frozenset[str], frozenset[str]]:
        sibling_module_names = (
            frozenset(m for modules in package_module_name_map.values() for m in modules) - member_module_names
        )
        sibling_dep_names = frozenset(
            dep.name
            for other_member, extract in member_extracts.items()
            if other_member != member
            for dep in (*extract.dependencies, *extract.dev_dependencies)
        )
        return sibling_module_names, sibling_dep_names

    def _build_member_base_config(self, member: Path) -> Config:
        """Build a Config for a workspace member, applying any [tool.deptry] from its pyproject.toml."""
        try:
            data = load_pyproject_toml(member / "pyproject.toml")
        except FileNotFoundError:
            data = {}
        member_deptry_config = data.get("tool", {}).get("deptry", {})
        return self.config.with_overrides({
            **member_deptry_config,
            "config": member / "pyproject.toml",
            "root": (member,),
        })

    def _get_root_extract(self) -> DependenciesExtract:
        """Retrieve dev dependencies declared at the workspace root (e.g. [tool.uv.dev-dependencies],
        [dependency-groups]). These are installed into the shared environment and should be visible
        to all member scans as dev dependencies."""
        return UvDependencyGetter(
            self.config.config,
            self.config.package_module_name_map,
            self.config.optional_dependencies_dev_groups,
            self.config.non_dev_dependency_groups,
        ).get()

    def _build_workspace_package_module_name_map(self, members: tuple[Path, ...]) -> dict[str, tuple[str, ...]]:
        """
        For each workspace member, find its editable-install .pth file via importlib.metadata,
        resolve the source root it points to, and discover top-level Python modules there.
        Returns a mapping of {package_name: (module_name, ...)}.
        """
        result: dict[str, tuple[str, ...]] = {}

        for member in members:
            package_name = self._get_package_name(member)
            if package_name is None:
                logging.debug("Could not determine package name for %s, skipping.", member)
                continue

            modules = self._get_modules_for_package(package_name)
            if modules:
                logging.debug("Package '%s': modules: %s", package_name, modules)
                result[package_name] = modules

        return result

    @staticmethod
    def _get_package_name(member: Path) -> str | None:
        """Read the distribution name from the member's pyproject.toml."""
        try:
            data = load_pyproject_toml(member / "pyproject.toml")
        except FileNotFoundError:
            return None
        name = data.get("project", {}).get("name")
        return str(name) if name is not None else None

    @staticmethod
    def _get_modules_for_package(package_name: str) -> tuple[str, ...]:
        """Use importlib.metadata to find the editable-install .pth file for the package,
        then discover top-level Python modules in the source root it points to."""
        try:
            dist = distribution(package_name)
        except PackageNotFoundError:
            logging.debug("Package '%s' is not installed in the current environment.", package_name)
            return ()

        source_root = UvWorkspaceScanner._find_pth_source_root(package_name, dist)
        if source_root is None:
            logging.debug("No .pth file found for package '%s'.", package_name)
            return ()

        return UvWorkspaceScanner._collect_top_level_modules(source_root)

    @staticmethod
    def _find_pth_source_root(package_name: str, dist: Distribution) -> Path | None:
        """Locate the editable-install .pth file in site-packages and return the source root it points to."""
        for f in (f for f in dist.files or [] if f.suffix == ".pth"):
            for sp in site.getsitepackages():
                pth_path = Path(sp) / f
                if not pth_path.exists():
                    continue
                source_root = Path(pth_path.read_text(encoding="utf-8").strip())
                if source_root.is_dir():
                    return source_root
                logging.debug(".pth for '%s' points to non-existent directory: %s", package_name, source_root)
        return None

    @staticmethod
    def _collect_top_level_modules(source_root: Path) -> tuple[str, ...]:
        """Discover top-level Python packages and modules directly under source_root."""
        return tuple(
            entry.name if entry.is_dir() else entry.stem
            for entry in sorted(source_root.iterdir())
            if not entry.name.startswith(".")
            and (
                (entry.is_dir() and (entry / "__init__.py").exists())
                or (entry.is_file() and entry.suffix == ".py" and entry.name != "__init__.py")
            )
        )
