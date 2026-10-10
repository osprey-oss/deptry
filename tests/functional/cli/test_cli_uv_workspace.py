from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project
from tests.utils import get_issues_report

if TYPE_CHECKING:
    from tests.utils import UvVenvFactory, VirtualEnvironment

STANDARD_ERROR_CODES = {"DEP001", "DEP002", "DEP003", "DEP004", "DEP005"}
WORKSPACE_ERROR_CODES = {"DEP101", "DEP102"}


class ReportedViolation(NamedTuple):
    file: str
    line: int | None
    column: int | None
    module: str
    code: str

    @property
    def import_site(self) -> tuple[str, int | None, int | None, str]:
        """What is reported, regardless of the error code it is reported with."""
        return self.file, self.line, self.column, self.module


def get_violations(
    virtual_env: VirtualEnvironment, directory: Path = Path(), arguments: str = "."
) -> set[ReportedViolation]:
    """Run deptry from `directory`, and return the violations with paths relative to the current directory, so that
    runs from different directories can be compared."""
    issue_report = Path(f"{uuid.uuid4()}.json").resolve()
    virtual_env.run(
        f"deptry {arguments} --enforce-posix-paths --no-ansi -o {issue_report.as_posix()}", cwd=Path.cwd() / directory
    )

    violations = {
        ReportedViolation(
            (directory / violation["location"]["file"]).as_posix(),
            violation["location"]["line"],
            violation["location"]["column"],
            violation["module"],
            violation["error"]["code"],
        )
        for violation in get_issues_report(issue_report)
    }
    issue_report.unlink()
    return violations


@pytest.mark.xdist_group(name=Project.UV_WORKSPACE)
def test_cli_with_uv_workspace(uv_venv_factory: UvVenvFactory) -> None:
    with uv_venv_factory(Project.UV_WORKSPACE) as virtual_env:
        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Scanning 1 file...
Scanning 2 files...
Scanning 1 file...
Scanning 1 file...
Scanning 1 file...

uv_workspace/__init__.py:2:8: DEP102 'pandas' imported but it is only available because another workspace member declares it as a dependency
packages/bar/pyproject.toml: DEP002 'pandas' defined as a dependency but not used in the codebase
packages/baz/baz/__init__.py:2:1: DEP101 'bar2' imported but it is a uv workspace sibling not declared as a dependency
packages/foo/foo/__init__.py:1:8: DEP102 'pandas' imported but it is only available because another workspace member declares it as a dependency
packages/qux/pyproject.toml: DEP002 'foo' defined as a dependency but not used in the codebase
packages/qux/qux/__init__.py:1:8: DEP001 'missing_package' imported but missing from the dependency definitions
packages/qux/qux/__init__.py:2:8: DEP003 'numpy' imported but it is a transitive dependency
Found 7 dependency issues.

For more information, see the documentation: https://deptry.com/
""")


@pytest.mark.xdist_group(name=Project.UV_WORKSPACE)
def test_cli_with_uv_workspace_is_equivalent_to_running_from_each_member(uv_venv_factory: UvVenvFactory) -> None:
    """
    Running deptry from the workspace root must report, for each member, exactly what running deptry from the
    directory of that member reports for DEP001 to DEP005, apart from the imports that only work thanks to the
    workspace: those are reported as DEP101 or DEP102 from the root, instead of whatever a member-local run makes of
    a module that is installed in the shared environment without being declared.

    The workspace root is not compared: running deptry from its directory is the workspace run itself.
    """
    # The arguments are the ones needed to correctly run deptry on each member in isolation. A member-local run has no
    # way to know about what the workspace run finds out by itself:
    # - `bar` uses a `src` layout, so `src` has to be the directory to scan for its own modules to be found;
    # - `qux` depends on its sibling `bar`, whose only module is `bar2`. Workspace members are installed as editable
    #   packages, for which the modules cannot be read from the metadata, so the mapping has to be given.
    # Without those arguments, the member-local runs report false positives for `bar2` that the workspace run does not.
    arguments_per_member = {
        Path("packages/bar"): "src",
        Path("packages/baz"): ".",
        Path("packages/foo"): ".",
        Path("packages/qux"): ". --package-module-name-map bar=bar2",
    }

    with uv_venv_factory(Project.UV_WORKSPACE) as virtual_env:
        all_workspace_violations = get_violations(virtual_env)
        member_violations = {
            violation
            for member, arguments in arguments_per_member.items()
            for violation in get_violations(virtual_env, member, arguments)
        }

    workspace_violations = {
        violation
        for violation in all_workspace_violations
        if any(Path(violation.file).is_relative_to(member) for member in arguments_per_member)
    }
    assert {violation.code for violation in workspace_violations} == snapshot({
        "DEP001",
        "DEP002",
        "DEP003",
        "DEP101",
        "DEP102",
    })

    # Every import reported as DEP101 or DEP102 from the root is also reported by the member-local run, that can only
    # tell that the module is not provided by a declared dependency.
    workspace_only_import_sites = {
        violation.import_site for violation in workspace_violations if violation.code in WORKSPACE_ERROR_CODES
    }
    reclassified_member_violations = {
        violation for violation in member_violations if violation.import_site in workspace_only_import_sites
    }
    assert {violation.import_site for violation in reclassified_member_violations} == workspace_only_import_sites
    assert {violation.code for violation in reclassified_member_violations} == snapshot({"DEP003"})

    # Everything else is strictly identical.
    assert {violation.code for violation in member_violations} <= STANDARD_ERROR_CODES
    assert member_violations - reclassified_member_violations == {
        violation for violation in workspace_violations if violation.code in STANDARD_ERROR_CODES
    }


@pytest.mark.xdist_group(name=Project.UV_WORKSPACE_ISSUE_1060)
def test_cli_with_uv_workspace_issue_1060(uv_venv_factory: UvVenvFactory) -> None:
    """Scenario of https://github.com/osprey-oss/deptry/issues/1060, where `first` imports `a`, that it does not
    declare, `click` (`b` in the issue), that it declares, its sibling `second`, that it declares, and itself."""
    with uv_venv_factory(Project.UV_WORKSPACE_ISSUE_1060) as virtual_env:
        result = virtual_env.run_deptry(".")
        violations = get_violations(virtual_env)

    assert result.returncode == 1
    assert result.stderr == snapshot("""\
