from __future__ import annotations

from pathlib import Path

from deptry.dependency_getter.requirements_files import RequirementsTxtDependencyGetter
from tests.utils import run_within_dir


def test_parse_requirements_files(tmp_path: Path) -> None:
    fake_requirements_files = """click==8.1.3 #123asd
colorama==0.4.5
importlib-metadata==4.2.0 ; python_version >= "3.7" and python_version < "3.8"
isort==5.10.1, <6.0
toml==0.10.2
typing-extensions
zipp==3.8.1
foobar[foo, bar]
SomeProject ~= 1.4.2
SomeProject2 == 5.4 ; python_version < '3.8'
SomeProject3 ; sys_platform == 'win32'
requests [security] >= 2.8.1, == 2.8.* ; python_version < "2.7"
# This is a comment, to show how #-prefixed lines are ignored.
#this is a comment without a space after the `#`, which should also be ignored.
pytest
pytest-cov
beautifulsoup4
docopt == 0.6.1
requests [security] >= 2.8.1, == 2.8.* ; python_version < "2.7"
fox-python
httpx==0.25.2
"""
    with run_within_dir(tmp_path):
        with Path("requirements.txt").open("w") as f:
            f.write(fake_requirements_files)

        getter = RequirementsTxtDependencyGetter(
            config=Path("pyproject.toml"),
            package_module_name_map={"fox-python": ("fox",)},
        )
        dependencies_extract = getter.get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 19
        assert len(dependencies_extract.dev_dependencies) == 0

        assert dependencies[1].name == "colorama"
        assert "colorama" in dependencies[1].top_levels

        assert dependencies[2].name == "importlib-metadata"
        assert "importlib_metadata" in dependencies[2].top_levels

        assert dependencies[11].name == "requests"
        assert "requests" in dependencies[11].top_levels

        assert dependencies[17].name == "fox-python"
        assert "fox" in dependencies[17].top_levels


def test_parse_requirements_files_urls(tmp_path: Path) -> None:
    fake_requirements_files = """urllib3 @ https://github.com/urllib3/urllib3/archive/refs/tags/1.26.8.zip
https://github.com/urllib3/urllib3/archive/refs/tags/1.26.8.zip
git+https://github.com/baz/foo-bar.git@asd#egg=foo-bar
git+https://github.com/baz/foo-bar.git@asd
git+https://github.com/abc123/bar-foo@xyz789#egg=bar-fooo
https://unsupported-specification.com"""

    with run_within_dir(tmp_path):
        with Path("requirements.txt").open("w") as f:
            f.write(fake_requirements_files)

        dependencies_extract = RequirementsTxtDependencyGetter(Path("pyproject.toml")).get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 5
        assert len(dependencies_extract.dev_dependencies) == 0

        assert dependencies[0].name == "urllib3"
        assert dependencies[1].name == "urllib3"
        assert dependencies[2].name == "foo-bar"
        assert dependencies[3].name == "foo-bar"
        assert dependencies[4].name == "bar-fooo"


