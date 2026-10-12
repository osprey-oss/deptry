from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import UvVenvFactory


@pytest.mark.xdist_group(name=Project.PEP_723)
def test_cli_with_pep_723(uv_venv_factory: UvVenvFactory) -> None:
    with uv_venv_factory(Project.PEP_723) as virtual_env:
        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'arrow' is 'arrow'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 2 files...

pyproject.toml: DEP002 'arrow' defined as a dependency but not used in the codebase
Found 1 dependency issue.

For more information, see the documentation: https://deptry.com/
""")