Scanning 0 file...
Scanning 2 files...
Scanning 1 file...

packages/first/src/first/main.py:1:8: DEP001 'a' imported but missing from the dependency definitions
Found 1 dependency issue.

For more information, see the documentation: https://deptry.com/
""")

    reported_modules = {violation.module for violation in violations}
    # The missing dependency of `first` is reported when running from the workspace root.
    assert ReportedViolation("packages/first/src/first/main.py", 1, 8, "a", "DEP001") in violations
    # `first` importing itself is not reported.
    assert "first" not in reported_modules
    # `second` is a sibling that `first` declares and uses, and the declared `click` is used too.
    assert "second" not in reported_modules
    assert "click" not in reported_modules


@pytest.mark.xdist_group(name=Project.UV_WORKSPACE_MEMBER_DISCOVERY)
def test_cli_with_uv_workspace_member_discovery(uv_venv_factory: UvVenvFactory) -> None:
    """The workspace has a virtual root (no `[project]` section), and members defined with
    `members = ["packages/*", "libs/*/*"]` and `exclude = ["packages/excl*"]`, where `packages/*` also matches a file,
    and a directory without `pyproject.toml`."""
    with uv_venv_factory(Project.UV_WORKSPACE_MEMBER_DISCOVERY) as virtual_env:
        # uv only accepts a directory without `pyproject.toml` under a `members` glob if all the files it contains are
        # ignored by git (leftovers of a removed member, for instance), which cannot be committed in a fixture. So it
        # is created once the environment is set up.
        not_a_member = Path("packages/not_a_member")
        not_a_member.mkdir(exist_ok=True)
        (not_a_member / "script.py").write_text("import missing_in_not_a_member\n")

        result = virtual_env.run_deptry(".")
        violations = get_violations(virtual_env)

    assert result.returncode == 1
    # Only `packages/alpha` and the nested `libs/group/nested` are scanned.
    assert result.stderr == snapshot("""\
Scanning 1 file...
Scanning 1 file...

packages/alpha/alpha/__init__.py:2:8: DEP101 'nested' imported but it is a uv workspace sibling not declared as a dependency
libs/group/nested/src/nested/__init__.py:1:8: DEP102 'click' imported but it is only available because another workspace member declares it as a dependency
libs/group/nested/src/nested/__init__.py:2:8: DEP001 'missing_in_nested' imported but missing from the dependency definitions
Found 3 dependency issues.

For more information, see the documentation: https://deptry.com/
""")
    assert {violation.file for violation in violations} == {
        "packages/alpha/alpha/__init__.py",
        "libs/group/nested/src/nested/__init__.py",
    }
    # In particular, nothing is reported for `missing_in_excluded` and `missing_in_not_a_member`.
    assert {violation.module for violation in violations} == {"nested", "click", "missing_in_nested"}
