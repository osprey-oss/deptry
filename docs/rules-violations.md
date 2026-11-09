---
icon: lucide/shield
---
# Rules and Violations

_deptry_ checks your project against the following rules related to dependencies:

| Code   | Description                        | More information                                    |
|--------|------------------------------------| ----------------------------------------------------|
| DEP001 | Project should not contain missing dependencies               | [link](#missing-dependencies-dep001)                |
| DEP002 | Project should not contain unused dependencies               | [link](#unused-dependencies-dep002)                 |
| DEP003 | Project should not use transitive dependencies            | [link](#transitive-dependencies-dep003)             |
| DEP004 | Project should not use development dependencies in non-development code | [link](#misplaced-development-dependencies-dep004)  |
| DEP005 | Project should not contain dependencies that are in the standard library    | [link](#standard-library-dependencies-dep005)       |

When a [uv workspace](uv-workspaces.md) is detected, the following additional rules are applied:

| Code   | Description                        | More information                                    |
|--------|------------------------------------| ----------------------------------------------------|
| DEP101 | Workspace member should declare sibling dependencies it imports | [link](#missing-workspace-dependency-dep101)        |
| DEP102 | Workspace member should not rely on dependencies declared by siblings | [link](#workspace-leaked-dependency-dep102)         |

Any of the checks can be disabled with the [`ignore`](configuration.md#ignore) flag. Specific dependencies or modules
can be ignored with the [`per-rule-ignores`](configuration.md#per-rule-ignores) flag. Individual import lines can also
be excluded using [inline ignore comments](usage.md#inline-ignore-comments).

## Missing dependencies (DEP001)

Python modules that are imported within a project, for which no corresponding packages are found in the dependencies.

### Example

On a project with the following dependencies:

```toml
[project]
dependencies = []
```

and the following `main.py` that is the only Python file in the project:

```python
import httpx

def make_http_request():
    return httpx.get("https://example.com")
```

_deptry_ will report `httpx` as a missing dependency because it is imported in the project, but not defined in the dependencies.

To fix the issue, `httpx` should be added to `[project.dependencies]`:

```toml
[project]
dependencies = ["httpx==0.23.1"]
```

## Unused dependencies (DEP002)

Dependencies that are required in a project, but are not used within the codebase.

!!! note

    Development dependencies are not considered for this rule, as they are usually meant to only be used outside the codebase (for instance in tests, or as CLI tools for type-checking, formatting, etc.).

### Example

On a project with the following dependencies:

```toml
[project]
dependencies = [
    "httpx==0.23.1",
    "requests==2.28.1",
]
```

and the following `main.py` that is the only Python file in the project:

```python
import httpx
import requests

def make_http_request():
    return httpx.get("https://example.com")
```

_deptry_ will report `requests` as an unused dependency because it is not used in the project.

To fix the issue, `requests` should be removed from `[project.dependencies]`:

```toml
[project]
dependencies = ["httpx==0.23.1"]
```

## Transitive dependencies (DEP003)

Python modules that are imported within a project, where the corresponding dependencies are in the dependency tree, but not as direct dependencies.
For example, assume your project has a `.py` file that imports module A. However, A is not in your project's dependencies. Instead, another package (B) is in your list of dependencies, which in turn depends on A. Package A should be explicitly added to your project's list of dependencies.

### Example

On a project with the following dependencies:

```toml
[project]
dependencies = [
    # Here `httpx` depends on `certifi` package.
    "httpx==0.23.1",
]
```

and the following `main.py` that is the only Python file in the project:

```python
import certifi
import httpx

def make_http_request():
    return httpx.get("https://example.com")

def get_certificates_location():
    return certifi.where()
```

_deptry_ will report `certifi` as a transitive dependency because it is used in the project, but not defined as a direct dependency, and is only present in the dependency tree because another dependency depends on it.

To fix the issue, `certifi` should be explicitly added to `[project.dependencies]`:

```toml
[project]
dependencies = [
    "certifi==2024.7.4",
    "httpx==0.23.1",
]
```

## Misplaced development dependencies (DEP004)

Dependencies specified as development ones that should be included as regular dependencies.

### Example

On a project with the following dependencies:

```toml
[project]
dependencies = ["httpx==0.23.1"]

[tool.pdm.dev-dependencies]
test = [
    "orjson==3.8.3",
    "pytest==7.2.0",
]
```

And the following `main.py` that is the only Python file in the project:

```python
import httpx
import orjson

def make_http_request():
    return httpx.get("https://example.com")

def dump_json():
    return orjson.dumps({"foo": "bar"})
```

_deptry_ will report `orjson` as a misplaced development dependency because it is used in non-development code.

To fix the issue, `orjson` should be moved from `[tool.pdm.dev-dependencies]` to `[project.dependencies]`:


```toml
[project]
dependencies = [
    "httpx==0.23.1",
    "orjson==3.8.3",
]

[tool.pdm.dev-dependencies]
test = ["pytest==7.2.0"]
```

## Standard library dependencies (DEP005)

Dependencies that are part of the Python standard library should not be defined as dependencies in your project.

### Example

On a project with the following dependencies:

```toml
[project]
dependencies = [
    "asyncio",
]
```

and the following `main.py` in the project:

```python
import asyncio

def async_example():
    return asyncio.run(some_coroutine())
```

_deptry_ will report `asyncio` as a standard library dependency because it is part of the standard library, yet it is defined as a dependency in the project.

To fix the issue, `asyncio` should be removed from `[project.dependencies]`:

```toml
[project]
dependencies = []
```

## uv Workspace rules

The following rules only apply when _deptry_ detects a [uv workspace](uv-workspaces.md). They catch dependency issues
that are specific to multi-package workspaces.

### Missing workspace dependency (DEP101)

A module provided by a sibling workspace member is imported, but that sibling is not declared as a dependency of the
importing package.

#### Example

Consider a uv workspace with two members, `bar` (which exposes the `bar2` module) and `baz`:

```toml title="packages/baz/pyproject.toml"
[project]
name = "baz"
dependencies = []
```

and the following `__init__.py` in `baz`:

```python
import bar2
```

_deptry_ will report `bar2` as a missing workspace dependency (DEP101), because `baz` imports a module from sibling
package `bar` without declaring it as a dependency.

To fix the issue, `bar` should be added to `baz`'s dependencies with a workspace source:

```toml title="packages/baz/pyproject.toml"
[project]
name = "baz"
dependencies = ["bar"]

[tool.uv.sources]
bar = { workspace = true }
```

### Workspace leaked dependency (DEP102)

A third-party package is imported by a workspace member that does not declare it as a dependency. The package is only
available because another workspace member declares it, and it is installed in the shared workspace environment.

This differs from [transitive dependencies (DEP003)](#transitive-dependencies-dep003), where the imported package is a
dependency of one of the member's own dependencies.

#### Example

Consider a uv workspace with two members, `bar` (which declares `pandas` as a dependency) and `foo`:

```toml title="packages/foo/pyproject.toml"
[project]
name = "foo"
dependencies = []
```

and the following `__init__.py` in `foo`:

```python
import pandas
```

_deptry_ will report `pandas` as a workspace leaked dependency (DEP102), because `foo` imports it without declaring it.
`pandas` is only available because `bar` declares it.

To fix the issue, `pandas` should be added to `foo`'s dependencies:

```toml title="packages/foo/pyproject.toml"
[project]
name = "foo"
dependencies = ["pandas"]
```
