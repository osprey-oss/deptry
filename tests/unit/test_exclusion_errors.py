from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("option", ["exclude", "extend-exclude"])
@pytest.mark.parametrize("from_config", [False, True])
def test_invalid_exclusion_reports_usage_error(tmp_path: Path, option: str, from_config: bool) -> None:
    config = '[project]\nname = "example"\nversion = "0.0.1"\ndependencies = []\n'
    arguments = ["."]
    if from_config:
        config += f'\n[tool.deptry]\n{option.replace("-", "_")} = ["["]\n'
    else:
        arguments += [f"--{option}", "["]
    (tmp_path / "pyproject.toml").write_text(config)
    (tmp_path / "main.py").write_text("import os\n")

    result = subprocess.run(
        [sys.executable, "-m", "deptry", *arguments],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Invalid exclusion pattern" in result.stderr
    assert "unclosed character class" in result.stderr
    assert "panicked" not in result.stderr
    assert "Traceback" not in result.stderr
