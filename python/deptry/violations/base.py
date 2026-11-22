from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from deptry.dependency import Dependency
    from deptry.imports.location import Location
    from deptry.module import Module, ModuleLocations


@dataclass
class ViolationsFinder(ABC):
    """Base class for all issues finders.

    This abstract class provides a common interface for classes that find issues related to project dependencies.
    Subclasses must implement the 'find' method, which returns a list of Violation objects representing the issues found.

    Attributes:
        imported_modules_with_locations: A list of ModuleLocations objects representing the
            modules imported by the project and their locations.
        dependencies: A list of Dependency objects representing the project's dependencies.
        ignored_modules: A tuple of module names to ignore when scanning for issues. Defaults to an
            empty tuple.
        standard_library_modules: A set of modules that are part of the standard library
        optional_dependencies_runtime: Mapping of optional extra names to module patterns that may import them
        optional_group_dependencies: Dependencies declared in each non-dev optional extra
        project_dependencies: Dependencies declared in the project's main dependency list
        source_roots: Directories passed as ROOT when invoking deptry
    """

    violation: ClassVar[type[Violation]]
    imported_modules_with_locations: list[ModuleLocations]
    dependencies: list[Dependency]
    standard_library_modules: frozenset[str]
    ignored_modules: tuple[str, ...] = ()
    optional_dependencies_runtime: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    optional_group_dependencies: Mapping[str, Sequence[Dependency]] = field(default_factory=dict)
    project_dependencies: Sequence[Dependency] = ()
    source_roots: tuple[Path, ...] = ()

    @abstractmethod
    def find(self) -> list[Violation]:
        """Find issues about dependencies."""
        raise NotImplementedError()


@dataclass
class Violation(ABC):
    """
    An abstract base class representing a violation found in the project's dependencies.

    Attributes:
        error_code: A class variable representing the error code associated with the violation. e.g.
            `DEP001`.
        error_template: A class variable representing a string template used to generate an error
            message for the violation.
        issue: An attribute representing the module or dependency where the violation
            occurred.
        location: An attribute representing the location in the code where the violation occurred.
    """

    error_code: ClassVar[str] = ""
    error_template: ClassVar[str] = ""
    issue: Dependency | Module
    location: Location

    @abstractmethod
    def get_error_message(self) -> str:
        raise NotImplementedError()
