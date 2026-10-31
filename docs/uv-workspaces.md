---
icon: lucide/folder-tree
---
# uv Workspaces

_deptry_ has built-in support for [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/). When a workspace is
detected, _deptry_ analyses each member separately, against its own declared dependencies, and applies two additional
rules that catch issues specific to multi-package projects.

Workspaces of other tools are not supported.

## Detection

_deptry_ auto-detects uv workspaces by looking for a `[tool.uv.workspace]` section in the root `pyproject.toml`. No
extra CLI flag is needed.

## How it works

When a uv workspace is detected, _deptry_:

1. **Scans the root**, if it is a project itself, using the paths provided on the CLI (e.g. `deptry .` or
   `deptry src`).
2. **Discovers the workspace members**: the directories matched by the `members` globs of `[tool.uv.workspace]` that
   contain a `pyproject.toml`, minus the ones matched by the `exclude` globs.
3. **Scans each member separately**, against the dependencies declared in that member's own `pyproject.toml`.
4. **Discovers the top-level modules of each member** from its source tree (the member directory, and its `src`
   directory if there is one), so that imports of a member's own modules and of sibling members can be recognised.

This means a single `deptry .` invocation checks every package in the workspace.

A member can import its own modules without declaring anything, including when the name of a module differs from the
name of the package.

The [standard rules](rules-violations.md) (DEP001 to DEP005) apply to each member as usual. For instance, a member that
declares a sibling member as a dependency (with a `workspace = true` source) and imports it is fine, while a member that
declares a sibling without importing it gets an
[unused dependency (DEP002)](rules-violations.md#unused-dependencies-dep002) violation.

## Prerequisites

As for any project, _deptry_ needs the dependencies to be installed in the environment it runs in. For a workspace, this
means the environment must be synced with all members installed:

```shell
uv sync --all-packages
```

before invoking _deptry_.

## Running deptry

From the workspace root, run:

```shell
uv run deptry .
```

If the root package uses a `src` layout, pass that directory instead:

```shell
uv run deptry src
```

## Configuration

The `[tool.deptry]` section of the root `pyproject.toml` applies to all members. Each member can also have its own
`[tool.deptry]` section in its `pyproject.toml`, whose settings override the ones from the root for that member:

```toml title="packages/foo/pyproject.toml"
[tool.deptry]
ignore = ["DEP002"]
```

The following options can be set for a member: `ignore`, `per_rule_ignores`, `exclude`, `extend_exclude`,
`ignore_notebooks`, `known_first_party`, `package_module_name_map`, `optional_dependencies_dev_groups`,
`non_dev_dependency_groups` and `experimental_namespace_package`. The other options, like the ones that configure the
output, can only be set for the whole workspace. They are ignored with a warning if a member sets them.

!!! note

    Development dependencies of the root are not shared with the members. A member must declare every package it
    imports itself, including the ones that are only used for development.

## Workspace-specific rules

In addition to the [standard rules](rules-violations.md), _deptry_ applies two workspace-specific rules:

- [**DEP101** — Missing workspace dependency](rules-violations.md#missing-workspace-dependency-dep101): a module provided
  by a sibling workspace member is imported, but that sibling is not declared as a dependency.
- [**DEP102** — Workspace leaked dependency](rules-violations.md#workspace-leaked-dependency-dep102): a third-party
  package is imported without being declared as a dependency. It is only available because another workspace member
  declares it, and it is installed in the shared environment.

These rules only apply when _deptry_ detects a uv workspace.

## Example

Consider the following workspace layout:

```
my-workspace/
├── pyproject.toml          # workspace root; depends on `foo`
├── my_workspace/
│   └── __init__.py         # imports `foo` (ok) and `pandas` (not declared)
└── packages/
    ├── bar/                # declares `pandas`; exposes module `bar2`
    ├── baz/                # declares `foo`; imports `bar2` without declaring `bar`
    └── foo/                # no dependencies; imports `pandas`
```

Root `pyproject.toml`:

```toml
[project]
name = "my-workspace"
dependencies = ["foo"]

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
foo = { workspace = true }
```

Running `deptry .` produces:

```
my_workspace/__init__.py:2:8: DEP102 'pandas' imported but it is only available because another workspace member declares it as a dependency
packages/bar/pyproject.toml: DEP002 'pandas' defined as a dependency but not used in the codebase
packages/baz/baz/__init__.py:2:1: DEP101 'bar2' imported but it is a uv workspace sibling not declared as a dependency
packages/foo/foo/__init__.py:1:8: DEP102 'pandas' imported but it is only available because another workspace member declares it as a dependency
```

## Known limitations

If a member imports a package that is only installed as a transitive dependency of a dependency of a _sibling_ member,
_deptry_ reports it as a [transitive dependency (DEP003)](rules-violations.md#transitive-dependencies-dep003) rather
than as DEP102. For instance, if `foo` imports `numpy`, and `numpy` is only installed because sibling `bar` depends on
`pandas`, `numpy` is reported as DEP003 for `foo`. The fix is the same in both cases: declare the dependency in the
member that imports it.
