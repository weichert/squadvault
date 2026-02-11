from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Type


class ValidationError(ValueError):
    """Deterministic validation error for PFL broadcast data-layer objects."""


def require_type(name: str, value: Any, expected_type: Type[Any]) -> None:
    if not isinstance(value, expected_type):
        raise ValidationError(f"{name} must be {expected_type.__name__}")


def require_enum(name: str, value: Any, enum_type: Type[Enum]) -> None:
    if not isinstance(value, enum_type):
        raise ValidationError(f"{name} must be a {enum_type.__name__} enum value")


def require_int_min(name: str, value: int, min_value: int) -> None:
    if value < min_value:
        raise ValidationError(f"{name} must be >= {min_value}")


def require_str_max_len(name: str, value: str, max_len: int) -> None:
    if len(value) > max_len:
        raise ValidationError(f"{name} length must be <= {max_len}")


def require_iterable_max_len(name: str, values: Iterable[Any], max_len: int) -> None:
    n = 0
    for _ in values:
        n += 1
        if n > max_len:
            raise ValidationError(f"{name} length must be <= {max_len}")


def require_range_int(name: str, value: int, min_value: int, max_value: int) -> None:
    if value < min_value or value > max_value:
        raise ValidationError(f"{name} must be between {min_value} and {max_value}")
