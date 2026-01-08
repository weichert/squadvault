from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import requests

from squadvault.utils.http import http_request_with_retries

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self, api_key: str, notion_version: str = "2022-06-28") -> None:
        self.api_key = api_key
        self.notion_version = notion_version
        self.base_url = "https://api.notion.com/v1"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Notion-Version": self.notion_version,
                "Content-Type": "application/json",
            }
        )

    def get_database(self, database_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{database_id}"
        resp = http_request_with_retries(self.session, "GET", url)
        return resp.json()

    def query_database(
        self,
        database_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{database_id}/query"
        payload: Dict[str, Any] = {"page_size": page_size}
        if filter_obj:
            payload["filter"] = filter_obj
        if start_cursor:
            payload["start_cursor"] = start_cursor
        resp = http_request_with_retries(self.session, "POST", url, json=payload)
        return resp.json()

    def query_by_property_equals(
        self,
        database_id: str,
        property_name: str,
        property_type: str,
        value: Any,
    ) -> Dict[str, Any]:
        """
        property_type must be one of: title, rich_text, number, select, url, checkbox
        """
        if property_type == "title":
            filter_obj = {"property": property_name, "title": {"equals": str(value)}}
        elif property_type == "rich_text":
            filter_obj = {"property": property_name, "rich_text": {"equals": str(value)}}
        elif property_type == "number":
            filter_obj = {"property": property_name, "number": {"equals": float(value)}}
        elif property_type == "select":
            filter_obj = {"property": property_name, "select": {"equals": str(value)}}
        elif property_type == "url":
            filter_obj = {"property": property_name, "url": {"equals": str(value)}}
        elif property_type == "checkbox":
            filter_obj = {"property": property_name, "checkbox": {"equals": bool(value)}}
        else:
            raise ValueError(f"Unsupported property_type for equals query: {property_type}")
        return self.query_database(database_id=database_id, filter_obj=filter_obj, page_size=100)

    def create_page(self, parent_database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/pages"
        payload = {"parent": {"database_id": parent_database_id}, "properties": properties}
        resp = http_request_with_retries(self.session, "POST", url, json=payload)
        return resp.json()

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/pages/{page_id}"
        payload = {"properties": properties}
        resp = http_request_with_retries(self.session, "PATCH", url, json=payload)
        return resp.json()

    def upsert_by_title_key(
        self,
        database_id: str,
        title_property_name: str,
        key_value: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Idempotent upsert where the Notion database Title property is the key field.
        - Looks up pages where title_property_name == key_value
        - Updates if found; creates if not found
        """
        q = self.query_by_property_equals(
            database_id=database_id,
            property_name=title_property_name,
            property_type="title",
            value=key_value,
        )
        results = q.get("results", [])
        if results:
            page_id = results[0]["id"]
            logger.debug("Upsert: update existing page %s in db=%s key=%s", page_id, database_id, key_value)
            return self.update_page(page_id=page_id, properties=properties)

        logger.debug("Upsert: create new page in db=%s key=%s", database_id, key_value)
        # Ensure the title property is set to the key_value deterministically.
        props_with_key = dict(properties)
        if title_property_name not in props_with_key:
            # Caller may provide it; if not, enforce it here.
            props_with_key[title_property_name] = {
                "title": [{"type": "text", "text": {"content": key_value}}]
            }
        return self.create_page(parent_database_id=database_id, properties=props_with_key)
