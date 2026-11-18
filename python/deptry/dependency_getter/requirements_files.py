from __future__ import annotations

import codecs
import itertools
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import requirements

from deptry.dependency import Dependency
from deptry.dependency_getter.base import DependenciesExtract, DependencyGetter

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from requirements.requirement import Requirement


# Byte order marks recognized by `pip`, ordered so that a longer mark is matched before a shorter prefix of it.
BOM_ENCODINGS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


@dataclass
class RequirementsTxtDependencyGetter(DependencyGetter):
    """Extract dependencies from requirements.txt files."""

    requirements_files: tuple[str, ...] = ("requirements.txt",)
    requirements_files_dev: tuple[str, ...] = ("dev-requirements.txt", "requirements-dev.txt")

    def get(self) -> DependenciesExtract:
        return DependenciesExtract(
            get_dependencies_from_requirements_files(self.requirements_files, self.package_module_name_map),
            get_dependencies_from_requirements_files(
                self._scan_for_dev_requirements_files(), self.package_module_name_map
            ),
        )

    def _scan_for_dev_requirements_files(self) -> list[str]:
        """
        Check if any of the files passed as requirements_files_dev exist, and if so; return them.
        """
        project_path = Path()

        dev_requirements_files = [
            file_name for file_name in self.requirements_files_dev if (project_path / file_name).exists()
        ]

        if dev_requirements_files:
            logging.debug("Found files with development requirements! %s", dev_requirements_files)

        return dev_requirements_files


def get_dependencies_from_requirements_files(
    file_names: Sequence[str], package_module_name_map: Mapping[str, Sequence[str]], is_dev: bool = False
) -> list[Dependency]:
    return list(
        itertools.chain(
            *(
                get_dependencies_from_requirements_file(file_name, package_module_name_map, is_dev)
                for file_name in file_names
            )
        )
    )


def get_dependencies_from_requirements_file(
    file_name: str, package_module_name_map: Mapping[str, Sequence[str]], is_dev: bool = False
) -> list[Dependency]:
    logging.debug("Scanning %s for %s", file_name, "dev dependencies" if is_dev else "dependencies")

    dependencies = []
    requirements_file = Path(file_name)

    for requirement in requirements.parse(_read_requirements_file(requirements_file)):
        if (
            dependency := _build_dependency_from_requirement(requirement, requirements_file, package_module_name_map)
        ) is not None:
            dependencies.append(dependency)

    return dependencies


def _read_requirements_file(requirements_file: Path) -> str:
    """
    Read a requirements file, honoring the byte order mark if there is one.

    `pip` supports requirements files encoded as UTF-8, UTF-16 or UTF-32 by looking at their BOM, so files that
    `pip` can install from should also be parseable by deptry. Files without a BOM are decoded as UTF-8.
    """
    content = requirements_file.read_bytes()

    for bom, encoding in BOM_ENCODINGS:
        if content.startswith(bom):
            return content.decode(encoding)

    return content.decode("utf-8")


def _build_dependency_from_requirement(
    requirement: Requirement, requirements_file: Path, package_module_name_map: Mapping[str, Sequence[str]]
) -> Dependency | None:
    """
    Build a dependency from an extracted requirement.
    """
    # Explicitly set types, as "name" and "uri" default to `None` in `Requirement`, and are not typed, so `mypy` always
    # assume that they both will be `None`.
    dependency_name: str | None = requirement.name
    dependency_uri: str | None = requirement.uri

    # If the dependency name could not be guessed, and we have a URI, try to guess it from the URI.
    if not dependency_name and dependency_uri:
        dependency_name = _extract_name_from_url(dependency_uri)

    if dependency_name is None:
        return None

    return Dependency(
        name=dependency_name,
        definition_file=requirements_file,
        module_names=package_module_name_map.get(dependency_name),
    )


def _extract_name_from_url(line: str) -> str | None:
    # Try to find egg, for url like git+https://github.com/xxxxx/package@xxxxx#egg=package
    match = re.search("egg=([a-zA-Z0-9-_]*)", line)
    if match:
        return match.group(1)

    # for url like git+https://github.com/name/python-module.git@0d6dc38d58
    match = re.search(r"\/((?:(?!\/).)*?)\.git", line)
    if match:
        return match.group(1)

    # for url like https://github.com/urllib3/urllib3/archive/refs/tags/1.26.8.zip
    match = re.search(r"\/((?:(?!\/).)*?)\/archive\/", line)
    if match:
        return match.group(1)

    logging.warning("Could not parse dependency name from url %s", line)
    return None
