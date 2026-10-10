# uv_workspace fixture

A uv workspace made of a root project and four members, used to test that running _deptry_ from the workspace root
checks each member against its own dependencies. It must be synced with `uv sync --all-packages`.

`uv.lock` is generated: run `uv lock` in this directory after changing a dependency or a member.

## Workspace structure

```
uv_workspace/
├── pyproject.toml          # workspace root (members = ["packages/*"]), also a project that declares `foo`
├── uv_workspace/           # root project: imports `foo` and `pandas`
└── packages/
    ├── bar/                # `src` layout, exposes module `bar2`; declares `pandas`; imports its own module `bar2`
    ├── baz/                # declares `foo`; imports `foo` and `bar2`
    ├── foo/                # no dependencies; imports `pandas`
    └── qux/                # declares `bar`, `foo` and `pandas`; imports `bar2`, `pandas`, `numpy` and `missing_package`
```

## Expected violations

| Location | Code | Reason |
|---|---|---|
| `uv_workspace/__init__.py:2:8` | DEP102 | `pandas` is only declared by the siblings `bar` and `qux` |
| `packages/bar/pyproject.toml` | DEP002 | `pandas` is declared by `bar` but never imported |
| `packages/baz/baz/__init__.py:2:1` | DEP101 | `bar2` is a module of the sibling `bar`, that `baz` does not declare |
| `packages/foo/foo/__init__.py:1:8` | DEP102 | `pandas` is only declared by the siblings `bar` and `qux` |
| `packages/qux/pyproject.toml` | DEP002 | the sibling `foo` is declared by `qux` but never imported |
| `packages/qux/qux/__init__.py:1:8` | DEP001 | `missing_package` is declared nowhere and is not installed |
| `packages/qux/qux/__init__.py:2:8` | DEP003 | `numpy` is only installed as a dependency of `pandas`, that `qux` declares |

## Expected absence of violations

| Location | Import | Reason |
|---|---|---|
| `uv_workspace/__init__.py:1` | `foo` | sibling declared by the root project |
| `packages/bar/src/bar2/__init__.py:1` | `bar2` | own module of `bar`, in a `src` layout and not named after the package |
| `packages/baz/baz/__init__.py:1` | `foo` | sibling declared by `baz` |
| `packages/qux/qux/__init__.py:3` | `pandas` | dependency declared by `qux` |
| `packages/qux/qux/__init__.py:4` | `bar2` | module of the sibling `bar`, declared by `qux`, although not named after the package |
