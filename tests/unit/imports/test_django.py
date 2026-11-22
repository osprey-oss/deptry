from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from deptry.imports.django import get_imported_modules_from_django
from deptry.imports.location import Location

if TYPE_CHECKING:
    from pathlib import Path


def _write(root: Path, files: dict[str, str]) -> None:
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(source), encoding="utf-8")


def test_installed_apps_list(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                INSTALLED_APPS = [
                    "django.contrib.admin",
                    "rest_framework",
                    "corsheaders.apps.CorsHeadersConfig",
                ]
                """
        },
    )

    settings = tmp_path / "settings.py"

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "django": [Location(settings, 2, 5)],
        "rest_framework": [Location(settings, 3, 5)],
        "corsheaders": [Location(settings, 4, 5)],
    }


def test_installed_apps_tuple_and_annotation(tmp_path: Path) -> None:
    _write(tmp_path, {"settings.py": 'INSTALLED_APPS: tuple[str, ...] = ("django.contrib.auth", "polls")\n'})

    settings = tmp_path / "settings.py"

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "django": [Location(settings, 1, 36)],
        "polls": [Location(settings, 1, 59)],
    }


def test_installed_apps_missing(tmp_path: Path) -> None:
    _write(tmp_path, {"settings.py": "DEBUG = True\n"})

    assert get_imported_modules_from_django("settings", tmp_path) == {}


def test_only_nonempty_dotted_identifiers_are_kept(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                INSTALLED_APPS = [
                    "",
                    "not an app",
                    "has-dash",
                    "double..dot",
                    "class.def",
                    ".leading",
                    "trailing.",
                    "1numeric",
                    42,
                    b"bytes",
                    f"fstring",
                    "valid.name",
                ]
                """
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "valid": [Location(tmp_path / "settings.py", 13, 5)],
    }


def test_non_ascii_column_is_measured_in_characters(tmp_path: Path) -> None:
    _write(tmp_path, {"settings.py": 'INSTALLED_APPS = ["é-x", "polls"]\n'})

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "polls": [Location(tmp_path / "settings.py", 1, 26)],
    }


