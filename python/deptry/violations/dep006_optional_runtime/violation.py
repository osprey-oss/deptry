from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from deptry.violations.base import Violation


@dataclass
class DEP006OptionalDependencyPlacementViolation(Violation):
    error_code: ClassVar[str] = "DEP006"
    error_template: ClassVar[str] = "'{name}' imported outside optional extra '{group}'"
    group: str = ""

    def get_error_message(self) -> str:
        return self.error_template.format(name=self.issue.name, group=self.group)
