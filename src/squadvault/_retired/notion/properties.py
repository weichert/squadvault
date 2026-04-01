"""Notion property value builders for page creation and updates."""

from __future__ import annotations

from typing import Any


def prop_title(text: str) -> dict[str, Any]:
    """Build a Notion title property value."""
    return {"title": [{"type": "text", "text": {"content": text}}]}


def prop_rich_text(text: str) -> dict[str, Any]:
    """Build a Notion rich text property value."""
    if text is None:
        text = ""
    return {"rich_text": [{"type": "text", "text": {"content": str(text)}}]}


def prop_number(num: float | int | None) -> dict[str, Any]:
    """Build a Notion number property value."""
    return {"number": None if num is None else float(num)}


def prop_select(name: str | None) -> dict[str, Any]:
    """Build a Notion select property value."""
    return {"select": None if not name else {"name": name}}


def prop_url(url: str | None) -> dict[str, Any]:
    """Build a Notion URL property value."""
    return {"url": None if not url else str(url)}


def prop_checkbox(value: bool) -> dict[str, Any]:
    """Build a Notion checkbox property value."""
    return {"checkbox": bool(value)}


def prop_relation(page_ids: list[str] | None) -> dict[str, Any]:
    """Build a Notion relation property value."""
    page_ids = page_ids or []
    return {"relation": [{"id": pid} for pid in page_ids]}


def prop_date_iso(iso_z: str | None) -> dict[str, Any]:
    """
    Notion date type.
    Provide an ISO 8601 string (ideally Zulu), e.g. 2024-09-08T03:14:15Z
    """
    return {"date": None if not iso_z else {"start": iso_z}}
