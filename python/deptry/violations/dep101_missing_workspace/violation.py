from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from deptry.violations.base import Violation


@dataclass
class DEP101MissingWorkspaceDependencyViolation(Violation):
    error_code: ClassVar[str] = "DEP101"
    error_template: ClassVar[str] = "'{name}' imported but it is a uv workspace sibling not declared as a dependency"

    def get_error_message(self) -> str:
        return self.error_template.format(name=self.issue.name)
