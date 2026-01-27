from __future__ import annotations

import sqlite3
from typing import List, Sequence

from squadvault.chronicle.input_contract_v1 import ApprovedRecapRefV1


def load_latest_approved_recap_refs_v1(
    *,
    db_path: str,
    league_id: int,
    season: int,
    artifact_type: str,
    week_indices: Sequence[int],
) -> List[ApprovedRecapRefV1]:
    weeks = sorted(set(int(w) for w in week_indices))
    if not weeks:
        return []

    placeholders = ",".join(["?"] * len(weeks))

    q = f"""
    SELECT ra.week_index, ra.artifact_type, ra.version, ra.selection_fingerprint
    FROM recap_artifacts ra
    JOIN (
        SELECT week_index, MAX(version) AS max_v
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND artifact_type = ?
          AND state = 'APPROVED'
          AND week_index IN ({placeholders})
        GROUP BY week_index
    ) latest
      ON latest.week_index = ra.week_index AND latest.max_v = ra.version
    WHERE ra.league_id = ?
      AND ra.season = ?
      AND ra.artifact_type = ?
      AND ra.state = 'APPROVED'
    ORDER BY ra.week_index ASC
    """

    args = [int(league_id), int(season), str(artifact_type), *weeks, int(league_id), int(season), str(artifact_type)]

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(q, args).fetchall()
    finally:
        con.close()

    out: List[ApprovedRecapRefV1] = []
    for week_index, a_type, version, fp in rows:
        out.append(
            ApprovedRecapRefV1(
                week_index=int(week_index),
                artifact_type=str(a_type),
                version=int(version),
                selection_fingerprint=str(fp),
            )
        )
    return out
