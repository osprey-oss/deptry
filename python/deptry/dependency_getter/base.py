from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from deptry.dependency import Dependency


@dataclass
class DependenciesExtract:
    dependencies: list[Dependency]
    dev_dependencies: list[Dependency]
    optional_group_dependencies: dict[str, tuple[Dependency, ...]] = field(default_factory=dict)
    project_dependencies: tuple[Dependency, ...] = ()


@dataclass
class DependencyGetter(ABC):
    """Base class for all classes that extract a list of project's dependencies from a file.

    Args:
        config: The path to a configuration file that contains the project's dependencies.
        package_module_name_map: A mapping of package names to their corresponding module names that may not be found
        otherwise from the package's metadata. The keys in the mapping should be package names, and the values should
        be sequences of module names associated with the package.
    """

    config: Path
    package_module_name_map: Mapping[str, Sequence[str]] = field(default_factory=dict)

    @abstractmethod
    def get(self) -> DependenciesExtract:
        """Get extracted dependencies and dev dependencies."""
        raise NotImplementedError()
