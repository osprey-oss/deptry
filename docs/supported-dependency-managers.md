# Supported dependency managers

While most dependency managers support the
standard [PEP 621 format](https://packaging.python.org/en/latest/specifications/pyproject-toml/) for defining
dependencies in `pyproject.toml`, not all of them do. Even those that do often provide additional ways to define
dependencies that are not standardized.

_deptry_ can extract dependencies for any dependency manager that supports standard PEP 621, while also extracting them
from locations that are specific to some dependency managers that support this standard, but provide additional ways of
defining dependencies (e.g., [uv](https://docs.astral.sh/uv/), [Poetry](https://python-poetry.org/)).

_deptry_ can also extract dependencies from dependency managers that do not support PEP 621 at
all (e.g., [pip](https://pip.pypa.io/en/stable/reference/requirements-file-format/)).

## PEP 621

_deptry_ fully supports [PEP 621 standard](https://packaging.python.org/en/latest/specifications/pyproject-toml/), and
uses the presence of a `[project]` section in `pyproject.toml` to determine that the project uses PEP 621.

By default, _deptry_ extracts, from `pyproject.toml`:

- regular dependencies from:
    - `dependencies` entry under `[project]` section
    - groups under `[project.optional-dependencies]` section
- development dependencies from groups under `[dependency-groups]` section

For instance, given this `pyproject.toml`:

```toml title="pyproject.toml"
[project]
name = "foo"
dependencies = ["orjson>=3.0.0"]

[project.optional-dependencies]
cli = ["click>=8.0.0"]
http = [
    "httpx>=0.27.0",
    "uvicorn>=0.32.0",
]

[dependency-groups]
docs = ["mkdocs==1.6.1"]
test = [
    "pytest==8.3.3",
    "pytest-cov==5.0.0",
]
```

the following dependencies will be extracted:

- regular dependencies: `orjson`, `click`, `httpx`, `uvicorn`
- development dependencies: `mkdocs`, `pytest`, `pytest-cov`

!!! note

    Groups under `[project.optional-dependencies]` can be flagged as development dependency groups by
    using [`--optional-dependencies-dev-groups`](configuration.md#optional-dependencies-dev-groups) argument (or its
    `optional_dependencies_dev_groups` equivalent in `pyproject.toml`).

### uv

If a `[tool.uv.dev-dependencies]` section is found, _deptry_ will assume that uv is used as a dependency manager, and
will, additionally to PEP 621 dependencies,
extract [uv development dependencies](https://docs.astral.sh/uv/concepts/dependencies/#development-dependencies) from
`dev-dependencies` entry under `[tool.uv]` section, for instance:

```toml title="pyproject.toml"
[tool.uv]
dev-dependencies = [
    "mkdocs==1.6.1",
    "pytest==8.3.3",
    "pytest-cov==5.0.0",
]
```

### Poetry

Until [version 2.0](https://python-poetry.org/blog/announcing-poetry-2.0.0/), Poetry did not support PEP 621 syntax to
define project dependencies, instead relying on a specific syntax.

Because Poetry now supports PEP 621, it is now treated as an extension of PEP 621 manager, allowing _deptry_ to retrieve
dependencies defined under `[project.dependencies]` and `[project.optional-dependencies]`, while still allowing
retrieving:

- regular dependencies from `[tool.poetry.dependencies]` (which is still supported in Poetry 2.0)
- development dependencies from `[tool.poetry.group.<group>.dependencies]` and `[tool.poetry.dev-dependencies]`

#### Regular dependencies

Which regular dependencies are extracted depend on how you define your dependencies with Poetry, as _deptry_ will
closely
match [Poetry's behavior](https://python-poetry.org/docs/dependency-specification/#projectdependencies-and-toolpoetrydependencies).

If `[project.dependencies]` is not set, or is empty, regular dependencies will be extracted from
`[tool.poetry.dependencies]`. For instance, in this case:

```toml title="pyproject.toml"
[project]
name = "foo"

[tool.poetry.dependencies]
httpx = "0.28.1"
```

`httpx` will be extracted as a regular dependency.

If `[project.dependencies]` contains at least one dependency, then dependencies will **NOT** be extracted from
`[tool.poetry.dependencies]`, as in that case, Poetry will only consider that data in this section enriches dependencies
already defined in `[project.dependencies]` (for instance, to set a specific source), and not defining new dependencies.

For instance, in this case:

```toml title="pyproject.toml"
[project]
name = "foo"
dependencies = ["httpx"]

[tool.poetry.dependencies]
httpx = { git = "https://github.com/encode/httpx", tag = "0.28.1" }
urllib3 = "2.3.0"
```

although `[tool.poetry.dependencies]` contains both `httpx` and `urllib3`, only `httpx` will be extracted as a regular
dependency, as `[project.dependencies]` contains at least one dependency, so Poetry itself will not consider `urllib3`
to be a dependency of the project.

#### Development dependencies

In Poetry, [development dependencies](https://python-poetry.org/docs/managing-dependencies/#dependency-groups) can be
defined under either (or both):

- `[tool.poetry.group.<group>.dependencies]` sections
- `[tool.poetry.dev-dependencies]` section (which is considered legacy)

_deptry_ will extract dependencies from all those sections, for instance:

```toml title="pyproject.toml"
[tool.poetry.dev-dependencies]
mypy = "1.14.1"
ruff = "0.8.6"

[tool.poetry.group.docs.dependencies]
mkdocs = "1.6.1"

[tool.poetry.group.test.dependencies]
pytest = "8.3.3"
pytest-cov = "5.0.0"
```

### PDM

If a `[tool.pdm.dev-dependencies]` section is found, _deptry_ will assume that PDM is used as a dependency manager, and
will, additionally to PEP 621 dependencies,
extract [PDM development dependencies](https://pdm-project.org/en/latest/usage/dependency/#add-development-only-dependencies)
from `[tool.pdm.dev-dependencies]` section, for instance:

```toml title="pyproject.toml"
[tool.pdm.dev-dependencies]
docs = ["mkdocs==1.6.1"]
test = [
    "pytest==8.3.3",
    "pytest-cov==5.0.0",
]
```

### Setuptools

When using setuptools as a build backend, both `dependencies` and `optional-dependencies` can
be [dynamically read](https://setuptools.pypa.io/en/stable/userguide/pyproject_config.html#dynamic-metadata) from
`requirements.txt`-format files, for instance:

```toml title="pyproject.toml"
[build-backend]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "foo"
dynamic = ["dependencies", "optional-dependencies"]

[tool.setuptools.dynamic]
dependencies = { file = ["requirements.txt"] }

[tool.setuptools.dynamic.optional-dependencies]
cli = { file = ["cli-requirements.txt"] }
```

In this example, regular dependencies will be extracted from both `requirements.txt` and `cli-requirements.txt` files.

!!! note

    Groups under `[tool.setuptools.dynamic.optional-dependencies]` can be flagged as development dependency groups by
    using [`--pep621-dev-dependency-groups`](configuration.md#pep-621-dev-dependency-groups) argument (or its
    `pep_621_dev_dependency_groups` equivalent in `pyproject.toml`).

## `requirements.txt` (pip, pip-tools)

_deptry_ supports extracting [dependencies using
`requirements.txt` format](https://pip.pypa.io/en/stable/reference/requirements-file-format/), which is mostly used
by [pip](https://pip.pypa.io/en/stable/) and [pip-tools](https://pip-tools.readthedocs.io/en/stable/).

By default, _deptry_ will look for:

- regular dependencies in `requirements.txt` (or `requirements.in` if existing, assuming pip-tools is used)
- development dependencies in `dev-requirements.txt` and `requirements-dev.txt`

For instance, given the following `requirements.txt` file:

```python title="requirements.txt"
click>=8.0.0
orjson>=3.0.0
```

and the following `dev-requirements.txt` file:

```python title="dev-requirements.txt"
mkdocs==1.6.1
pytest==8.3.3
pytest-cov==5.0.0
```

the following dependencies will be extracted:

- regular dependencies: `click`, `orjson`
- development dependencies: `mkdocs`, `pytest`, `pytest-cov`

If a requirements
file [references other requirements files](https://pip.pypa.io/en/stable/reference/requirements-file-format/#referring-to-other-requirements-files),
for instance with `-r other-requirements.txt`, _deptry_ will also include the dependencies from the referenced files.

!!! note

    If using different files for regular dependencies, [`--requirements-files`](configuration.md#requirements-files)
    (or its `requirements_files` equivalent in `pyproject.toml`) can be used to instruct _deptry_ about the
    requirements files locations. Similarly, [`--requirements-files-dev`](configuration.md#requirements-files-dev) (or
    its `requirements_files_dev` equivalent in `pyproject.toml`) can be used for requirements files containing
    development dependencies.
