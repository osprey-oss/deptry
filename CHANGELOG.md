# Changelog

## 0.25.0 - 2025-03-18

### Repository moved to Osprey OSS

deptry has moved from [fpgmaas/deptry](https://github.com/fpgmaas/deptry) to [osprey-oss/deptry](https://github.com/osprey-oss/deptry) under the new Osprey OSS organisation. This ensures the project is not tied to a single account and makes it easier to manage contributors and access as the project grows.

### Features

* Support inline `# deptry: ignore` comments to suppress violations ([#1473](https://github.com/fpgmaas/deptry/pull/1473))
* Support non-dev dependency groups with `--non-dev-dependency-groups` ([#1440](https://github.com/fpgmaas/deptry/pull/1440))
* Use `tomli` on Python < 3.15 for TOML 1.1 support ([#1446](https://github.com/fpgmaas/deptry/pull/1446))
* Add `--optional-dependencies-dev-groups` and deprecate `--pep621-dev-dependency-groups` ([#1391](https://github.com/fpgmaas/deptry/pull/1391))

### Bug Fixes

* Ensure that `--config` does not suppress output ([#1390](https://github.com/fpgmaas/deptry/pull/1390))

### Full Changelog

https://github.com/fpgmaas/deptry/compare/0.24.0...0.25.0

## 0.24.0 - 2025-11-09

### Breaking changes

#### Python 3.9 support dropped

Support for Python 3.9 has been dropped, as it has reached its end of life.

#### PyPy 3.10 support dropped, 3.11 added

Support for PyPy 3.10 has been dropped, since it is unsupported. We now only test against PyPy 3.11, and only publish wheels for this version.

### Features

* Add GitHub Actions annotations reporter ([#1059](https://github.com/osprey-oss/deptry/pull/1059))
* Add support for Python 3.14 ([#1224](https://github.com/osprey-oss/deptry/pull/1224))
* Drop support for Python 3.9 ([#1328](https://github.com/osprey-oss/deptry/pull/1328))
* Publish wheels for PyPy 3.11 and drop 3.10 ([#1227](https://github.com/osprey-oss/deptry/pull/1227))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.23.1...0.24.0


## 0.23.1 - 2025-07-30

### Bug Fixes

* Improve handling of `TYPE_CHECKING` blocks by supporting `import typing as t` and checking `t.TYPE_CHECKING` ([#1218](https://github.com/osprey-oss/deptry/pull/1218))
* Fix missing hyperlink in report output ([#1162](https://github.com/osprey-oss/deptry/pull/1162))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.23.0...0.23.1


## 0.23.0 - 2025-01-25

### Features

* Correctly detect transitive dependencies with different module names ([#1033](https://github.com/osprey-oss/deptry/pull/1033))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.22.0...0.23.0


## 0.22.0 - 2025-01-10

Poetry 2.0 introduced support
for [defining project metadata in PEP 621](https://python-poetry.org/blog/announcing-poetry-2.0.0/). This is now
supported by _deptry_. [Documentation](https://deptry.com/supported-dependency-managers/#poetry) has been updated to
detail _deptry_'s behavior.

### Features

* Support PEP 621 in Poetry 2.0+ ([#1003](https://github.com/osprey-oss/deptry/pull/1003))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.21.2...0.22.0


## 0.21.2 - 2024-12-19

### Miscellaneous

* Provide wheels for musllinux ([#979](https://github.com/osprey-oss/deptry/pull/979))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.21.1...0.21.2


## 0.21.1 - 2024-11-15

### Bug Fixes

* Handle string requirements files for `setuptools` dynamic
  dependencies ([#945](https://github.com/osprey-oss/deptry/pull/945))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.21.0...0.21.1


## 0.21.0 - 2024-11-08

### Breaking changes

#### Ignore files handling

Unless [`--exclude`](https://deptry.com/usage/#exclude) is used, _deptry_ excludes files found in common ignore
files (`.gitignore`, `.ignore`, `$HOME/.config/git/ignore`. ...), by using [`ignore`](https://crates.io/crates/ignore)
Rust crate. The default behaviour has been changed, so that now:

- git-related ignore rules (`.gitignore`, `$HOME/.config/git/ignore`, ...) are only used if _deptry_ is run inside a git
  repository
- `.gitignore` files that are in parent directories of the git repository from where deptry is run are not
  used (previously, _deptry_ would traverse parent directories up to the root system)

If you were using `.gitignore` files for non-git repositories, you might want to switch to `.ignore` files, or use
[`--extend-exclude`](https://deptry.com/usage/#extend-exclude).

#### Requirements files parsing

_deptry_ now uses [`requirements-parser`](https://pypi.org/project/requirements-parser/) to parse dependencies from
requirements files, meaning that it can now extract nested requirements files referenced in other requirements files
without having to explicitly configure it in _deptry_.

For instance, if you have:

```python
# requirements.txt
-r cli-requirements.txt
httpx==0.27.2
```

```python
# cli-requirements.txt
click==8.1.7
```

With the default configuration, when parsing `requirements.txt`, both `httpx` and `click` will now be listed as
dependencies by _deptry_, while previously, only `httpx` was, unless _deptry_ was instructed about
`cli-requirements.txt` by using [`--requirements-files`](https://deptry.com/usage/#requirements-files). This new
behaviour also impacts development requirements files, that can be overridden by
using [`--requirements-files-dev`](https://deptry.com/usage/#requirements-files-dev).

#### Python 3.8 support dropped

Support for Python 3.8 has been dropped, as it has reached its end of life.

### Features

* _deptry_ now detects development dependencies from `[dependency-groups]` section, introduced
  by [PEP 735](https://peps.python.org/pep-0735/) ([#892](https://github.com/osprey-oss/deptry/pull/892))
* _deptry_ now supports `setuptools` dynamic dependencies set in `[tool.setuptools.dynamic]` section,
  see https://deptry.com/supported-dependency-managers/#setuptools for more
  details ([#894](https://github.com/osprey-oss/deptry/pull/894), [#724](https://github.com/osprey-oss/deptry/pull/724))
* Drop support for Python 3.8 ([#874](https://github.com/osprey-oss/deptry/pull/874))
* Improve ignore handling ([#908](https://github.com/osprey-oss/deptry/pull/908))
* Parse requirements files with `requirements-parser`, adding support for parsing nested requirements
  files referenced with `-r <requirement_file>` ([#913](https://github.com/osprey-oss/deptry/pull/913))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.20.0...0.21.0


## 0.20.0 - 2024-08-27

### Breaking changes

In release [0.15.0](https://github.com/osprey-oss/deptry/releases/tag/0.15.0), we announced the deprecation of the
following flags:

* `--requirements-txt` (and its `requirements_txt` setting counterpart in `pyproject.toml`)
* `--requirements-txt-dev` (and its `requirements_txt_dev` setting counterpart in `pyproject.toml`)

Those flags have now been removed. If you relied on them, you should now use, respectively:

* `--requirements-files` (and its `requirements_files` setting counterpart in `pyproject.toml`)
* `--requirements-files-dev` (and its `requirements_files_dev` setting counterpart in `pyproject.toml`)

### Features

* deptry now detects [uv](https://github.com/astral-sh/uv) and reads development dependencies from
  `[uv.tool.dev-dependencies]` section ([#816](https://github.com/osprey-oss/deptry/pull/816))
* Dynamically set max terminal width for better readability when displaying
  help ([#817](https://github.com/osprey-oss/deptry/pull/817))
* Remove deprecated `--requirements-txt`/`--requirements-txt-dev`
  flags ([#819](https://github.com/osprey-oss/deptry/pull/819))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.19.1...0.20.0


## 0.19.1 - 2024-08-10

### Features

* Add back PEP 420 support behind `--experimental-namespace-package` feature
  flag ([#808](https://github.com/osprey-oss/deptry/pull/808))
* Add support for Python 3.13 ([#713](https://github.com/osprey-oss/deptry/pull/713), [#809](https://github.com/osprey-oss/deptry/pull/809))

### Miscellaneous

* Provide Windows ARM64 wheels for Python ([#807](https://github.com/osprey-oss/deptry/pull/807))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.19.0...0.19.1


## 0.19.0 - 2024-08-08

This release reverts https://github.com/osprey-oss/deptry/pull/753 that caused a noticeable performance regression on large
codebases. The intent of the initial PR was to support projects following PEP 420, so if your project currently relies
on this behaviour, feel free to manifest your interest in https://github.com/osprey-oss/deptry/issues/740.

### Bug Fixes

* Revert "fix(core): use `rglob` to guess local Python modules (#753)" ([#798](https://github.com/osprey-oss/deptry/pull/798))

### New Contributors

* @huisman made their first contribution in [#796](https://github.com/osprey-oss/deptry/pull/796)

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.18.0...0.19.0


## 0.18.0 - 2024-07-31

### Features

* Support imports using `importlib.import_module` ([#782](https://github.com/osprey-oss/deptry/pull/782))

### New Contributors

* @lmmx made their first contribution in [#782](https://github.com/osprey-oss/deptry/pull/782)

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.17.0...0.18.0


## 0.17.0 - 2024-07-20

### Features

* Add a new rule `DEP005` to detect project dependencies that are in the standard library. ([#761](https://github.com/osprey-oss/deptry/pull/761))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.16.2...0.17.0


## 0.16.2 - 2024-07-05

### Bug Fixes

* Avoid crashing on PEP 621 and Poetry projects with no dependencies ([#752](https://github.com/osprey-oss/deptry/pull/752))
* Recursively search for Python files to detect local modules, to better support namespace packages ([#753](https://github.com/osprey-oss/deptry/pull/753))

### Miscellaneous

* Provide macOS ARM wheels for PyPy ([#691](https://github.com/osprey-oss/deptry/pull/691))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.16.1...0.16.2


## 0.16.1 - 2024-04-06

### Bug Fixes

* Skip type checking blocks whether future annotations are used ([#662](https://github.com/osprey-oss/deptry/pull/662))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.16.0...0.16.1


## 0.16.0 - 2024-04-04

### Breaking changes

#### `typing.TYPE_CHECKING` handling

Imports guarded by `typing.TYPE_CHECKING` when using `from __future__ import annotations` are now skipped. For instance:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  # This import will not be extracted as it is guarded by `TYPE_CHECKING` and `from __future__ import annotations`
  # is used. This means the import should only be evaluated by type checkers, and should not be evaluated during runtime.
  import mypy_boto3_s3
```

See https://deptry.com/usage/#imports-extraction for more information.

#### `requirements.in` handling

On projects using `pip` requirements format for defining dependencies, if `requirements_files` option is not overridden,
_deptry_ will first search for a `requirements.in` file before `requirements.txt`, to better support projects using
`pip-tools` and the like (which includes `uv` and Rye) out of the box. If you use `requirements.in` and want _deptry_ to
use `requirements.txt`, you can either pass `--requirements-files requirements.txt` when invoking _deptry_, or set the
option in `pyproject.toml`:

```toml
[tool.deptry]
requirements_files = ["requirements.txt"]
```

### Features

* Skip type checking blocks when parsing imports ([#652](https://github.com/osprey-oss/deptry/pull/652))
* Search for `requirements.in` before `requirements.txt` on projects using `pip` requirements format for
  dependencies ([#641](https://github.com/osprey-oss/deptry/pull/641))

### Bug Fixes

* Show module name instead of library name when reporting DEP003 ([#644](https://github.com/osprey-oss/deptry/pull/644)
* Better support for notebooks by handling magic commands and line
  continuations ([#656](https://github.com/osprey-oss/deptry/pull/656))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.15.0...0.16.0


## 0.15.0 - 2024-03-24

### Breaking changes

* In release [0.12.0](https://github.com/osprey-oss/deptry/releases/tag/0.12.0), we announced the deprecation of the following flags:
  * `--ignore-unused`
  * `--ignore-obsolete`
  * `--ignore-missing`
  * `--ignore-misplaced-dev`
  * `--ignore-transitive`
  * `--skip-unused`
  * `--skip-obsolete`
  * `--skip-missing`
  * `--skip-misplaced-dev`
  * `--skip-transitive`

  These flags are now no longer supported. If you are still using these flags and are planning to upgrade to this release, please refer to the release notes of [0.12.0](https://github.com/osprey-oss/deptry/releases/tag/0.12.0) for instructions on how to migrate to the new method of configuration. ([#596](https://github.com/osprey-oss/deptry/pull/596))

### Deprecations

* The options `requirements-txt` and `requirements-txt-dev` are replaced with `requirements-files` and `requirements-files-dev`, respectively, to provide better support for projects that use both a `requirements.in` and a `requirements.txt`. The legacy options will still be usable for the time being, with a warning being shown in the terminal, but they will be removed in a future release, so you are advised to migrate to the new ones. ([#609](https://github.com/osprey-oss/deptry/pull/609))

### Features

* Implement the collection of all Python files to be scanned by *deptry* in Rust ([#591](https://github.com/osprey-oss/deptry/pull/591))
* Implement import extraction for notebooks in Rust ([#606](https://github.com/osprey-oss/deptry/pull/606))
* Use ruff's AST parser for import extraction from Python files. This also adds support for files with Python 3.12 f-string syntax, see [PEP 701](https://docs.python.org/3/whatsnew/3.12.html#pep-701-syntactic-formalization-of-f-strings). ([#615](https://github.com/osprey-oss/deptry/pull/615))
* Improved logging of the detected imports and their locations when *deptry* is run in verbose mode ([#627](https://github.com/osprey-oss/deptry/pull/627))
* Introduce the `--pep621-dev-dependency-groups` flag that allows users to specify which groups under `[project.optional-dependencies]` are considered development dependencies ([#628](https://github.com/osprey-oss/deptry/pull/628))

### Bug Fixes

* Add back the license classifier, which was lost during the transition from Poetry to PDM in ([#624](https://github.com/osprey-oss/deptry/pull/624))

### Miscellaneous

* Remove upper bound on `requires-python` ([#621](https://github.com/osprey-oss/deptry/pull/621))
* Moved the documentation to [deptry.com](https://deptry.com) ([#630](https://github.com/osprey-oss/deptry/pull/630))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.14.2...0.15.0


## 0.14.2 - 2024-03-19

This release adds back MIT license classifier in package metadata, that was lost when changing the build backend ([#623](https://github.com/osprey-oss/deptry/pull/623)).

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.14.1...0.14.2


## 0.14.1 - 2024-03-18

This release improves runtime performance of built wheels by about 5%, and reduces their size ([#594](https://github.com/osprey-oss/deptry/pull/594)).

PyPy wheels are now also published on PyPI ([#612](https://github.com/osprey-oss/deptry/pull/612)).

### Bug Fixes

* Improve handling of comments in `requirements.txt` files ([#588](https://github.com/osprey-oss/deptry/pull/588))
* Avoid process hanging on error when parsing Python files ([#619](https://github.com/osprey-oss/deptry/pull/619))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.14.0...0.14.1


## 0.14.0 - 2024-03-14

This release significantly improves the speed of `deptry`, particularly for large projects, by utilizing Rust to manage the parsing of Abstract Syntax Trees (AST) from `.py` files and to extract the import statements. For some benchmarks, see below:

<img src="https://github.com/osprey-oss/deptry/assets/12008199/4f045622-7566-4cc3-a589-dbc6ea12ea5f" width="70%" />

Since the changes are all in the back-end, little has changed for the user other than the execution speed. The two minor notable changes are:

* Improved identification of `column` identifier in imports detection. Where earlier the column identifier for an imported module `foo` in the line `import foo` would be `0`, it now points to column `8`.

### Available wheels on PyPI

Where earlier releases published a single `.whl` file to PyPI, with the move to Rust we now build and publish wheels for a variety of platforms and architectures. More specifically, wheel files for the following combinations are now available on PyPI:

- Linux: ABI3 wheels for `x86_64` and `aarch64` architectures.
- Windows: ABI3 wheels for the `x64` architecture.
- macOS: ABI3 wheels for `x86_64` and `aarch64` (Apple Silicon) architectures.

Alongside the ABI3 wheels, we provide a source distribution (sdist) package.

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.13.0...0.14.0


## 0.13.0 - 2024-03-12

### Features

* _deptry_ will now report invalid configuration options defined in `pyproject.toml` ([#571](https://github.com/osprey-oss/deptry/pull/571))

### Bug Fixes

* Stricten URL detection to avoid flagging libraries like `httpx` as URLs ([#570](https://github.com/osprey-oss/deptry/pull/570))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.12.0...0.13.0


## 0.12.0 - 2023-06-18

This release introduces a significant change to the command-line flags and configuration options to make use of the error codes introduced in release [0.10.0](https://github.com/osprey-oss/deptry/releases/tag/0.10.0).

| Code   | Issue                            |
|--------|----------------------------------|
| DEP001 | Missing dependency               |
| DEP002 | Unused/obsolete dependency       |
| DEP003 | Transitive dependency            |
| DEP004 | Misplaced development dependency |

### Features

* **Replaced --skip-unused, --skip-obsolete, --skip-missing, --skip-misplaced-dev flags**: We have replaced the currently existing flags with the more generalized `--ignore` flag. Now, instead of skipping types of checks, you can specify the exact error codes to ignore using the `--ignore` flag (e.g., `deptry . --ignore "DEP001,DEP002"` to ignore checking for missing and unused dependencies).

The changes are also reflected in `pyproject.toml`. For example,


```toml
[tool.deptry]
skip_missing = true
skip_unused = true
```

is superseded by

```toml
[tool.deptry]
ignore = ["DEP001", "DEP002"]
```

* **Replaced --ignore-unused, --ignore-obsolete, --ignore-missing, --ignore-misplaced-dev flags**: Previously, specific checks for spefific dependencies/modules could be ingored using the `--ignore-<code>` flags. We are replacing these flags with the more generalized `--per-rule-ignores` flag. This flag allows you to specify dependencies that should be ignored for specific error codes, offering granular control over which errors are ignored for which dependencies. For instance, `deptry . --per-rule-ignores DEP001=matplotlib,DEP002=pandas|numpy` means `DEP001` will be ignored for `matplotlib`, while `DEP002` will be ignored for both `pandas` and `numpy`.

The changes are also reflected in `pyproject.toml`. For example,

```toml
[tool.deptry]
ignore_missing = ["matplotlib"]
ignore_unused = ["pandas", "numpy"]
```

is superseded by

```toml
[tool.deptry.per_rule_ignores]
DEP001 = ["matplotlib"]
DEP002 = ["pandas", "numpy"]
```

Please note that while the legacy arguments are still functional as of Deptry 0.12.0, we do plan to remove them in a future 1.0.0 release.


* Consider all groups for dev dependencies ([#392](https://github.com/osprey-oss/deptry/pull/392))

### Bug Fixes

* Handle `SyntaxError` raised by `ast.parse` ([#426](https://github.com/osprey-oss/deptry/pull/426))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.11.0...0.12.0


## 0.11.0 - 2023-05-10

### Deprecations

* `--skip-obsolete` CLI option and its `skip_obsolete` couterpart in `pyproject.toml` are being replaced with `--skip-unused` and `skip_unused`, respectively
* `--ignore-obsolete` CLI option and its `ignore_obsolete` counterpart in `pyproject.toml` are being replaced with `--ignore-unused` and `ignore_unused`, respectively

This is done to account for a wording change, as we are replacing "obsolete" with "unused", since it has a clearer meaning for users.

The legacy options will still be usable for the time being, with a warning being shown in the terminal, but they will be removed in a future release, so you are advised to migrate to the new ones.

### Features

* Add ability to pass multiple source directories ([#381](https://github.com/osprey-oss/deptry/pull/381))
* Replace the word `obsolete` with `unused` ([#373](https://github.com/osprey-oss/deptry/pull/373))

### Bug Fixes

* Load gitignore from where CLI is invoked ([#380](https://github.com/osprey-oss/deptry/pull/380))

### Full Changelog

https://github.com/osprey-oss/deptry/compare/0.10.1...0.11.0


## 0.10.1 - 2023-05-09

### Bug Fixes

* Fix terminal output when only a single file is scanned ([#372](https://github.com/osprey-oss/deptry/pull/372))
* Fix issue with `DEP004` being raised incorrectly when a dependency is defined both as a dev one and non-dev one ([#376](https://github.com/osprey-oss/deptry/pull/376))

### Full Changelog

[0.10.0...0.10.1](https://github.com/osprey-oss/deptry/compare/0.10.0...0.10.1)


## 0.10.0 - 2023-05-08

### Breaking Changes

Release `0.10.0` of deptry brings a significant improvement to the way in which issues are reported. Previously, issues were reported in a summarized format, making it difficult for users to pinpoint exactly where in the code the issue was occurring. This is resolved by https://github.com/osprey-oss/deptry/pull/357, which adds location information to the detected issues.

https://github.com/osprey-oss/deptry/pull/367 adds error codes to identify the different issue types:

| Code   | Issue                            |
|--------|----------------------------------|
| DEP001 | Missing dependency               |
| DEP002 | Obsolete dependency              |
| DEP003 | Transitive dependency            |
| DEP004 | Misplaced development dependency |

Here's an example of how issues are now reported in release 0.10.0:

```console
foo/bar.py:11:11: DEP002 'an_import' imported but missing from the dependencies
foo/bar.py:12:11: DEP002 'another_import' imported but missing from the dependencies
foo/baz.py:13:11: DEP003 'cfgv' imported but it is a transitive dependency
pyproject.toml: DEP001 'pandas' defined as a dependency but not used in the codebase
```

The json output generated by using the `-o` or `--json-output` is also modified to include the new error codes and location information:

```json
{
  "error": {
    "code": "DEP001",
    "message": "'seven' imported but missing from the dependency definitions"
  },
  "module": "seven",
  "location": {
    "file": "foo/bar.py",
    "line": 2,
    "column": 0
  }
}
```

### Features

* Add location to error reports by ([#357](https://github.com/osprey-oss/deptry/pull/357))
* Add colours to text output by ([#368](https://github.com/osprey-oss/deptry/pull/368))

### Full Changelog

[0.9.0...0.10.0](https://github.com/osprey-oss/deptry/compare/0.9.0...0.10.0)


## 0.9.0 - 2023-05-06

### Breaking Changes

#### Python 3.7 support dropped

Support for Python 3.7 has been dropped in https://github.com/osprey-oss/deptry/pull/352, given that it will reach end of life soon, and that PyPI stats show a really low usage of it. If you are using `deptry` on Python 3.7, consider upgrading to 3.8, or staying on `<0.9.0`.

#### Behaviour changes in package name guessing

In case packages don't provide the Python modules they expose, `deptry` tries to guess the package name by converting `-` to `_`, as a best effort, and warns about it in the logs. Before https://github.com/osprey-oss/deptry/pull/337, `deptry` always guessed the module name, regardless of if the package provided the necessary information or not. Now, it will only guess the module name if the package does not provide the information and no mapping has been provided using the new `--package-module-name-map` flag (or `package_module_name_map` option in `pyproject.toml`).

#### Handling modules without `__init__.py`

With https://github.com/osprey-oss/deptry/pull/285, `deptry` will now consider the following things as local modules:
- directories without `__init__.py` (and at least one Python file)
- single Python files

Previously, `deptry` only considered directories as local modules if an `__init__.py` was present, and did not account for cases where a single Python file could also be a local module, alongside directories.

### Features

* Drop support for Python 3.7 ([#352](https://github.com/osprey-oss/deptry/pull/352))
* Only try to guess module associated to a dependency as a fallback for when the package doesn't provide such information ([#337](https://github.com/osprey-oss/deptry/pull/337))
* Handle local modules without `__init__.py` ([#285](https://github.com/osprey-oss/deptry/pull/285))
* Ability to configure a map of package names to module names ([#333](https://github.com/osprey-oss/deptry/pull/333))

### Bug Fixes

* Replace 'PDM' with 'poetry' in log ([#294](https://github.com/osprey-oss/deptry/pull/294))
* Account for Windows in code and tests ([#343](https://github.com/osprey-oss/deptry/pull/343))

### Miscellaneous

* Run tests on macOS and Windows on CI ([#342](https://github.com/osprey-oss/deptry/pull/342))

### Full Changelog

[0.8.0...0.9.0](https://github.com/osprey-oss/deptry/compare/0.9.0...0.10.0)


## 0.8.0 - 2023-01-24

### Features

* Don't filter out `setuptools` ([#262](https://github.com/osprey-oss/deptry/pull/262))
* Use `sys.stdlib_module_names` to get stdlibs in Python >= 3.10 ([#275](https://github.com/osprey-oss/deptry/pull/275))

### Miscellaneous

* Drop `flake8` to only use `ruff` ([#268](https://github.com/osprey-oss/deptry/pull/268))
* Use more `ruff` rules and replace `pyupgrade` and `pygrep-hooks` usages ([#276](https://github.com/osprey-oss/deptry/pull/276))

### Full Changelog

[0.7.1...0.8.0](https://github.com/osprey-oss/deptry/compare/0.7.1...0.8.0)


## 0.7.1 - 2023-01-07

### Features

* Exclude files from `.gitignore` [#248](https://github.com/osprey-oss/deptry/pull/248))
* Add support for known first party modules [#257](https://github.com/osprey-oss/deptry/pull/257))

### Full Changelog

[0.7.0...0.7.1](https://github.com/osprey-oss/deptry/compare/0.7.0...0.7.1)


## 0.7.0 - 2022-12-27

### Breaking Changes

Previously,  `deptry` always searched for a `pyproject.toml` file in the root directory passed as a positional argument to the `deptry` command. Since this is not in line with what most other tools in the ecosystem do, this is changed in release `0.7.0`.

In previous releases, when running:

```shell
deptry src
```

`deptry` would search for both a `pyproject.toml` and for Python files to scan in the `src` directory.

Since this release, when running:

```shell
deptry src
```

`deptry` will search for `pyproject.toml` in the location it is run from, and for Python files to scan in the `src` directory.

The downside of the changes outlined above, is that this could break some projects that did explicitly want to find `pyproject.toml` in a directory other than the positional argument specified as `root`. For this purpose, release `0.7.0` adds a `--config` argument that can be used to explicitly pass the location of `pyproject.toml`.

### Features

* Separate `pyproject.toml` location from `root` argument ([#244](https://github.com/osprey-oss/deptry/pull/244))
* Expose and handle `--config` argument ([#245](https://github.com/osprey-oss/deptry/pull/245))

### Miscellaneous

* Only load local modules once by ([#242](https://github.com/osprey-oss/deptry/pull/242))
* More efficient Python files retrieval ([#243](https://github.com/osprey-oss/deptry/pull/243))

### Full Changelog

[0.6.6...0.7.0](https://github.com/osprey-oss/deptry/compare/0.6.6...0.7.0)


## 0.6.6 - 2022-11-22

### Features

* Add .direnv to default exclude argument ([#197](https://github.com/osprey-oss/deptry/pull/197))
* Add logic to `NotebookImportExtractor` to guess the encoding on initial `UnicodeDecodeError` ([#216](https://github.com/osprey-oss/deptry/pull/216))

### Miscellaneous

* Decrease lower bound of `chardet` dependency to `4.0.0` ([#205](https://github.com/osprey-oss/deptry/pull/205))

### Full Changelog

[0.6.5...0.6.6](https://github.com/osprey-oss/deptry/compare/0.6.5...0.6.6)


## 0.6.5 - 2022-11-14

No user facing change.

### Full Changelog

[0.6.4...0.6.5](https://github.com/osprey-oss/deptry/compare/0.6.4...0.6.5)


## 0.6.4 - 2022-11-09

### Features

* Add support for PEP 621 ([#166](https://github.com/osprey-oss/deptry/pull/166))

### Bug Fixes

* Remove obsolete duplicated local import detection ([#172](https://github.com/osprey-oss/deptry/pull/172))

### Full Changelog

[0.6.3...0.6.4](https://github.com/osprey-oss/deptry/compare/0.6.3...0.6.4)


## 0.6.3 - 2022-10-23

### Features

* Add hook for usage with `pre-commit` ([#157](https://github.com/osprey-oss/deptry/pull/157))

### Full Changelog

[0.6.2...0.6.3](https://github.com/osprey-oss/deptry/compare/0.6.2...0.6.3)


## 0.6.2 - 2022-10-22

### Bug Fixes

* Solve issue with importing from local files ([#163](https://github.com/osprey-oss/deptry/pull/163))

### Full Changelog

[0.6.1...0.6.2](https://github.com/osprey-oss/deptry/compare/0.6.1...0.6.2)


## 0.6.1 - 2022-10-08

### Features

* Add support for PEP621 with PDM ([#155](https://github.com/osprey-oss/deptry/pull/155))

### Full Changelog

[0.5.13...0.6.1](https://github.com/osprey-oss/deptry/compare/0.5.13...0.6.1)


## 0.5.13 - 2022-10-02

### Features

* Add support for Python 3.11 ([#152](https://github.com/osprey-oss/deptry/pull/152))

### Full Changelog

[0.5.12...0.5.13](https://github.com/osprey-oss/deptry/compare/0.5.12...0.5.13)


## 0.5.12 - 2022-10-01

### Features

* Accept multiple `requirements.txt` ([#141](https://github.com/osprey-oss/deptry/pull/141))

### Full Changelog

[0.5.11...0.5.12](https://github.com/osprey-oss/deptry/compare/0.5.11...0.5.12)


## 0.5.11 - 2022-09-30

### Miscellaneous

* Remove dependency on `isort` ([#140](https://github.com/osprey-oss/deptry/pull/140))

### Full Changelog

[0.5.10...0.5.11](https://github.com/osprey-oss/deptry/compare/0.5.10...0.5.11)


## 0.5.10 - 2022-09-27

No user facing change.

### Full Changelog

[0.5.9...0.5.10](https://github.com/osprey-oss/deptry/compare/0.5.9...0.5.10)


## 0.5.9 - 2022-09-26

### Bug Fixes

* Fix issue with logging if no `[tool.deptry]` section was found in `pyproject.toml` ([#134](https://github.com/osprey-oss/deptry/pull/134))

### Full Changelog

[0.5.8...0.5.9](https://github.com/osprey-oss/deptry/compare/0.5.8...0.5.9)


## 0.5.8 - 2022-09-26

No user facing change.

### Full Changelog

[0.5.7...0.5.8](https://github.com/osprey-oss/deptry/compare/0.5.7...0.5.8)


## 0.5.7 - 2022-09-24

### Features

* Add option to write output to JSON file ([#125](https://github.com/osprey-oss/deptry/pull/125))

### Full Changelog

[0.5.6...0.5.7](https://github.com/osprey-oss/deptry/compare/0.5.6...0.5.7)


## 0.5.6 - 2022-09-22

### Miscellaneous

* Replace `toml` with `tomli`/`tomllib` for parsing TOML ([#123](https://github.com/osprey-oss/deptry/pull/123))

### Full Changelog

[0.5.5...0.5.6](https://github.com/osprey-oss/deptry/compare/0.5.5...0.5.6)


## 0.5.5 - 2022-09-20

### Miscellaneous

* Rename `DIRECTORY` argument to `ROOT` ([#121](https://github.com/osprey-oss/deptry/pull/121))

### Full Changelog

[0.5.4...0.5.5](https://github.com/osprey-oss/deptry/compare/0.5.4...0.5.5)


## 0.5.4 - 2022-09-19

### Miscellaneous

* Add a summary line to the logging ([#120](https://github.com/osprey-oss/deptry/pull/120))

### Full Changelog

[0.5.3...0.5.4](https://github.com/osprey-oss/deptry/compare/0.5.3...0.5.4)


## 0.5.3 - 2022-09-18

### Miscellaneous

* Set Python version upper range to `<4.0` ([#117](https://github.com/osprey-oss/deptry/pull/117))

### Full Changelog

[0.5.2...0.5.3](https://github.com/osprey-oss/deptry/compare/0.5.2...0.5.3)


## 0.5.2 - 2022-09-18

### Features

* Extract top level module names from `RECORD` ([#116](https://github.com/osprey-oss/deptry/pull/116))

### Full Changelog

[0.5.1...0.5.2](https://github.com/osprey-oss/deptry/compare/0.5.1...0.5.2)


## 0.5.1 - 2022-09-18

### Features

* Parse `egg=...` in urls for `requirements.txt` ([#115](https://github.com/osprey-oss/deptry/pull/115))

### Full Changelog

[0.5.0...0.5.1](https://github.com/osprey-oss/deptry/compare/0.5.0...0.5.1)


## 0.5.0 - 2022-09-17

### Features

* Support regexes for file exclusions ([#111](https://github.com/osprey-oss/deptry/pull/111))

### Full Changelog

[0.4.7...0.5.0](https://github.com/osprey-oss/deptry/compare/0.4.7...0.5.0)


## 0.4.7 - 2022-09-15

### Miscellaneous

* Only decode files if initial decoding failed ([#105](https://github.com/osprey-oss/deptry/pull/105))

### Full Changelog

[0.4.6...0.4.7](https://github.com/osprey-oss/deptry/compare/0.4.6...0.4.7)


## 0.4.6 - 2022-09-14

### Features

* Detect file encoding with `chardet` before parsing Python files ([#103](https://github.com/osprey-oss/deptry/pull/103))

### Full Changelog

[0.4.5...0.4.6](https://github.com/osprey-oss/deptry/compare/0.4.5...0.4.6)


## 0.4.5 - 2022-09-13

No user facing change.

### Full Changelog

[0.4.4...0.4.5](https://github.com/osprey-oss/deptry/compare/0.4.4...0.4.5)


## 0.4.4 - 2022-09-13

### Features

* Add support for reading dependencies form urls in `requirements.txt` ([#100](https://github.com/osprey-oss/deptry/pull/100))

### Full Changelog

[0.4.3...0.4.4](https://github.com/osprey-oss/deptry/compare/0.4.3...0.4.4)


## 0.4.3 - 2022-09-13

### Bug Fixes

* Solve an issue where missing dev dependencies were added to the list as `None` ([#99](https://github.com/osprey-oss/deptry/pull/99))

### Full Changelog

[0.4.2...0.4.3](https://github.com/osprey-oss/deptry/compare/0.4.2...0.4.3)


## 0.4.2 - 2022-09-12

### Features

* Add a warning to not install `deptry` globally, but within virtual environment ([#93](https://github.com/osprey-oss/deptry/pull/93))

### Bug Fixes

* Fix an issue with `requirements.txt` not being found if not in root dir ([#94](https://github.com/osprey-oss/deptry/pull/94))

### Full Changelog

[0.4.1...0.4.2](https://github.com/osprey-oss/deptry/compare/0.4.1...0.4.2)


## 0.4.1 - 2022-09-11

### Features

* Ignore `setuptools` and `setup.py` by default ([#88](https://github.com/osprey-oss/deptry/pull/88))

### Full Changelog

[0.4.0...0.4.1](https://github.com/osprey-oss/deptry/compare/0.4.0...0.4.1)


## 0.4.0 - 2022-09-11

### Features

* Add support for `requirements.txt` ([#87](https://github.com/osprey-oss/deptry/pull/87))

### Full Changelog

[0.3.2...0.4.0](https://github.com/osprey-oss/deptry/compare/0.3.2...0.4.0)


## 0.3.2 - 2022-09-10

No user facing change.

### Full Changelog

[0.3.1...0.3.2](https://github.com/osprey-oss/deptry/compare/0.3.1...0.3.2)


## 0.3.1 - 2022-09-10

### Features

* Use commas to separate items in CLI arguments ([#87](https://github.com/osprey-oss/deptry/pull/87))

### Full Changelog

[0.2.16...0.3.1](https://github.com/osprey-oss/deptry/compare/0.2.16...0.3.1)


## 0.2.17 - 2022-09-10

### Features

* Add `--extend-exclude` option ([#76](https://github.com/osprey-oss/deptry/pull/76))

### Full Changelog

[0.2.16...0.2.17](https://github.com/osprey-oss/deptry/compare/0.2.16...0.2.17)


## 0.2.16 - 2022-09-09

No user facing change.

### Full Changelog

[0.2.15...0.2.16](https://github.com/osprey-oss/deptry/compare/0.2.15...0.2.16)


## 0.2.15 - 2022-09-09

### Features

* Guess top level name of modules by replacing `-` with `_` ([#73](https://github.com/osprey-oss/deptry/pull/73))

### Full Changelog

[0.2.14...0.2.15](https://github.com/osprey-oss/deptry/compare/0.2.14...0.2.15)


## 0.2.14 - 2022-09-09

### Features

* Handle conditional dependencies ([#65](https://github.com/osprey-oss/deptry/pull/65))

### Miscellaneous

* Decrease lower bound of `click` dependency to `8.0.0` ([#205](https://github.com/osprey-oss/deptry/pull/205))

### Full Changelog

[0.2.13...0.2.14](https://github.com/osprey-oss/deptry/compare/0.2.13...0.2.14)


## 0.2.13 - 2022-09-09

No user facing change.

### Full Changelog

[0.2.12...0.2.13](https://github.com/osprey-oss/deptry/compare/0.2.12...0.2.13)


## 0.2.12 - 2022-09-09

No user facing change.

### Full Changelog

[0.2.11...0.2.12](https://github.com/osprey-oss/deptry/compare/0.2.11...0.2.12)


## 0.2.11 - 2022-09-09

No user facing change.

### Full Changelog

[0.2.10...0.2.11](https://github.com/osprey-oss/deptry/compare/0.2.10...0.2.11)


## 0.2.10 - 2022-09-08

No user facing change.

### Full Changelog

[0.2.9...0.2.10](https://github.com/osprey-oss/deptry/compare/0.2.9...0.2.10)


## 0.2.9 - 2022-09-08

### Bug Fixes

* Fix issue with relative imports ([#54](https://github.com/osprey-oss/deptry/pull/54))

### Full Changelog

[0.2.8...0.2.9](https://github.com/osprey-oss/deptry/compare/0.2.8...0.2.9)


## 0.2.8 - 2022-09-08

### Features

* Add check for misplaced development dependencies ([#51](https://github.com/osprey-oss/deptry/pull/51))

### Full Changelog

[0.2.7...0.2.8](https://github.com/osprey-oss/deptry/compare/0.2.7...0.2.8)


## 0.2.7 - 2022-09-07

No user facing change.

### Full Changelog

[0.2.6...0.2.7](https://github.com/osprey-oss/deptry/compare/0.2.6...0.2.7)


## 0.2.6 - 2022-09-07

### Features

* Add `--version` argument to the CLI to display `deptry`'s version ([#47](https://github.com/osprey-oss/deptry/pull/47))

### Full Changelog

[0.2.5...0.2.6](https://github.com/osprey-oss/deptry/compare/0.2.5...0.2.6)


## 0.2.5 - 2022-09-07

### Features

* Add check for missing and transitive dependencies ([#43](https://github.com/osprey-oss/deptry/pull/43))

### Full Changelog

[0.2.3...0.2.5](https://github.com/osprey-oss/deptry/compare/0.2.3...0.2.5)


## 0.2.3 - 2022-09-06

No user facing change.

### Full Changelog

[0.2.2...0.2.3](https://github.com/osprey-oss/deptry/compare/0.2.2...0.2.3)


## 0.2.2 - 2022-09-06

### Full Changelog

[0.2.1...0.2.2](https://github.com/osprey-oss/deptry/compare/0.2.1...0.2.2)


## 0.2.1 - 2022-09-05

### Full Changelog

[0.2.0...0.2.1](https://github.com/osprey-oss/deptry/compare/0.2.0...0.2.1)


## 0.2.0 - 2022-09-05

### Features

* Add support for Python 3.7 ([#27](https://github.com/osprey-oss/deptry/pull/27))

### Full Changelog

[0.1.5...0.2.0](https://github.com/osprey-oss/deptry/compare/0.1.5...0.2.0)


## 0.1.5 - 2022-09-04

### Miscellaneous

* Improve logging statements ([#25](https://github.com/osprey-oss/deptry/pull/25))

### Full Changelog

[0.1.4...0.1.5](https://github.com/osprey-oss/deptry/compare/0.1.4...0.1.5)


## 0.1.4 - 2022-09-04

### Miscellaneous

* Improve logging when package name is not found ([#25](https://github.com/osprey-oss/deptry/pull/25))

### Full Changelog

[0.1.3...0.1.4](https://github.com/osprey-oss/deptry/compare/0.1.3...0.1.4)


## 0.1.3 - 2022-09-04

### Features

* Parse imports within `if`/`else` statements ([#23](https://github.com/osprey-oss/deptry/pull/23))

### Full Changelog

[0.1.2...0.1.3](https://github.com/osprey-oss/deptry/compare/0.1.2...0.1.3)


## 0.1.2 - 2022-09-04

No use facing change.

### Full Changelog

[0.1.1...0.1.2](https://github.com/osprey-oss/deptry/compare/0.1.1...0.1.2)


## 0.1.1 - 2022-09-04

### Features

* Replace `deptry check` command with `deptry` ([#21](https://github.com/osprey-oss/deptry/pull/21))

### Full Changelog

[0.0.4...0.1.1](https://github.com/osprey-oss/deptry/compare/0.0.4...0.1.1)


## 0.0.4 - 2022-09-03

### Features

* Add ability to specify the root directory ([#13](https://github.com/osprey-oss/deptry/pull/13))

### Full Changelog

[0.0.3...0.0.4](https://github.com/osprey-oss/deptry/compare/0.0.3...0.0.4)


## 0.0.3 - 2022-09-03

### Features

* Add support for Jupyter Notebooks ([#11](https://github.com/osprey-oss/deptry/pull/11))

### Full Changelog

[0.0.2...0.0.3](https://github.com/osprey-oss/deptry/compare/0.0.2...0.0.3)


## 0.0.2 - 2022-09-02

### Features

* Add mapping for common packages without metadata ([#1](https://github.com/osprey-oss/deptry/pull/1))

### Full Changelog

[0.0.1...0.0.2](https://github.com/osprey-oss/deptry/compare/0.0.1...0.0.2)


## 0.0.1 - 2022-09-02

Initial release
