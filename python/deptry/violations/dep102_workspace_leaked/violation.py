from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from deptry.violations.base import Violation


@dataclass
class DEP102WorkspaceLeakedDependencyViolation(Violation):
    error_code: ClassVar[str] = "DEP102"
    error_template: ClassVar[str] = (
        "'{name}' imported but it is only available because another workspace member declares it as a dependency"
    )

    def get_error_message(self) -> str:
        return self.error_template.format(name=self.issue.name)
