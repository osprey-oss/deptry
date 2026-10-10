from __future__ import annotations

import logging
import re
from contextlib import suppress
from importlib import metadata
from typing import TYPE_CHECKING

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from importlib.metadata import Distribution
    from pathlib import Path


class Dependency:
    """
    A project's dependency with its associated top-level module names. There are stored in the metadata's top_level.txt.
    An example of this is 'matplotlib' with top-levels: ['matplotlib', 'mpl_toolkits', 'pylab'].

    Attributes:
        name (str): The name of the dependency.
        definition_file (Path): The path to the file defining the dependency, e.g. 'pyproject.toml'.
          and that can be used to create a variant of the package with a set of extra functionalities.
        found (bool): Indicates if the dependency has been found in the environment.
        top_levels (set[str]): The top-level module names associated with the dependency.
    """

    def __init__(
        self,
        name: str,
        definition_file: Path,
        module_names: Sequence[str] | None = None,
    ) -> None:
        distribution = self.find_distribution(name)

        self.name = name
        self.definition_file = definition_file
        self.found = distribution is not None
        self.top_levels = self._get_top_levels(name, distribution, module_names)

    def _get_top_levels(
        self, name: str, distribution: Distribution | None, module_names: Sequence[str] | None
    ) -> set[str]:
        """
        Get the top-level module names for a dependency. They are searched for in the following order:
                1. If `module_names` is defined, simply use those as the top-level modules.
                2. Otherwise, try to extract the top-level module names from the metadata.
                3. If metadata extraction fails, fall back to the dependency's name, where `-` is replaced with `_`.

        Args:
            name: The name of the dependency.
            distribution: The metadata distribution of the package.
            module_names: If this is given, use these as the top-level modules instead of
                searching for them in the metadata.
        """
        if module_names is not None:
            return set(module_names)

        if distribution is not None:
            with suppress(FileNotFoundError):
                return self._get_top_level_module_names_from_top_level_txt(distribution)

            with suppress(FileNotFoundError):
                return self._get_top_level_module_names_from_record_file(distribution)

        # No metadata or other configuration has been found. As a fallback
        # we'll guess the name.
        module_name = name.replace("-", "_").lower()
        logging.warning(
            "Assuming the corresponding module name of package %r is %r. Install the package or configure a"
            " package_module_name_map entry to override this behaviour.",
            self.name,
            module_name,
        )
        return {module_name}

    def __repr__(self) -> str:
        return f"Dependency '{self.name}'"

    def __str__(self) -> str:
        return f"Dependency '{self.name}' with top-levels: {self.top_levels}."

    @staticmethod
    def find_distribution(name: str) -> Distribution | None:
        try:
            return metadata.distribution(name)
        except metadata.PackageNotFoundError:
            return None

    @staticmethod
    def _get_top_level_module_names_from_top_level_txt(distribution: Distribution) -> set[str]:
        """
        top-level.txt is a metadata file added by setuptools that looks as follows:

        610faff656c4cfcbb4a3__mypyc
        _black_version
        black
        blackd
        blib2to3

        This function extracts these names, if a top-level.txt file exists.
        """
        metadata_top_levels = distribution.read_text("top_level.txt")
        if metadata_top_levels is None:
            raise FileNotFoundError("top_level.txt")

        return {x for x in metadata_top_levels.splitlines() if x}

    @staticmethod
    def _get_top_level_module_names_from_record_file(distribution: Distribution) -> set[str]:
        """
        Get the top-level module names from the RECORD file, whose contents usually look as follows:

            ...
            ../../../bin/black,sha256=<HASH>,247
            __pycache__/_black_version.cpython-311.pyc,,
            _black_version.py,sha256=<HASH>,19
            black/trans.cpython-39-darwin.so,sha256=<HASH>
            black/trans.py,sha256=<HASH>
            blackd/__init__.py,sha256=<HASH>
            blackd/__main__.py,sha256=<HASH>
            ...

        So if no file top-level.txt is provided, we can try and extract top-levels from this file, in
        this case _black_version, black, and blackd.
        """
        metadata_records = distribution.read_text("RECORD")

        if metadata_records is None:
            raise FileNotFoundError("RECORD")

        matches = re.finditer(r"^(?!__)([a-zA-Z0-9-_]+)(?:/|\.py,)", metadata_records, re.MULTILINE)

        return {x.group(1) for x in matches}


def parse_pep_508_dependency(
    specification: str, definition_file: Path, package_module_name_map: Mapping[str, Sequence[str]]
) -> Dependency | None:
    try:
        requirement = Requirement(specification)
    except InvalidRequirement:
        return None

    return Dependency(
        name=requirement.name,
        definition_file=definition_file,
        module_names=package_module_name_map.get(
            requirement.name, package_module_name_map.get(canonicalize_name(requirement.name))
        ),
    )
