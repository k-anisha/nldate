import calendar
import re
from datetime import date, timedelta

NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
}

MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
MONTHS.update(
    {name.lower(): index for index, name in enumerate(calendar.month_abbr) if name}
)

WEEKDAYS = {name.lower(): index for index, name in enumerate(calendar.day_name)}

UNITS = {
    "day": "days",
    "days": "days",
    "week": "weeks",
    "weeks": "weeks",
    "month": "months",
    "months": "months",
    "year": "years",
    "years": "years",
}


def _number(value: str) -> int:
    """Convert a numeric string or number word to an integer."""
    if value.isdigit():
        return int(value)

    if value in NUMBER_WORDS:
        return NUMBER_WORDS[value]

    raise ValueError(f"Unrecognized number: {value}")


def _add_months(current: date, months: int) -> date:
    """Add months while clamping to the last valid day."""
    month_index = current.month - 1 + months
    year = current.year + month_index // 12
    month = month_index % 12 + 1

    last_day = calendar.monthrange(year, month)[1]
    day = min(current.day, last_day)

    return date(year, month, day)


def _add_unit(current: date, amount: int, unit: str) -> date:
    """Add or subtract a date unit."""
    if unit == "days":
        return current + timedelta(days=amount)

    if unit == "weeks":
        return current + timedelta(weeks=amount)

    if unit == "months":
        return _add_months(current, amount)

    if unit == "years":
        return _add_months(current, amount * 12)

    raise ValueError(f"Unknown unit: {unit}")


def _parse_absolute(s: str) -> date:
    """Parse common absolute date formats."""
    s = s.replace(".", "")
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            return (
                date.fromisoformat(s)
                if fmt == "%Y-%m-%d"
                else (__import__("datetime").datetime.strptime(s, fmt).date())
            )
        except ValueError:
            continue

    raise ValueError(f"Unrecognized date: {s}")


def _parse_expression(s: str, today: date) -> date:
    """Parse a relative date expression."""
    s = s.strip().lower()

    if s in ("today", "now"):
        return today

    if s == "tomorrow":
        return today + timedelta(days=1)

    if s == "yesterday":
        return today - timedelta(days=1)

    if s in WEEKDAYS:
        target = WEEKDAYS[s]
        difference = (target - today.weekday()) % 7
        return today + timedelta(days=difference)

    for prefix, direction in [
        ("next ", 1),
        ("last ", -1),
        ("this ", 0),
    ]:
        if s.startswith(prefix) and s[len(prefix) :] in WEEKDAYS:
            target = WEEKDAYS[s[len(prefix) :]]
            difference = (target - today.weekday()) % 7

            if direction == 1 and difference == 0:
                difference = 7
            elif direction == -1:
                difference = difference - 7 if difference else -7

            return today + timedelta(days=difference)

    # Expressions such as "5 days before tomorrow"
    for connector in (" before ", " after ", " from "):
        if connector in s:
            left, right = s.split(connector, 1)

            if connector == " before ":
                return _apply_quantities(
                    _parse_expression(right, today),
                    left,
                    -1,
                )

            if connector == " after ":
                return _apply_quantities(
                    _parse_expression(right, today),
                    left,
                    1,
                )

            # "2 weeks from tomorrow"
            try:
                return _apply_quantities(
                    _parse_expression(right, today),
                    left,
                    1,
                )
            except ValueError:
                pass

    # Expressions such as "in 5 days" and "3 days ago"
    if s.startswith("in "):
        return _apply_quantities(today, s[3:], 1)

    if s.endswith(" ago"):
        return _apply_quantities(today, s[:-4], -1)

    # Absolute dates, including ordinal suffixes
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", s)
    return _parse_absolute(cleaned)


def _apply_quantities(
    current: date,
    expression: str,
    direction: int,
) -> date:
    """Apply one or more date quantities to a date."""
    expression = expression.strip().lower()

    pattern = re.compile(r"(\d+|[a-z]+)\s+" r"(days?|weeks?|months?|years?)")

    matches = list(pattern.finditer(expression))

    if not matches:
        raise ValueError(f"Invalid date quantity: {expression}")

    remaining = list(expression)

    for match in reversed(matches):
        start, end = match.span()
        remaining[start:end] = [" "] * (end - start)

    leftovers = "".join(remaining)
    leftovers = re.sub(r"\band\b|,", "", leftovers).strip()

    if leftovers:
        raise ValueError(f"Invalid date quantity: {expression}")

    for match in matches:
        amount = _number(match.group(1)) * direction
        unit = UNITS[match.group(2)]
        current = _add_unit(current, amount, unit)

    return current


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date into a datetime.date object."""
    if not isinstance(s, str) or not s.strip():
        raise ValueError("Date input must be a nonempty string")

    reference = today if today is not None else date.today()

    try:
        return _parse_expression(s.strip(), reference)
    except (OverflowError, TypeError) as exc:
        raise ValueError(f"Invalid date: {s}") from exc
