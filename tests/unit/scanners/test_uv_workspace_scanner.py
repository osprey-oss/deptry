from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from deptry.config import Config
from deptry.dependency import Dependency
from deptry.dependency_getter.base import DependenciesExtract
from deptry.python_file_finder import get_all_python_files_in
from deptry.scanners.uv_workspace import UvWorkspaceConfig, UvWorkspaceScanner, get_uv_workspace_config
from tests.utils import create_files, run_within_dir

DEFAULT_EXCLUDE = ("venv", r"\.venv", r"\.direnv", "tests", r"\.git", r"setup\.py")


def _make_config(**overrides: Any) -> Config:
    defaults: dict[str, Any] = {
        "root": (Path(),),
        "config": Path("pyproject.toml"),
        "no_ansi": False,
        "per_rule_ignores": {},
        "ignore": (),
        "exclude": DEFAULT_EXCLUDE,
        "extend_exclude": (),
        "using_default_exclude": True,
        "ignore_notebooks": False,
        "requirements_files": (),
        "requirements_files_dev": (),
        "known_first_party": (),
        "json_output": "",
        "package_module_name_map": {},
        "optional_dependencies_dev_groups": (),
        "non_dev_dependency_groups": (),
        "using_default_requirements_files": True,
        "experimental_namespace_package": False,
        "github_output": False,
        "github_warning_errors": (),
        "enforce_posix_paths": False,
    }
    defaults.update(overrides)
    return Config(**defaults)


def _write_files(files: dict[str, str]) -> None:
    for path, content in files.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")


def _pyproject(name: str, dependencies: tuple[str, ...] = (), extra: str = "") -> str:
    return f'[project]\nname = "{name}"\ndependencies = [{", ".join(repr(dep) for dep in dependencies)}]\n{extra}'


WORKSPACE = '[tool.uv.workspace]\nmembers = ["packages/*"]\n'


def _scan(**config_overrides: Any) -> list[tuple[str, str, str]]:
    """Scan the uv workspace of the current directory like the CLI would, and return the violations found as
    (error code, name of the module or dependency, file) tuples."""
    config = _make_config(**config_overrides)
    uv_workspace_config = get_uv_workspace_config(config.config)
    assert uv_workspace_config is not None

    return [
        (violation.error_code, violation.issue.name, violation.location.file.as_posix())
        for violation in UvWorkspaceScanner(config, uv_workspace_config).scan()
    ]


# ---------------------------------------------------------------------------
# get_uv_workspace_config
# ---------------------------------------------------------------------------


def test_get_uv_workspace_config_without_pyproject_toml(tmp_path: Path) -> None:
    assert get_uv_workspace_config(tmp_path / "pyproject.toml") is None


def test_get_uv_workspace_config_without_workspace(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_pyproject("foo"), encoding="utf-8")

    assert get_uv_workspace_config(tmp_path / "pyproject.toml") is None