def test_single(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        with Path("req.txt").open("w") as f:
            f.write("click==8.1.3 #123asd\ncolorama==0.4.5")

        dependencies_extract = RequirementsTxtDependencyGetter(
            Path("pyproject.toml"), requirements_files=("req.txt",)
        ).get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 2
        assert len(dependencies_extract.dev_dependencies) == 0

        assert dependencies[0].name == "click"
        assert dependencies[1].name == "colorama"


def test_multiple(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        with Path("foo.txt").open("w") as f:
            f.write("click==8.1.3 #123asd")

        with Path("bar.txt").open("w") as f:
            f.write("bar")

        dependencies_extract = RequirementsTxtDependencyGetter(
            Path("pyproject.toml"), requirements_files=("foo.txt", "bar.txt")
        ).get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 2
        assert len(dependencies_extract.dev_dependencies) == 0

        assert dependencies[0].name == "click"
        assert dependencies[1].name == "bar"


def test_dev_single(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        with Path("requirements.txt").open("w") as f:
            f.write("")

        with Path("requirements-dev.txt").open("w") as f:
            f.write("click==8.1.3 #123asd\ncolorama==0.4.5")

        dependencies_extract = RequirementsTxtDependencyGetter(Path("pyproject.toml")).get()
        dev_dependencies = dependencies_extract.dev_dependencies

        assert len(dependencies_extract.dependencies) == 0
        assert len(dev_dependencies) == 2

        assert dev_dependencies[1].name == "colorama"
        assert "colorama" in dev_dependencies[1].top_levels


def test_dev_multiple(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        with Path("requirements.txt").open("w") as f:
            f.write("")

        with Path("requirements-dev.txt").open("w") as f:
            f.write("click==8.1.3 #123asd")

        with Path("dev-requirements.txt").open("w") as f:
            f.write("bar")

        dependencies_extract = RequirementsTxtDependencyGetter(Path("pyproject.toml")).get()
        dev_dependencies = dependencies_extract.dev_dependencies

        assert len(dependencies_extract.dependencies) == 0
        assert len(dev_dependencies) == 2

        assert "click" in [dev_dependencies[0].name, dev_dependencies[1].name]
        assert "bar" in [dev_dependencies[0].name, dev_dependencies[1].name]


def test_dev_multiple_with_arguments(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        with Path("requirements.txt").open("w") as f:
            f.write("")

        with Path("foo.txt").open("w") as f:
            f.write("click==8.1.3 #123asd")

        with Path("bar.txt").open("w") as f:
            f.write("bar")

        dependencies_extract = RequirementsTxtDependencyGetter(
            Path("pyproject.toml"), requirements_files_dev=("foo.txt", "bar.txt")
        ).get()
        dev_dependencies = dependencies_extract.dev_dependencies

        assert len(dependencies_extract.dependencies) == 0
        assert len(dev_dependencies) == 2

        assert dev_dependencies[0].name == "click"
        assert dev_dependencies[1].name == "bar"


def test_parse_requirements_file_utf16_le(tmp_path: Path) -> None:
    """Test that requirements.txt files with UTF-16 LE encoding (with BOM) are parsed correctly."""
    content = "click==8.1.3\ncolorama==0.4.5\n"
    with run_within_dir(tmp_path):
        # Write with BOM (\xff\xfe) followed by UTF-16 LE encoded content, as editors like VS Code do.
        Path("requirements.txt").write_bytes(b"\xff\xfe" + content.encode("utf-16-le"))

        dependencies_extract = RequirementsTxtDependencyGetter(Path("pyproject.toml")).get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 2
        assert dependencies[0].name == "click"
        assert dependencies[1].name == "colorama"


def test_parse_requirements_file_utf16_be(tmp_path: Path) -> None:
    """Test that requirements.txt files with UTF-16 BE encoding (with BOM) are parsed correctly."""
    content = "click==8.1.3\ncolorama==0.4.5\n"
    with run_within_dir(tmp_path):
        # Write with BOM (\xfe\xff) followed by UTF-16 BE encoded content.
        Path("requirements.txt").write_bytes(b"\xfe\xff" + content.encode("utf-16-be"))

        dependencies_extract = RequirementsTxtDependencyGetter(Path("pyproject.toml")).get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 2
        assert dependencies[0].name == "click"
        assert dependencies[1].name == "colorama"


def test_parse_requirements_file_utf8_with_bom(tmp_path: Path) -> None:
    """Test that requirements.txt files with UTF-8 BOM are parsed correctly."""
    content = "click==8.1.3\ncolorama==0.4.5\n"
    with run_within_dir(tmp_path):
        Path("requirements.txt").write_bytes(content.encode("utf-8-sig"))

        dependencies_extract = RequirementsTxtDependencyGetter(Path("pyproject.toml")).get()
        dependencies = dependencies_extract.dependencies

        assert len(dependencies) == 2
        assert dependencies[0].name == "click"
        assert dependencies[1].name == "colorama"
