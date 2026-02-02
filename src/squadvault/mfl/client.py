from __future__ import annotations

import logging
from typing import Any, Dict
import requests

from squadvault.utils.http import http_request_with_retries

logger = logging.getLogger(__name__)


class MflClient:
    """
    Minimal MFL client for v1 ingestion.

    Notes:
    - `server` may be provided as:
        * "www03"
        * "03"
        * "44"
        * "www03.myfantasyleague.com"
      All forms are normalized safely.
    - Host discovery via redirect is intentionally NOT implemented yet
      (explicit config is the current contract).
    """

    def __init__(
        self,
        server: str,
        league_id: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.server = server
        self.league_id = league_id
        self.username = username
        self.password = password
        self.session = requests.Session()

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _host(self) -> str:
        """
        Normalize the MFL host.

        Accepts either:
        - "www03"
        - "03"
        - "44"
        - "www03.myfantasyleague.com"

        Always returns a valid hostname like:
        - "www03.myfantasyleague.com"
        """
        raw = (self.server or "").strip()

        if not raw:
            # Historical default; should almost never be hit in practice
            raw = "44"

        # Already a full hostname
        if "myfantasyleague.com" in raw:
            return raw

        # Ensure www-prefix for numeric shards like "03" or "44"
        if raw.isdigit():
            raw = f"www{raw}"

        return f"{raw}.myfantasyleague.com"

    # ----------------------------
    # URL builders
    # ----------------------------

    def export_url(self, year: int, export_type: str) -> str:
        host = self._host()
        return (
            f"https://{host}/{year}/export"
            f"?TYPE={export_type}&L={self.league_id}&JSON=1"
        )

    def _login_url(self, year: int) -> str:
        host = self._host()
        return f"https://{host}/{year}/login"

    # ----------------------------
    # API calls
    # ----------------------------

    def get_transactions(self, year: int) -> tuple[Dict[str, Any], str]:
        """
        Fetch transactions export for a given year.

        v1 behavior:
        - Attempt unauthenticated request first
        - If non-200 and creds exist, attempt login and retry once
        """
        url = self.export_url(year, "transactions")
        resp = http_request_with_retries(self.session, "GET", url)

        if resp.status_code != 200 and self.username and self.password:
            logger.info(
                "MFL unauthenticated request failed (%s); attempting login then retry.",
                resp.status_code,
            )
            self._login(year)
            resp = http_request_with_retries(self.session, "GET", url)

        resp.raise_for_status()
        return resp.json(), url

    def _login(self, year: int) -> None:
        """
        Best-effort login for leagues requiring authentication.

        Intentionally minimal for v1.
        """
        if not (self.username and self.password):
            return

        login_url = self._login_url(year)
        payload = {
            "USERNAME": self.username,
            "PASSWORD": self.password,
            "XML": "1",
        }

        http_request_with_retries(
            self.session,
            "POST",
            login_url,
            data=payload,
        )
       
