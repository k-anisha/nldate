from datetime import date

import pytest

from nldate import parse


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("2025-12-01", date(2025, 12, 1)),
        ("December 1, 2025", date(2025, 12, 1)),
        ("Dec 1, 2025", date(2025, 12, 1)),
        ("12/01/2025", date(2025, 12, 1)),
        ("Dec. 1, 2025", date(2025, 12, 1)),
        ("2 years, 3 months before Dec. 1, 2025", date(2023, 9, 1)),
    ],
)
def test_absolute_dates(input_string, expected):
    assert parse(input_string) == expected


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("today", date(2025, 12, 1)),
        ("tomorrow", date(2025, 12, 2)),
        ("yesterday", date(2025, 11, 30)),
        ("in 3 days", date(2025, 12, 4)),
        ("3 days ago", date(2025, 11, 28)),
        ("2 weeks from today", date(2025, 12, 15)),
    ],
)
def test_relative_dates(input_string, expected):
    assert parse(input_string, today=date(2025, 12, 1)) == expected


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("next Tuesday", date(2025, 12, 2)),
        ("next Monday", date(2025, 12, 8)),
        ("next Friday", date(2025, 12, 5)),
    ],
)
def test_weekdays(input_string, expected):
    assert parse(input_string, today=date(2025, 12, 1)) == expected


@pytest.mark.parametrize(
    "input_string, expected",
    [
        (
            "5 days before December 1st, 2025",
            date(2025, 11, 26),
        ),
        (
            "1 year and 2 months after yesterday",
            date(2027, 1, 30),
        ),
        (
            "2 weeks from tomorrow",
            date(2025, 12, 16),
        ),
    ],
)
def test_before_after(input_string, expected):
    assert parse(input_string, today=date(2025, 12, 1)) == expected


@pytest.mark.parametrize(
    "input_string",
    [
        "",
        "hello",
        "not a date",
        "yesterdayish",
        "32/32/2025",
    ],
)
def test_invalid_inputs(input_string):
    with pytest.raises(ValueError):
        parse(input_string, today=date(2025, 12, 1))


def test_default_today():
    from datetime import timedelta

    expected = date.today() + timedelta(days=1)
    assert parse("tomorrow") == expected
