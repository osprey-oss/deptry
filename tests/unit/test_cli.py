from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from deptry.cli import (
    CommaSeparatedMappingParamType,
    CommaSeparatedTupleParamType,
    cli,
    display_deptry_version,
    set_debug_level,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping, Sequence
    from re import Pattern


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "",
            ("",),
            id="from empty str",
        ),
        pytest.param(
            "foo",
            ("foo",),
            id="from single str",
        ),
        pytest.param(
            "foo,bar",
            ("foo", "bar"),
            id="from multiple str",
        ),
        pytest.param(
            "foo, bar ",
            ("foo", "bar"),
            id="strips whitespace from multiple str",
        ),
        pytest.param(
            [],
            (),
            id="from empty list",
        ),
        pytest.param(
            ["foo"],
            ("foo",),
            id="from single item list",
        ),
        pytest.param(
            ["foo", "bar"],
            ("foo", "bar"),
            id="from multiple item list",
        ),
        pytest.param(
            (),
            (),
            id="from empty tuple",
        ),
        pytest.param(
            ("foo",),
            ("foo",),
            id="from single item tuple",
        ),
        pytest.param(
            ("foo", "bar"),
            ("foo", "bar"),
            id="from multiple item tuple",
        ),
    ],
)
def test_comma_separated_tuple_param_type_convert(
    value: str | list[str] | tuple[str, ...],
    expected: tuple[str, ...],
) -> None:
    """Tests all valid conversion paths."""
    param = mock.Mock(spec=click.Parameter)
    ctx = mock.Mock(spec=click.Context)

    actual = CommaSeparatedTupleParamType().convert(value=value, param=param, ctx=ctx)

    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "foo=bar",
            {"foo": ("bar",)},
            id="from str, single key, single value",
        ),
        pytest.param(
            "foo=bar|baz",
            {"foo": ("bar", "baz")},
            id="from str, single key, multi value",
        ),
        pytest.param(
            "foo=bar,fox=fuz",
            {"foo": ("bar",), "fox": ("fuz",)},
            id="from str, multi key, single value",
        ),
        pytest.param(
            "foo=bar | baz, fox = fuz",
            {"foo": ("bar", "baz"), "fox": ("fuz",)},
            id="strips whitespace from keys and values",
        ),
        pytest.param(
            "foo=bar,foo=fuz",
            {"foo": ("bar", "fuz")},
            id="from str, redefined key, single value",
        ),
        pytest.param(
            {"foo": "bar"},
            {"foo": ("bar",)},
            id="from str-to-str map",
        ),
        pytest.param(
            "foo|bar=baz",
            {"foo|bar": ("baz",)},
            id="from str, key with multiple-value separator token",
        ),
        pytest.param(
            "foo=bar=baz",
            {"foo": ("bar=baz",)},
            id="from str, single value with key-value seperator token",
        ),
        pytest.param(
            "foo=",
            {"foo": ("",)},
            id="from str, empty value",
        ),
        pytest.param(
            {"foo": ("bar",)},
            {"foo": ("bar",)},
            id="from str-to-tuple-of-str map",
        ),
        pytest.param(
            {"foo": ("bar",), "bar": "baz"},
            {"foo": ("bar",), "bar": ("baz",)},
            id="from str-to-mixed map",
        ),
    ],
)
def test_comma_separated_mapping_param_type_convert(
    value: str | MutableMapping[str, Sequence[str] | str],
    expected: MutableMapping[str, tuple[str, ...]],
) -> None:
    """Tests all valid conversion paths."""
    param = mock.Mock(spec=click.Parameter)
    ctx = mock.Mock(spec=click.Context)

    actual = CommaSeparatedMappingParamType().convert(value=value, param=param, ctx=ctx)

    assert actual == expected


