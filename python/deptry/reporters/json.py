from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from deptry.reporters.base import Reporter

if TYPE_CHECKING:
    from typing import Any


@dataclass
class JSONReporter(Reporter):
    json_output: str

    def report(self) -> None:
        output: list[dict[str, str | dict[str, Any]]] = [
            {
                "error": {
                    "code": violation.error_code,
                    "message": violation.get_error_message(),
                },
                "module": violation.issue.name,
                "location": {
                    "file": self._format_path(violation.location.file),
                    "line": violation.location.line,
                    "column": violation.location.column,
                },
            }
            for violation in self.violations
        ]

        with Path(self.json_output).open("w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
