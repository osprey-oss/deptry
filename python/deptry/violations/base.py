from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
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
        standard_library_modules: A set of modules that are part of the standard library.
        workspace_sibling_module_names: A set of top-level module names provided by uv workspace
            siblings. These modules are available in the environment but must still be explicitly
            declared as dependencies by each member that imports them.
    """

    violation: ClassVar[type[Violation]]
    imported_modules_with_locations: list[ModuleLocations]
    dependencies: list[Dependency]
    standard_library_modules: frozenset[str]
    ignored_modules: tuple[str, ...] = ()
    workspace_sibling_module_names: frozenset[str] = frozenset()
    workspace_sibling_dep_names: frozenset[str] = frozenset()

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