@pytest.mark.parametrize(
    ("value", "err_type", "err_msg_matcher"),
    [
        pytest.param(
            "",
            ValueError,
            re.compile(r"equal sign"),
            id="from empty str",
        ),
        pytest.param(
            "foo,bar=baz",
            ValueError,
            re.compile(r"equal sign"),
            id="from invalid first item",
        ),
    ],
)
def test_comma_separated_mapping_param_type_convert_err(
    value: str | MutableMapping[str, Sequence[str] | str],
    err_type: type[Exception],
    err_msg_matcher: Pattern[str] | str,
) -> None:
    """Tests some invalid conversion paths."""
    param = mock.Mock(spec=click.Parameter)
    ctx = mock.Mock(spec=click.Context)
    param_type = CommaSeparatedMappingParamType()

    with pytest.raises(err_type, match=err_msg_matcher):
        param_type.convert(value=value, param=param, ctx=ctx)


def test_display_deptry_version(capsys: pytest.CaptureFixture[str]) -> None:
    ctx = mock.Mock(resilient_parsing=False, spec=click.Context)
    param = mock.Mock(spec=click.Parameter)

    with patch("deptry.cli.version", return_value="1.2.3"):
        display_deptry_version(ctx, param, True)

    assert capsys.readouterr().out == "deptry 1.2.3\n"


@pytest.mark.parametrize(
    ("resilient_parsing", "value"),
    [
        (
            False,
            False,
        ),
        (
            True,
            False,
        ),
        (
            True,
            True,
        ),
    ],
)
def test_display_deptry_version_none(resilient_parsing: bool, value: bool, capsys: pytest.CaptureFixture[str]) -> None:
    ctx = mock.Mock(resilient_parsing=resilient_parsing, spec=click.Context)
    param = mock.Mock(spec=click.Parameter)

    display_deptry_version(ctx, param, value)
    assert capsys.readouterr().out == ""


def test_set_debug_level_verbose() -> None:
    ctx = mock.Mock(spec=click.Context)
    param = mock.Mock(spec=click.Parameter)

    with mock.patch("logging.Logger.setLevel") as mock_set_level:
        set_debug_level(ctx, param, True)
        mock_set_level.assert_called_with(logging.DEBUG)


def test_set_debug_level_not_verbose() -> None:
    ctx = mock.Mock(spec=click.Context)
    param = mock.Mock(spec=click.Parameter)

    with mock.patch("logging.Logger.setLevel") as mock_set_level:
        set_debug_level(ctx, param, False)
        mock_set_level.assert_not_called()


def test_deprecated_arguments(caplog: pytest.LogCaptureFixture) -> None:
    with mock.patch("deptry.core.Core.run"):
        result = CliRunner().invoke(cli, ". --pep621-dev-dependency-groups dev")

    assert result.exit_code == 0
    assert (
        "Warning: In an upcoming release, support for the `--pep621-dev-dependency-groups` command-line option and the `pep621_dev_dependency_groups` configuration parameter will be discontinued. Instead, use `--optional-dependencies-dev-groups` or `optional_dependencies_dev_groups` under the `[tool.deptry]` section in pyproject.toml."
        in caplog.text
    )


def test_deprecated_options(caplog: pytest.LogCaptureFixture) -> None:
    with mock.patch("deptry.core.Core.run"):
        result = CliRunner().invoke(cli, ". --config tests/fixtures/deprecated_options/pyproject.toml")

    assert result.exit_code == 0
    assert (
        "Warning: In an upcoming release, support for the `--pep621-dev-dependency-groups` command-line option and the `pep621_dev_dependency_groups` configuration parameter will be discontinued. Instead, use `--optional-dependencies-dev-groups` or `optional_dependencies_dev_groups` under the `[tool.deptry]` section in pyproject.toml."
        in caplog.text
    )


def test_deprecated_conflict(caplog: pytest.LogCaptureFixture) -> None:
    with mock.patch("deptry.core.Core.run"):
        result = CliRunner().invoke(cli, ". --pep621-dev-dependency-groups dev --optional-dependencies-dev-groups dev")

    assert result.exit_code == 2
    assert (
        "Error: Cannot use both `--pep621-dev-dependency-groups` and `--optional-dependencies-dev-groups`. Only use the latter, as the former is deprecated."
        in caplog.text
    )