def test_package_is_preferred_over_module(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings/__init__.py": 'INSTALLED_APPS = ["from_package"]\n',
            "settings.py": 'INSTALLED_APPS = ["from_module"]\n',
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["from_package"]


def test_dotted_settings_module(tmp_path: Path) -> None:
    _write(tmp_path, {"config/settings/production.py": 'INSTALLED_APPS = ["polls"]\n'})

    assert get_imported_modules_from_django("config.settings.production", tmp_path) == {
        "polls": [Location(tmp_path / "config/settings/production.py", 1, 19)],
    }


def test_last_assignment_wins(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                INSTALLED_APPS = ["first"]
                INSTALLED_APPS = ["second"]
                """
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["second"]


def test_concatenation_of_names_and_displays(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                DJANGO_APPS = ["django.contrib.auth"]
                LOCAL_APPS = ("polls",)
                INSTALLED_APPS = DJANGO_APPS + ["rest_framework"] + ["corsheaders"]
                OTHER = LOCAL_APPS + ("blog",)
                """
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["django", "rest_framework", "corsheaders"]


def test_concatenation_of_different_sequence_kinds_is_unknown(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                INSTALLED_APPS = ["kept_then_lost"]
                INSTALLED_APPS = ["polls"] + ("blog",)
                """
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {}


def test_list_augmented_assignment_mutates_shared_list(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                BASE = ["django.contrib.auth"]
                INSTALLED_APPS = BASE
                INSTALLED_APPS += ("polls",)
                BASE += ["blog"]
                """
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["django", "polls", "blog"]


def test_tuple_augmented_assignment_rebinds_target_only(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                BASE = ("django.contrib.auth",)
                INSTALLED_APPS = BASE
                INSTALLED_APPS += ("polls",)
                """
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["django", "polls"]

    _write(
        tmp_path,
        {
            "settings.py": """\
                BASE = ("django.contrib.auth",)
                INSTALLED_APPS = BASE
                INSTALLED_APPS += ("polls",)
                INSTALLED_APPS = BASE
                """
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["django"]


def test_tuple_augmented_with_list_is_unknown(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                INSTALLED_APPS = ("django.contrib.auth",)
                INSTALLED_APPS += ["polls"]
                """
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {}


def test_unsupported_update_invalidates_binding(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                INSTALLED_APPS = ["django.contrib.auth"]
                INSTALLED_APPS += get_extra_apps()
                """
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {}


@pytest.mark.parametrize(
    "source",
    [
        'INSTALLED_APPS = [app for app in ["polls"]]\n',
        'INSTALLED_APPS = list(["polls"])\n',
        'INSTALLED_APPS = ["polls"] * 2\n',
        'INSTALLED_APPS = ["polls"]\nINSTALLED_APPS -= ["polls"]\n',
        'if True:\n    INSTALLED_APPS = ["polls"]\n',
        'def configure():\n    INSTALLED_APPS = ["polls"]\n',
        'class Settings:\n    INSTALLED_APPS = ["polls"]\n',
        'INSTALLED_APPS = ["polls"]\ndef INSTALLED_APPS():\n    pass\n',
        'INSTALLED_APPS = ["polls"]\nimport INSTALLED_APPS\n',
        "from base import *\n",
    ],
)
def test_unsupported_constructs_yield_no_references(tmp_path: Path, source: str) -> None:
    _write(tmp_path, {"settings.py": source, "base.py": 'INSTALLED_APPS = ["inherited"]\n'})

    assert get_imported_modules_from_django("settings", tmp_path) == {}


def test_repeated_app_reference_at_same_location_is_reported_once(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings.py": """\
                BASE = ["django.contrib.auth"]
                INSTALLED_APPS = BASE + BASE
                """
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "django": [Location(tmp_path / "settings.py", 1, 9)],
    }


def test_apps_with_same_top_level_module_keep_each_location(tmp_path: Path) -> None:
    _write(tmp_path, {"settings.py": 'INSTALLED_APPS = ["django.contrib.auth", "django.contrib.admin"]\n'})

    settings = tmp_path / "settings.py"

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "django": [Location(settings, 1, 19), Location(settings, 1, 42)],
    }


def test_absolute_import_between_local_modules(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "base.py": """\
                APPS = ["django.contrib.auth"]
                OTHER = ["unused"]
                """,
            "settings.py": """\
                from base import APPS as BASE_APPS
                INSTALLED_APPS = BASE_APPS + ["polls"]
                """,
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "django": [Location(tmp_path / "base.py", 1, 9)],
        "polls": [Location(tmp_path / "settings.py", 2, 31)],
    }


def test_relative_imports(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "site/__init__.py": "",
            "site/common.py": 'COMMON = ["django.contrib.auth"]\n',
            "site/settings/__init__.py": "",
            "site/settings/base.py": """\
                from ..common import COMMON
                from . import sibling
                BASE = COMMON + ["polls"]
                """,
            "site/settings/dev.py": """\
                from .base import BASE
                INSTALLED_APPS = BASE + ["debug_toolbar"]
                """,
        },
    )

    assert get_imported_modules_from_django("site.settings.dev", tmp_path) == {
        "django": [Location(tmp_path / "site/common.py", 1, 11)],
        "polls": [Location(tmp_path / "site/settings/base.py", 3, 18)],
        "debug_toolbar": [Location(tmp_path / "site/settings/dev.py", 2, 26)],
    }


def test_relative_import_in_package_init(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "settings/__init__.py": """\
                from .base import INSTALLED_APPS
                INSTALLED_APPS += ["debug_toolbar"]
                """,
            "settings/base.py": 'INSTALLED_APPS = ["polls"]\n',
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {
        "polls": [Location(tmp_path / "settings/base.py", 1, 19)],
        "debug_toolbar": [Location(tmp_path / "settings/__init__.py", 2, 20)],
    }


def test_imported_list_is_shared_with_its_source_module(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "base.py": 'INSTALLED_APPS = ["polls"]\n',
            "settings.py": """\
                from base import INSTALLED_APPS
                INSTALLED_APPS += ["debug_toolbar"]
                """,
            "other.py": """\
                from base import INSTALLED_APPS
                """,
        },
    )

    assert list(get_imported_modules_from_django("other", tmp_path)) == ["polls"]
    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["polls", "debug_toolbar"]


@pytest.mark.parametrize(
    "source",
    [
        "from missing import APPS\nINSTALLED_APPS = APPS\n",
        "from base import MISSING\nINSTALLED_APPS = MISSING\n",
        "from .. import APPS\nINSTALLED_APPS = APPS\n",
        "from base import APPS\nINSTALLED_APPS = APPS\n",
        "from invalid import APPS\nINSTALLED_APPS = APPS\n",
        "from base import *\nINSTALLED_APPS = APPS\n",
        "import base\nINSTALLED_APPS = base.APPS\n",
    ],
)
def test_unresolvable_import_yields_unknown_binding(tmp_path: Path, source: str) -> None:
    _write(
        tmp_path,
        {
            "settings.py": source,
            "base.py": 'APPS = ["polls"] + get_more()\n',
            "invalid.py": "APPS = [\n",
        },
    )

    assert get_imported_modules_from_django("settings", tmp_path) == {}


def test_import_cycle_contributes_unknown_binding(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "a.py": """\
                from b import B_APPS
                A_APPS = ["from_a"]
                INSTALLED_APPS = A_APPS + B_APPS
                """,
            "b.py": """\
                from a import A_APPS
                B_APPS = ["from_b"]
                OTHER = A_APPS + ["extra"]
                """,
        },
    )

    assert get_imported_modules_from_django("a", tmp_path) == {
        "from_a": [Location(tmp_path / "a.py", 2, 11)],
        "from_b": [Location(tmp_path / "b.py", 2, 11)],
    }


def test_settings_outside_of_root_are_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "project"
    _write(
        tmp_path,
        {
            "outside.py": 'APPS = ["outside"]\n',
            "project/settings.py": "from outside import APPS\nINSTALLED_APPS = APPS\n",
        },
    )

    assert get_imported_modules_from_django("settings", root) == {}


def test_symlink_pointing_outside_of_root_is_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "project"
    _write(tmp_path, {"outside.py": 'INSTALLED_APPS = ["outside"]\n', "project/placeholder.py": ""})
    try:
        (root / "settings.py").symlink_to(tmp_path / "outside.py")
    except OSError:
        pytest.skip("symlinks are not available")

    with pytest.raises(FileNotFoundError):
        get_imported_modules_from_django("settings", root)


def test_settings_are_not_executed(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    _write(
        tmp_path,
        {
            "settings.py": f"""\
                from pathlib import Path
                Path({str(marker)!r}).touch()
                INSTALLED_APPS = ["polls"]
                """
        },
    )

    assert list(get_imported_modules_from_django("settings", tmp_path)) == ["polls"]
    assert not marker.exists()


def test_missing_settings_module(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match=r"Cannot locate Django settings module 'settings' beneath"):
        get_imported_modules_from_django("settings", tmp_path)


def test_invalid_settings_module_name(tmp_path: Path) -> None:
    _write(tmp_path, {"settings.py": 'INSTALLED_APPS = ["polls"]\n'})

    with pytest.raises(FileNotFoundError):
        get_imported_modules_from_django("../settings", tmp_path)


def test_settings_module_with_syntax_error(tmp_path: Path) -> None:
    _write(tmp_path, {"settings.py": "INSTALLED_APPS = [\n"})

    with pytest.raises(SyntaxError):
        get_imported_modules_from_django("settings", tmp_path)
