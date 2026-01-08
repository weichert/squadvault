from __future__ import annotations

from typing import Any, Dict, List, Optional


def prop_title(text: str) -> Dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": text}}]}


def prop_rich_text(text: str) -> Dict[str, Any]:
    if text is None:
        text = ""
    return {"rich_text": [{"type": "text", "text": {"content": str(text)}}]}


def prop_number(num: float | int | None) -> Dict[str, Any]:
    return {"number": None if num is None else float(num)}


def prop_select(name: str | None) -> Dict[str, Any]:
    return {"select": None if not name else {"name": name}}


def prop_url(url: str | None) -> Dict[str, Any]:
    return {"url": None if not url else str(url)}


def prop_checkbox(value: bool) -> Dict[str, Any]:
    return {"checkbox": bool(value)}


def prop_relation(page_ids: List[str] | None) -> Dict[str, Any]:
    page_ids = page_ids or []
    return {"relation": [{"id": pid} for pid in page_ids]}


def prop_date_iso(iso_z: str | None) -> Dict[str, Any]:
    """
    Notion date type.
    Provide an ISO 8601 string (ideally Zulu), e.g. 2024-09-08T03:14:15Z
    """
    return {"date": None if not iso_z else {"start": iso_z}}
