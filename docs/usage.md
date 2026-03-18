# Usage & Configuration

## Basic Usage

_deptry_ can be run with:

```shell
deptry .
```

where `.` is the path to the root directory of the project to be scanned.

If your project has multiple source directories, multiple root directories can be provided:

```shell
deptry a_directory another_directory
```

If you want to configure _deptry_ using `pyproject.toml`, or if your dependencies are stored in `pyproject.toml`, but it is located in another location than the one _deptry_ is run from, you can specify the location to it by using `--config <path_to_pyproject.toml>` argument.

## Dependencies extraction

_deptry_ can extract dependencies from a broad range of [dependency managers](supported-dependency-managers.md).

Dependencies are always extracted into two separate groups:

- regular ones, meant to be used in the codebase
- development ones

This is an important distinction, as development dependencies are usually meant to only be used outside the
codebase (e.g. `pytest` to run tests, Mypy for type-checking, or Ruff for formatting). For this reason, _deptry_ will
not run [Unused dependencies (DEP002)](rules-violations.md#unused-dependencies-dep002) for development dependencies.

## Imports extraction

_deptry_ will search for imports in Python files (`*.py`, and `*.ipynb` unless [`--ignore-notebooks`](#ignore-notebooks)
is set) that are not part of excluded files.

Imports will be extracted regardless of where they are made in a file (top-level, functions, class methods, guarded by
conditions, ...).

The only exception is imports that are guarded
by [`TYPE_CHECKING`](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING). In this specific case,
_deptry_ will not extract those imports, as they are not considered problematic. For instance:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # This import will not be extracted as it is guarded by `TYPE_CHECKING` and `from __future__ import annotations`
    # is used. This means the import should only be evaluated by type checkers, and should not be evaluated during runtime.
    import mypy_boto3_s3
```

### Inline ignore comments

Individual import statements can be excluded from _deptry_'s analysis by adding an inline `# deptry: ignore` comment,
similar to `# noqa` in flake8/ruff or `# type: ignore` in mypy. The following forms are supported:

```python
import foo  # deptry: ignore
```

This will suppress all violation rules for this import. To suppress only specific rules, provide the rule codes in
brackets:

```python
import foo  # deptry: ignore[DEP001]
import bar  # deptry: ignore[DEP001,DEP003]
```

The comment must be placed on the same line as the import statement (specifically, on the line where the `import` or
`from` keyword appears).

!!! note

    Inline ignore comments only apply to rules that report violations on import lines (DEP001, DEP003, DEP004).
    Rules that report on dependency definitions (DEP002, DEP005) are not affected, as their violations point to
    `pyproject.toml` or requirements files, not to source code lines.

### Dynamic imports

There is some support for imports created with [`importlib.import_module`](https://docs.python.org/3/library/importlib.html#importlib.import_module) that use a string literal:

```python
import importlib

importlib.import_module("foo")  # package 'foo' imported
```

but not where the argument is provided dynamically from a variable, attribute, etc., e.g.:

```python
bar = "foo"
importlib.import_module(bar)  # Not detected
```

## Excluding files and directories

To determine issues with imported modules and dependencies, _deptry_ will scan the working directory and its subdirectories recursively for `.py` and `.ipynb` files, so it can
extract the imported modules from those files. Any file solely used for development purposes, such as a file used for unit testing, should not be scanned. By default, the directories
`venv`, `.venv`, `.direnv`, `tests`, `.git` and the file `setup.py` are excluded.

_deptry_ also reads entries in `.gitignore` file, to ignore any pattern present in the file, similarly to what `git` does.

To ignore other directories and files than the defaults, use the `--exclude` (short `-e`) flag. The argument can either be one long regular expression, or it can be reused multiple times to pass multiple smaller regular expressions. The paths should be specified as paths relative to the directory _deptry_ is running in, without the trailing `./`. An example:

```shell
deptry . --exclude bar --exclude ".*/foo/"
deptry . --exclude "bar|.*/foo/"
```

The two statements above are equivalent, and will both ignore all files in the directory `bar`, and all files within any directory named `foo`.

Note that using the `--exclude` argument overwrites the defaults, and will prevent _deptry_ from considering entries in
`.gitignore`.
To add additional patterns to ignore on top of the defaults instead of overwriting them, or to make sure that _deptry_
still considers `.gitignore`, use the `--extend-exclude` (short `-ee`) flag.

```shell
deptry . --extend-exclude bar --extend-exclude ".*/foo/"
deptry . --extend-exclude "bar|.*/foo/"
```

This will exclude `venv`, `.venv`, `.direnv`, `.git`, `tests`, `setup.py`, `bar`, and any directory named `foo`, as well
as entries in `.gitignore`, if there are some.

## Usage in pre-commit

_deptry_ can be added to your [pre-commit](https://pre-commit.com/) rules. Here is
an example config for your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/osprey-oss/deptry.git
  rev: "<tag>"
  hooks:
    - id: deptry
      args: ["--ignore", "DEP001"]
```

Replace `<tag>` with one of the [tags](https://github.com/osprey-oss/deptry/tags) from the
project or a specific commit hash.

!!! important

    This will only pull in the pre commit-hooks config file from the version passed to the `rev` agument. The actual version of _deptry_ that will be run will be the first one found in your path, so you will need to add _deptry_ to your local virtual environment.

    For the pre-commit hook to run successfully, it should be run within the virtual environment of the project to be scanned, since it needs access to the metadata of the installed packages.

## Increasing verbosity

To show more details about the scanned Python files, the imported modules found, and how _deptry_ determines issues in dependencies, add the `--verbose` (short `-v`) flag:

```shell
deptry . --verbose
```

## Configuration

_deptry_ can be configured with command line arguments or by adding a `[tool.deptry]` section to `pyproject.toml`.

### Lookup hierarchy

The lookup hierarchy for each configuration option is as follows:

1. Default value is used
2. If set, value in `[tool.deptry]` section of `pyproject.toml` is used, overriding the default
3. If set, value passed through the CLI is used, overriding both the default and `pyproject.toml` values

### Options

#### Config

Path to the `pyproject.toml` file that holds _deptry_'s configuration and dependencies definition (if any).

- Type: `Path`
- Default: `pyproject.toml`
- CLI option name: `--config`
- CLI example:
```shell
deptry . --config sub_directory/pyproject.toml
```

#### No ANSI

Disable ANSI characters in terminal output.

- Type: `bool`
- Default: `False`
- CLI option name: `--no-ansi`
- CLI example:
```shell
deptry . --no-ansi
```

#### Exclude

List of patterns to exclude when searching for source files.

- Type: `list[str]`
- Default: `["venv", "\.venv", "\.direnv", "tests", "\.git", "setup\.py"]`
- `pyproject.toml` option name: `exclude`
- CLI option name: `--exclude` (short: `-e`)
- `pyproject.toml` example:
```toml
[tool.deptry]
exclude = ["a_directory", "a_python_file\\.py", "a_pattern/.*"]
```
- CLI example:
```shell
deptry . --exclude "a_directory|a_python_file\.py|a_pattern/.*"
```

#### Extend exclude

Additional list of patterns to exclude when searching for source files.
This extends the patterns set in [Exclude](#exclude), to allow defining patterns while keeping the default list.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `extend_exclude`
- CLI option name: `--extend-exclude` (short: `-ee`)
- `pyproject.toml` example:
```toml
[tool.deptry]
extend_exclude = ["a_directory", "a_python_file\\.py", "a_pattern/.*"]
```
- CLI example:
```shell
deptry . --extend-exclude "a_directory|a_python_file\.py|a_pattern/.*"
```

#### Ignore

A comma-separated list of [rules](rules-violations.md) to ignore.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `ignore`
- CLI option name: `--ignore` (short: `-i`)
- `pyproject.toml` example:
```toml
[tool.deptry]
ignore = ["DEP003", "DEP004"]
```
- CLI example:
```shell
deptry . --ignore DEP003,DEP004
```

#### Per rule ignores

A comma-separated mapping of packages or modules to be ignored per [rule](rules-violations.md) .

- Type: `dict[str, list[str] | str]`
- Default: `{}`
- `pyproject.toml` option name: `per_rule_ignores`
- CLI option name: `--per-rule-ignores` (short: `-pri`)
- `pyproject.toml` example:
```toml
[tool.deptry.per_rule_ignores]
DEP001 = ["matplotlib"]
DEP002 = ["pandas", "numpy"]
```
- CLI example:
```shell
deptry . --per-rule-ignores "DEP001=matplotlib,DEP002=pandas|numpy"
```

#### Ignore notebooks

Disable searching for notebooks (`*.ipynb`) files when looking for imports.

- Type: `bool`
- Default: `False`
- `pyproject.toml` option name: `ignore_notebooks`
- CLI option name: `--ignore-notebooks` (short: `-nb`)
- `pyproject.toml` example:
```toml
[tool.deptry]
ignore_notebooks = true
```
- CLI example:
```shell
deptry . --ignore-notebooks
```

#### Requirements files

List of [`pip` requirements files](https://pip.pypa.io/en/stable/user_guide/#requirements-files) that contain the source dependencies.

- Type: `list[str]`
- Default: `["requirements.txt"]`
- `pyproject.toml` option name: `requirements_files`
- CLI option name: `--requirements-files` (short: `-rt`)
- `pyproject.toml` example:
```toml
[tool.deptry]
requirements_files = ["requirements.txt", "requirements-private.txt"]
```
- CLI example:
```shell
deptry . --requirements-files requirements.txt,requirements-private.txt
```

#### Requirements files dev

List of [`pip` requirements files](https://pip.pypa.io/en/stable/user_guide/#requirements-files) that contain the source development dependencies.

- Type: `list[str]`
- Default: `["dev-requirements.txt", "requirements-dev.txt"]`
- `pyproject.toml` option name: `requirements_files_dev`
- CLI option name: `--requirements-files-dev` (short: `-rtd`)
- `pyproject.toml` example:
```toml
[tool.deptry]
requirements_files_dev = ["requirements-dev.txt", "requirements-tests.txt"]
```
- CLI example:
```shell
deptry . --requirements-files-dev requirements-dev.txt,requirements-tests.txt
```

#### Known first party

List of Python modules that should be considered as first party ones. This is useful in case _deptry_ is not able to automatically detect modules that should be considered as local ones.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `known_first_party`
- CLI option name: `--known-first-party` (short: `-kf`)
- `pyproject.toml` example:
```toml
[tool.deptry]
known_first_party = ["bar", "foo"]
```
- CLI example:
```shell
deptry . --known-first-party bar --known-first-party foo
```

#### JSON output

Write the detected issues to a JSON file. This will write the following kind of output:

```json
[
     {
         "error": {
             "code": "DEP002",
             "message": "uvicorn defined as a dependency but not used in the codebase"
         },
         "module": "uvicorn",
         "location": {
             "file": "pyproject.toml",
             "line": null,
             "column": null
         }
     },
     {
         "error": {
             "code": "DEP002",
             "message": "uvloop defined as a dependency but not used in the codebase"
         },
         "module": "uvloop",
         "location": {
             "file": "pyproject.toml",
             "line": null,
             "column": null
         }
     },
     {
         "error": {
             "code": "DEP004",
             "message": "black imported but declared as a dev dependency"
         },
         "module": "black",
         "location": {
             "file": "src/main.py",
             "line": 4,
             "column": 0
         }
     },
     {
         "error": {
             "code": "DEP003",
             "message": "httpx imported but it is a transitive dependency"
         },
         "module": "httpx",
         "location": {
             "file": "src/main.py",
             "line": 6,
             "column": 0
         }
     }
]
```

- Type: `Path`
- Default: `None`
- `pyproject.toml` option name: `json_output`
- CLI option name: `--json-output` (short: `-o`)
- `pyproject.toml` example:
```toml
[tool.deptry]
json_output = "deptry_report.txt"
```
- CLI example:
```shell
deptry . --json-output deptry_report.txt
```

#### GitHub output

Print [GitHub Actions annotations](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands) in the console when dependency issues are detected.

Annotations follow this format:

```shell
::error file=<file>,line=<line>,col=<column>,title=<error_code>::<error_message>
```

By default, violations are annotated as errors. To report specific violation codes as warnings instead, use the [GitHub warning errors](#github-warning-errors) option.

- Type: `bool`
- Default: `False`
- `pyproject.toml` option name: `github_output`
- CLI option name: `--github-output`
- `pyproject.toml` example:
```toml
[tool.deptry]
github_output = true
```
- CLI example:
```shell
deptry . --github-output
```

#### GitHub warning errors

When [GitHub output](#github-output) option is enabled, this sets the severity of messages to `warning` instead of `error` for the specified error codes.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `github_warning_errors`
- CLI option name: `--github-warning-errors`
- `pyproject.toml` example:
```toml
[tool.deptry]
github_warning_errors = ["DEP001", "DEP002"]
```
- CLI example:
```shell
deptry . --github-warning-errors DEP001,DEP002
```

#### Package module name map

Deptry will automatically detect top level modules names that belong to a
module in two ways.
The first is by inspecting the installed packages. The second, used as fallback
for when the package is not installed, is by translating the package name to a
module name (`Foo-Bar` translates to `foo_bar`).

This however is not always sufficient. A situation may occur where a package is
not installed because it is optional and unused in the current installation.
Then when the package name doesn't directly translate to the top level module
name, or there are more top level modules names, Deptry may report both
unused packages, and missing packages. A concrete example is deptry reporting unused (optional) dependency
`foo-python`, and missing package `foo`, while package `foo-python` would
install top level module `foo`, if it were installed.

A solution is to pre-define a mapping between the package name and the top
level module name(s).

* Type `dict[str, list[str] | str]`
* Default: `{}`
* `pyproject.toml` option name: `package_module_name_map`
* CLI option name: `--package-module-name-map` (short: `-pmnm`)
* `pyproject.toml` examples:
```toml
[tool.deptry.package_module_name_map]
foo-python = "foo"
```
Or for multiple top level module names:
```toml
[tool.deptry.package_module_name_map]
foo-python = [
    "foo",
    "bar",
]
```
* CLI examples:
```shell
deptry . --package-module-name-map "foo-python=foo"
```
Multiple module names are joined by a pipe (`|`):
```shell
deptry . --package-module-name-map "foo-python=foo|bar"
```
Multiple package name to module name mappings are joined by a comma (`,`):
```shell
deptry . --package-module-name-map "foo-python=foo,bar-python=bar"
```

#### Optional dependencies dev groups

Historically, PEP 621
did [not define](https://peps.python.org/pep-0621/#recommend-that-tools-put-development-related-dependencies-into-a-dev-extra)
a standard convention for specifying development dependencies. [PEP 735](https://peps.python.org/pep-0735/) now covers
this, but in the meantime, several projects defined development dependencies under `[project.optional-dependencies]`.
_deptry_ offers a mechanism to interpret specific optional dependency groups as development dependencies.

By default, all dependencies under `[project.dependencies]` and `[project.optional-dependencies]` are extracted as
regular dependencies. By using the `--optional-dependencies-dev-groups` argument, users can specify which groups defined
under `[project.optional-dependencies]` should be treated as development dependencies instead. This is particularly
useful for projects that adhere to PEP 621 but do not employ a separate build tool for declaring development
dependencies.

For example, consider a project with the following `pyproject.toml`:

```toml
[project]
...
dependencies = ["httpx"]

[project.optional-dependencies]
plot = ["matplotlib"]
test = ["pytest"]
```

By default, `httpx`, `matplotlib` and `pytest` are extracted as regular dependencies. By specifying
`--optional-dependencies-dev-groups=test`, `pytest` dependency will be treated as a development dependency instead.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `optional_dependencies_dev_groups`
- CLI option name: `--optional-dependencies-dev-groups` (short: `-oddg`)
- `pyproject.toml` example:
```toml
[tool.deptry]
optional_dependencies_dev_groups = ["test", "docs"]
```
- CLI example:
```shell
deptry . --optional-dependencies-dev-groups "test,docs"
```

#### PEP 621 dev dependency groups

!!! warning

    This option is deprecated. Use [`--optional-dependencies-dev-groups`](#optional-dependencies-dev-groups) instead.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `pep621_dev_dependency_groups`
- CLI option name: `--pep621-dev-dependency-groups` (short: `-ddg`)
- `pyproject.toml` example:
```toml
[tool.deptry]
pep621_dev_dependency_groups = ["test", "docs"]
```
- CLI example:
```shell
deptry . --pep621-dev-dependency-groups "test,docs"
```

#### Non-dev dependency groups

By default, _deptry_ considers that groups defined under `[dependency-groups]` contain development dependencies. Some
projects use dependency groups to define optional regular dependencies. To account for that, it is possible to specify a
list of groups that need to be treated as containing regular dependencies.

For example, consider a project with the following `pyproject.toml`:

```toml
[project]
...
dependencies = ["httpx"]

[dependency-groups]
server = ["uvicorn"]
telemetry = ["opentelemetry-sdk"]
```

By default, `uvicorn` and `opentelemetry-sdk` are extracted as development dependencies. By specifying
`--non-dev-dependency-groups=server,telemetry`, `uvicorn` and `opentelemetry-sdk` will be treated as regular
dependencies instead.

- Type: `list[str]`
- Default: `[]`
- `pyproject.toml` option name: `non_dev_dependency_groups`
- CLI option name: `--non-dev-dependency-groups` (short: `-nddg`)
- `pyproject.toml` example:
```toml
[tool.deptry]
non_dev_dependency_groups = ["server", "telemetry"]
```
- CLI example:
```shell
deptry . --non-dev-dependency-groups "server,telemetry"
```

#### Experimental namespace package

!!! warning

    This option is experimental and disabled by default for now, as it could degrade performance in large codebases.

Enable experimental namespace package ([PEP 420](https://peps.python.org/pep-0420/)) support.

When enabled, deptry will not only rely on the presence of `__init__.py` file in a directory to determine if it is a
local Python module or not, but will consider any Python file in the directory or its subdirectories, recursively. If a
Python file is found, then the directory will be considered as a local Python module.

- Type: `bool`
- Default: `False`
- `pyproject.toml` option name: `experimental_namespace_package`
- CLI option name: `--experimental-namespace-package`
- `pyproject.toml` example:
```toml
[tool.deptry]
experimental_namespace_package = true
```
- CLI example:
```shell
deptry . --experimental-namespace-package
```
