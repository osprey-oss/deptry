from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from deptry.reporters.base import Reporter

if TYPE_CHECKING:
    from deptry.violations import Violation


@dataclass
class GithubReporter(Reporter):
    warning_ids: tuple[str, ...] = field(default_factory=tuple)  # tuple of error codes to print as warnings

    def report(self) -> None:
        self._log_and_exit()

    def _log_and_exit(self) -> None:
        self._log_violations(self.violations)

    def _log_violations(self, violations: list[Violation]) -> None:
        for violation in violations:
            self._print_github_annotation(violation)

    def _print_github_annotation(self, violation: Violation) -> None:
        annotation_severity = "warning" if violation.error_code in self.warning_ids else "error"

        ret = _build_workflow_command(
            annotation_severity,
            violation.error_code,
            violation.get_error_message(),
            self._format_path(violation.location.file),
            # For dependency files (like "pyproject.toml"), we don't extract a line. Setting the first line in that case
            # allows a comment to be added in GitHub, even if it's not on the proper line, otherwise it doesn't appear
            # at all.
            line=violation.location.line or 1,
            column=violation.location.column,
        )

        logging.info(ret)


def _build_workflow_command(
    command_name: str,
    title: str,
    message: str,
    file: str,
    line: int,
    end_line: int | None = None,
    column: int | None = None,
    end_column: int | None = None,
) -> str:
    """Build a command to annotate a workflow."""
    result = f"::{command_name} "

    entries = [
        ("file", file),
        ("line", line),
        ("endLine", end_line),
        ("col", column),
        ("endColumn", end_column),
        ("title", title),
    ]

    result += ",".join(
        f"{k}={_escape_property(v) if isinstance(v, str) else v}" for k, v in entries if v is not None
    )

    return f"{result}::{_escape(message)}"


def _escape(s: str) -> str:
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(s: str) -> str:
    return _escape(s).replace(":", "%3A").replace(",", "%2C")
