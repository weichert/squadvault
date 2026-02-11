from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Type


@dataclass(frozen=True, slots=True)
class ValidationError(Exception):
    """
    Deterministic, structured validation error.

    Phase 1 expects this symbol to exist.
    """
    message: str

    def __str__(self) -> str:
        return self.message


def require_non_empty_str(field_name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if value.strip() == "":
        raise ValueError(f"{field_name} must be non-empty")
    return value


def require_max_len(field_name: str, value: str, max_len: int) -> None:
    if len(value) > max_len:
        raise ValueError(f"{field_name} must be <= {max_len} chars")


def require_tuple(field_name: str, value: object) -> tuple:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    return value


def require_unique_items(field_name: str, items: Iterable[object]) -> None:
    seen: set[object] = set()
    for x in items:
        if x in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(x)


def require_enum_instance(field_name: str, value: object, enum_type: Type[Enum]) -> Enum:
    # Fail-closed: no coercion from strings.
    if not isinstance(value, enum_type):
        raise TypeError(f"{field_name} must be {enum_type.__name__}")
    return value  # type: ignore[return-value]


def require_optional_enum_instance(
    field_name: str, value: object, enum_type: Type[Enum]
) -> Optional[Enum]:
    if value is None:
        return None
    return require_enum_instance(field_name, value, enum_type)

def require_enum(field_name: str, value: object, enum_type: Type[Enum]) -> Enum:
    """
    Phase 1 compatibility shim.
    Fail-closed: requires an enum instance; does not coerce from strings.
    """
    return require_enum_instance(field_name, value, enum_type)


def require_optional_enum(field_name: str, value: object, enum_type: Type[Enum]) -> Optional[Enum]:
    """
    Phase 1 compatibility shim.
    """
    return require_optional_enum_instance(field_name, value, enum_type)

# -----------------------------
# Phase 1 compatibility helpers
# -----------------------------

def require_type(field_name: str, value: object, expected_type: type) -> object:
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} must be {expected_type.__name__}")
    return value


def require_str_max_len(field_name: str, value: object, max_len: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if len(value) > max_len:
        raise ValueError(f"{field_name} must be <= {max_len} chars")
    return value


def require_int_min(field_name: str, value: object, min_value: int) -> int:
    # bool is a subclass of int; reject it explicitly.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be int")
    if value < min_value:
        raise ValueError(f"{field_name} must be >= {min_value}")
    return value


def require_range_int(field_name: str, value: object, min_value: int, max_value: int) -> int:
    v = require_int_min(field_name, value, min_value)
    if v > max_value:
        raise ValueError(f"{field_name} must be <= {max_value}")
    return v


def require_iterable_max_len(field_name: str, value: object, max_len: int) -> object:
    # Deterministic: only checks __len__; no iteration side effects.
    if not hasattr(value, "__len__"):
        raise TypeError(f"{field_name} must be sized (have __len__)")
    if len(value) > max_len:  # type: ignore[arg-type]
        raise ValueError(f"{field_name} must have length <= {max_len}")
    return value


def require_enum(field_name: str, value: object, enum_type: Type[Enum]) -> Enum:
    # Fail-closed: do not coerce from strings.
    return require_enum_instance(field_name, value, enum_type)

# -----------------------------------------
# Phase 1 behavior overrides (raise ValidationError)
# -----------------------------------------

def _ve(msg: str) -> ValidationError:
    return ValidationError(msg)


def require_type(field_name: str, value: object, expected_type: type) -> object:
    if not isinstance(value, expected_type):
        raise _ve(f"{field_name} must be {expected_type.__name__}")
    return value


def require_str_max_len(field_name: str, value: object, max_len: int) -> str:
    if not isinstance(value, str):
        raise _ve(f"{field_name} must be str")
    if len(value) > max_len:
        raise _ve(f"{field_name} must be <= {max_len} chars")
    return value


def require_int_min(field_name: str, value: object, min_value: int) -> int:
    # bool is a subclass of int; reject it explicitly.
    if not isinstance(value, int) or isinstance(value, bool):
        raise _ve(f"{field_name} must be int")
    if value < min_value:
        raise _ve(f"{field_name} must be >= {min_value}")
    return value


def require_range_int(field_name: str, value: object, min_value: int, max_value: int) -> int:
    v = require_int_min(field_name, value, min_value)
    if v > max_value:
        raise _ve(f"{field_name} must be <= {max_value}")
    return v


def require_iterable_max_len(field_name: str, value: object, max_len: int) -> object:
    # Deterministic: only checks __len__; no iteration side effects.
    if not hasattr(value, "__len__"):
        raise _ve(f"{field_name} must be sized (have __len__)")
    if len(value) > max_len:  # type: ignore[arg-type]
        raise _ve(f"{field_name} must have length <= {max_len}")
    return value


def require_enum(field_name: str, value: object, enum_type: Type[Enum]) -> Enum:
    # Fail-closed: do not coerce from strings, but raise ValidationError (Phase 1 expectation).
    if not isinstance(value, enum_type):
        raise _ve(f"{field_name} must be {enum_type.__name__}")
    return value  # type: ignore[return-value]