def test_get_uv_workspace_config_only_keeps_directories_with_pyproject_toml(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": '[tool.uv.workspace]\nmembers = ["packages/*", "packages/foo", "libs/nested/*"]\n',
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/bar/pyproject.toml": _pyproject("bar"),
            # Neither a stray file nor a directory without `pyproject.toml` are members.
            "packages/README.md": "",
            "packages/not_a_member/module.py": "",
            "libs/nested/baz/pyproject.toml": _pyproject("baz"),
        })

        assert get_uv_workspace_config(Path("pyproject.toml")) == UvWorkspaceConfig(
            members=(Path("packages/bar"), Path("packages/foo"), Path("libs/nested/baz"))
        )


def test_get_uv_workspace_config_exclude(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": '[tool.uv.workspace]\nmembers = ["packages/*"]\nexclude = ["packages/ba*"]\n',
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/bar/pyproject.toml": _pyproject("bar"),
            "packages/baz/pyproject.toml": _pyproject("baz"),
        })

        assert get_uv_workspace_config(Path("pyproject.toml")) == UvWorkspaceConfig(members=(Path("packages/foo"),))


def test_get_uv_workspace_config_absolute_config(tmp_path: Path) -> None:
    _write_files({
        str(tmp_path / "pyproject.toml"): WORKSPACE,
        str(tmp_path / "packages/foo/pyproject.toml"): _pyproject("foo"),
    })

    assert get_uv_workspace_config(tmp_path / "pyproject.toml") == UvWorkspaceConfig(
        members=(tmp_path / "packages/foo",)
    )


# ---------------------------------------------------------------------------
# _get_member_modules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("files", "experimental_namespace_package", "expected"),
    [
        # Flat layout, with a package, a single-file module and a directory without `__init__.py`.
        (
            ["foo/__init__.py", "script.py", "no_init/module.py", "__init__.py"],
            False,
            {"foo", "script", "no_init"},
        ),
        # `src` layout, where `src` itself is not a module.
        (
            ["src/foo2/__init__.py", "src/single.py", "src/__init__.py"],
            False,
            {"foo2", "single"},
        ),
        # Both layouts at once.
        (
            ["src/foo/__init__.py", "tests/test_foo.py"],
            False,
            {"foo", "tests"},
        ),
        # Directories without Python files, and paths that cannot be imported, are not modules.
        (
            ["docs/index.md", ".hidden/module.py", "not-importable/module.py", "namespace/foo/module.py"],
            False,
            set(),
        ),
        # With namespace packages, Python files are also searched in subdirectories, but `src` is still not a module.
        (
            ["docs/index.md", ".hidden/module.py", "namespace/foo/module.py", "src/other/foo/module.py"],
            True,
            {"namespace", "other"},
        ),
        (
            [],
            False,
            set(),
        ),
    ],
)
def test__get_member_modules(
    tmp_path: Path, files: list[str], experimental_namespace_package: bool, expected: set[str]
) -> None:
    with run_within_dir(tmp_path):
        create_files([Path("packages/foo") / file for file in files])
        Path("packages/foo").mkdir(parents=True, exist_ok=True)

        assert (
            UvWorkspaceScanner._get_member_modules(
                Path("packages/foo"), (Path(), Path("packages/foo")), experimental_namespace_package
            )
            == expected
        )


@pytest.mark.parametrize("experimental_namespace_package", [True, False])
def test__get_member_modules_skips_directories_of_other_members(
    tmp_path: Path, experimental_namespace_package: bool
) -> None:
    with run_within_dir(tmp_path):
        create_files([
            Path("root_module/__init__.py"),
            # Without the member it holds, those directories would be modules.
            Path("packages/conftest.py"),
            Path("packages/foo/foo/__init__.py"),
            Path("bar/conftest.py"),
            Path("bar/bar/__init__.py"),
        ])
        members = (Path(), Path("packages/foo"), Path("bar"))

        assert UvWorkspaceScanner._get_member_modules(Path(), members, experimental_namespace_package) == {
            "root_module"
        }
        assert UvWorkspaceScanner._get_member_modules(Path("bar"), members, experimental_namespace_package) == {
            "bar",
            "conftest",
        }


# ---------------------------------------------------------------------------
# _get_sibling_context
# ---------------------------------------------------------------------------


def test__get_sibling_context() -> None:
    foo, bar, baz = Path("packages/foo"), Path("packages/bar"), Path("packages/baz")
    member_modules = {
        foo: frozenset({"foo", "tests"}),
        bar: frozenset({"bar2", "tests"}),
        baz: frozenset({"baz"}),
    }
    dependency_extracts = {
        foo: DependenciesExtract([], [Dependency("pytest", foo / "pyproject.toml", module_names=("pytest",))]),
        bar: DependenciesExtract([Dependency("PyYAML", bar / "pyproject.toml", module_names=("yaml",))], []),
        baz: DependenciesExtract([Dependency("foo", baz / "pyproject.toml", module_names=("foo",))], []),
    }

    # A module that the member has itself (here, `tests`) is not a sibling module. Names of dependencies are
    # canonicalized, and the modules they provide are returned too.
    assert UvWorkspaceScanner._get_sibling_context(foo, member_modules, dependency_extracts) == (
        frozenset({"bar2", "baz"}),
        frozenset({"pyyaml", "foo"}),
        frozenset({"yaml", "foo"}),
    )
    assert UvWorkspaceScanner._get_sibling_context(baz, member_modules, dependency_extracts) == (
        frozenset({"foo", "bar2", "tests"}),
        frozenset({"pytest", "pyyaml"}),
        frozenset({"pytest", "yaml"}),
    )


def test__get_sibling_context_no_siblings() -> None:
    only = Path("packages/only")

    assert UvWorkspaceScanner._get_sibling_context(
        only,
        {only: frozenset({"only"})},
        {only: DependenciesExtract([Dependency("requests", only / "pyproject.toml", module_names=("requests",))], [])},
    ) == (frozenset(), frozenset(), frozenset())


# ---------------------------------------------------------------------------
# _build_member_base_config
# ---------------------------------------------------------------------------


def test__build_member_base_config_applies_member_deptry_overrides(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "packages/foo/pyproject.toml": '[tool.deptry]\nignore = ["DEP001"]\nextend_exclude = ["generated"]\n',
        })
        member = Path("packages/foo")
        scanner = UvWorkspaceScanner(
            _make_config(ignore=("DEP002",), exclude=("tests",)), UvWorkspaceConfig(members=(member,))
        )

        config = scanner._build_member_base_config(member, (Path(), member))

        assert config.root == (member,)
        assert config.config == member / "pyproject.toml"
        assert list(config.ignore) == ["DEP001"]
        # Patterns also apply from the member directory, like when running deptry from there.
        assert config.exclude == ("tests", "packages/foo/(?:tests)")
        assert config.extend_exclude == ("generated", "packages/foo/(?:generated)")


def test__build_member_base_config_no_deptry_section(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({"packages/bar/pyproject.toml": _pyproject("bar")})
        member = Path("packages/bar")
        scanner = UvWorkspaceScanner(_make_config(ignore=("DEP002",)), UvWorkspaceConfig(members=(member,)))

        config = scanner._build_member_base_config(member, (Path(), member))

        # No [tool.deptry] in member, so base config values are preserved
        assert config.ignore == ("DEP002",)
        assert config.root == (member,)


def test__build_member_base_config_excludes_other_members(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/foo/plugins/bar/pyproject.toml": _pyproject("bar"),
        })
        foo, bar = Path("packages/foo"), Path("packages/foo/plugins/bar")
        members = (Path(), foo, bar)
        base_config = _make_config(exclude=(), extend_exclude=("generated",))
        scanner = UvWorkspaceScanner(base_config, UvWorkspaceConfig(members=(foo, bar)))

        assert scanner._build_member_base_config(Path(), members) == base_config.with_overrides({
            "extend_exclude": ("generated", "packages/foo(/|$)", "packages/foo/plugins/bar(/|$)")
        })
        # A member nested in another one is excluded from it too.
        assert scanner._build_member_base_config(foo, members).extend_exclude == (
            "generated",
            "packages/foo/(?:generated)",
            "packages/foo/plugins/bar(/|$)",
        )
        assert scanner._build_member_base_config(bar, members).extend_exclude == (
            "generated",
            "packages/foo/plugins/bar/(?:generated)",
        )


# ---------------------------------------------------------------------------
# _get_member_exclude_patterns
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("absolute_root", [False, True])
def test__get_member_exclude_patterns_match_whole_path_segments(tmp_path: Path, absolute_root: bool) -> None:
    with run_within_dir(tmp_path):
        create_files([
            Path("root_module/__init__.py"),
            Path("packages/foo/foo/__init__.py"),
            Path("packages/foobar/foobar/__init__.py"),
            Path("packages/foo.py"),
            Path("packages/with space-and.dot/module.py"),
            Path("other/packages/foo/module.py"),
        ])
        root = tmp_path if absolute_root else Path()

        patterns = UvWorkspaceScanner._get_member_exclude_patterns(
            (root,), (Path("packages/foo"), Path("packages/with space-and.dot"))
        )

        # Only the members are excluded, and not the paths that merely start or end like them.
        assert sorted(get_all_python_files_in((root,), (), patterns, using_default_exclude=False)) == [
            root / "other/packages/foo/module.py",
            root / "packages/foo.py",
            root / "packages/foobar/foobar/__init__.py",
            root / "root_module/__init__.py",
        ]


def test__get_member_exclude_patterns_several_roots(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        create_files([Path("src/foo/pyproject.toml"), Path("packages/bar/pyproject.toml"), Path("scripts/run.py")])

        # Patterns are built for each root that contains the member, and absolute members are supported.
        assert UvWorkspaceScanner._get_member_exclude_patterns(
            (Path("src"), Path("scripts"), Path()), (Path("src/foo"), tmp_path / "packages/bar")
        ) == ("src/foo(/|$)", "src/foo(/|$)", "packages/bar(/|$)")


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------


def test_scan_self_imports(tmp_path: Path) -> None:
    """A member can import its own modules, whatever its layout and even if they are not named after the package."""
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": _pyproject("root", extra=WORKSPACE),
            "src/root_module/__init__.py": "import root_module",
            "packages/flat/pyproject.toml": _pyproject("flat"),
            "packages/flat/flat/__init__.py": "import flat\nimport helpers",
            "packages/flat/helpers.py": "",
            "packages/src-layout/pyproject.toml": _pyproject("src-layout"),
            "packages/src-layout/src/other_name/__init__.py": "from other_name import foo",
            "packages/src-layout/src/other_name/foo.py": "",
        })

        assert _scan() == []


def test_scan_declared_sibling_with_module_named_differently(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": WORKSPACE,
            "packages/foo/pyproject.toml": _pyproject("foo", ("bar",)),
            "packages/foo/foo/__init__.py": "import bar2",
            "packages/bar/pyproject.toml": _pyproject("bar"),
            "packages/bar/src/bar2/__init__.py": "",
            # `baz` declares the sibling but does not use it, and uses the other one without declaring it.
            "packages/baz/pyproject.toml": _pyproject("baz", ("foo",)),
            "packages/baz/baz/__init__.py": "import bar2",
        })

        violations = _scan()

        assert ("DEP002", "foo", "packages/baz/pyproject.toml") in violations
        assert ("DEP101", "bar2", "packages/baz/baz/__init__.py") in violations
        assert {file for _, _, file in violations} == {"packages/baz/pyproject.toml", "packages/baz/baz/__init__.py"}


@pytest.mark.parametrize(
    ("sibling_name", "declared_as"),
    [
        ("my_pkg", "my-pkg"),
        ("my-pkg", "my_pkg"),
        ("My.Pkg", "my-pkg"),
    ],
)
def test_scan_declared_sibling_with_name_written_differently(
    tmp_path: Path, sibling_name: str, declared_as: str
) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": WORKSPACE,
            "packages/foo/pyproject.toml": _pyproject("foo", (declared_as,)),
            "packages/foo/foo/__init__.py": "import core",
            "packages/bar/pyproject.toml": _pyproject(sibling_name),
            "packages/bar/src/core/__init__.py": "",
        })

        assert _scan() == []


def test_scan_user_package_module_name_map_wins_over_sibling_modules(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": WORKSPACE,
            "packages/foo/pyproject.toml": _pyproject("foo", ("bar",)),
            "packages/foo/foo/__init__.py": "import configured",
            "packages/bar/pyproject.toml": _pyproject("bar"),
            "packages/bar/bar/__init__.py": "",
        })

        assert _scan(package_module_name_map={"bar": ("configured",)}) == []


def test_scan_members_with_modules_of_the_same_name(tmp_path: Path) -> None:
    """A module that a member has itself is local, even if a sibling has a module of the same name."""
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": WORKSPACE,
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/foo/src/foo/__init__.py": "",
            "packages/foo/testing/__init__.py": "",
            "packages/foo/testing/test_foo.py": "import foo\nfrom testing import utils",
            "packages/bar/pyproject.toml": _pyproject("bar"),
            "packages/bar/src/bar/__init__.py": "",
            "packages/bar/testing/__init__.py": "",
            "packages/bar/testing/test_bar.py": "import bar\nfrom testing import utils",
        })

        assert _scan() == []


def test_scan_does_not_share_root_dev_dependencies_with_members(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": _pyproject(
                "root", extra=f'{WORKSPACE}\n[dependency-groups]\ndev = ["deptry-test-root-dev-dependency"]\n'
            ),
            "root_module.py": "import deptry_test_root_dev_dependency",
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/foo/foo/__init__.py": "import deptry_test_root_dev_dependency",
        })

        assert _scan() == [
            ("DEP004", "deptry_test_root_dev_dependency", "root_module.py"),
            ("DEP001", "deptry_test_root_dev_dependency", "packages/foo/foo/__init__.py"),
        ]


@pytest.mark.parametrize("absolute_root", [False, True])
def test_scan_scans_files_of_members_once(tmp_path: Path, absolute_root: bool) -> None:
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": _pyproject("root", extra=WORKSPACE),
            "root_module.py": "import deptry_test_missing",
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/foo/foo/__init__.py": "import deptry_test_missing",
            "packages/foobar/not_in_a_member.py": "import deptry_test_missing",
        })
        root = tmp_path if absolute_root else Path()

        assert sorted(_scan(root=(root,))) == sorted([
            ("DEP001", "deptry_test_missing", (root / "packages/foobar/not_in_a_member.py").as_posix()),
            ("DEP001", "deptry_test_missing", (root / "root_module.py").as_posix()),
            ("DEP001", "deptry_test_missing", "packages/foo/foo/__init__.py"),
        ])


def test_scan_applies_exclude_from_member_directory(tmp_path: Path) -> None:
    """Like when running deptry from the member directory, `tests` is excluded by default."""
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": WORKSPACE,
            "packages/foo/pyproject.toml": _pyproject("foo", extra='[tool.deptry]\nextend_exclude = ["generated"]\n'),
            "packages/foo/foo/__init__.py": "",
            "packages/foo/tests/test_foo.py": "import deptry_test_missing",
            "packages/foo/generated/module.py": "import deptry_test_missing",
        })

        assert _scan() == []


def test_scan_virtual_workspace_root(tmp_path: Path) -> None:
    """A workspace root without `[project]` section is not a project, so only its members are scanned."""
    with run_within_dir(tmp_path):
        _write_files({
            "pyproject.toml": WORKSPACE,
            "script.py": "import deptry_test_missing",
            "packages/foo/pyproject.toml": _pyproject("foo"),
            "packages/foo/foo/__init__.py": "import deptry_test_missing",
        })

        assert _scan() == [("DEP001", "deptry_test_missing", "packages/foo/foo/__init__.py")]
