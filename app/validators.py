"""Server-side input validation helpers.

Each helper returns the cleaned value, or raises ValidationError with a
user-facing message that the route flashes back to the form.
"""

import datetime
import re
from decimal import Decimal, InvalidOperation


class ValidationError(ValueError):
    """Raised when a submitted form value fails validation."""


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
REG_NO_RE = re.compile(r"^[0-9]{2}[A-Z]{3}[0-9]{4}$")          # e.g. 25BAI0077
EMPLOYEE_CODE_RE = re.compile(r"^[A-Z]{2,5}[0-9]{3,6}$")       # e.g. EMP1001
COURSE_CODE_RE = re.compile(r"^[A-Z]{2,6}[0-9]{3,5}$")         # e.g. CSE2005
INVOICE_NO_RE = re.compile(r"^[A-Z0-9-]{3,20}$")               # e.g. INV-2026-005
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,50}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{0,49}$")
PHONE_RE = re.compile(r"^[0-9]{10}$")


def required_text(value, label, max_len, pattern=None, hint=None):
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{label} is required.")
    if len(value) > max_len:
        raise ValidationError(f"{label} must be at most {max_len} characters.")
    if pattern is not None and not pattern.match(value):
        raise ValidationError(f"{label} '{value}' is not valid" + (f" (expected {hint})." if hint else "."))
    return value


def integer(value, label, min_value=None, max_value=None):
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a whole number.")
    if min_value is not None and number < min_value:
        raise ValidationError(f"{label} must be at least {min_value}.")
    if max_value is not None and number > max_value:
        raise ValidationError(f"{label} must be at most {max_value}.")
    return number


def optional_id(value, label):
    if value in (None, "", "None"):
        return None
    return integer(value, label, min_value=1)


def money(value, label, min_value=Decimal("0.00"), max_value=Decimal("99999999.99")):
    try:
        amount = Decimal(str(value).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{label} must be a valid amount.")
    if amount < min_value:
        raise ValidationError(f"{label} cannot be less than ₹{min_value:,.2f}.")
    if amount > max_value:
        raise ValidationError(f"{label} cannot exceed ₹{max_value:,.2f}.")
    return amount


def decimal_range(value, label, min_value, max_value):
    try:
        number = Decimal(str(value).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{label} must be a number.")
    if not (Decimal(min_value) <= number <= Decimal(max_value)):
        raise ValidationError(f"{label} must be between {min_value} and {max_value}.")
    return number


def iso_date(value, label, not_after=None, not_before=None):
    try:
        day = datetime.date.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a valid date (YYYY-MM-DD).")
    if not_after is not None and day > not_after:
        raise ValidationError(f"{label} cannot be after {not_after.isoformat()}.")
    if not_before is not None and day < not_before:
        raise ValidationError(f"{label} cannot be before {not_before.isoformat()}.")
    return day


def choice(value, label, allowed):
    value = (value or "").strip()
    if value not in allowed:
        raise ValidationError(f"{label} must be one of: {', '.join(allowed)}.")
    return value


def password(value):
    value = value or ""
    if len(value) < 6:
        raise ValidationError("Password must be at least 6 characters.")
    if len(value) > 255:
        raise ValidationError("Password must be at most 255 characters.")
    return value


def like_pattern(term):
    """Escapes LIKE wildcards in a search term and wraps it for a contains-match."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
