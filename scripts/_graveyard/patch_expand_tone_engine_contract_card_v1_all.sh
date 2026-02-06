#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: expand Tone Engine Contract Card to full canonical (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_expand_tone_engine_contract_card_v1.py"

cat > "${PATCHER}" <<'PY'
#!/usr/bin/env python3
import os
import sys

PATH = "docs/canonical/contracts/Tone_Engine_Contract_Card_v1.0.md"

NEW = """# Tone Engine — Contract Card (v1.0)

Contract Name: TONE_ENGINE  
Version: v1.0  
Status: CANONICAL  
Applies To: SquadVault Core Engine — tone governance across all narrative artifacts

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- SquadVault Core Engine — Technical Specification (v1.0)
- SquadVault — What We Are Not (Platform Guardrails) (v1.0)
- SquadVault — Data Ethics & Trust Positioning Memo (v1.0)
- Editorial Attunement Layer — Core Engine Addendum (v1.0)
- Creative Layer — Contract Card (v1.0)
- Approval Authority — Contract Card (v1.0)

---

## 1) Purpose

The Tone Engine governs **how** SquadVault speaks on behalf of a group, without changing:

- facts,
- selection,
- ordering,
- or meaning.

It emits deterministic, auditable **Tone Directives** that constrain drafting so narrative expression remains culturally consistent, predictable, and trust-preserving over time.

**Tone is governed expression — not learned preference.**

---

## 2) Authority & Boundary

### 2.1 What Tone Engine May Do (Allowed)

- Read **explicit, group-scoped tone configuration** (versioned).
- Produce a **ToneDirectiveSet** (enumerable constraints) for the Creative Layer.
- Provide neutral defaults when configuration is absent.
- Be overridden by safety constraints and explicit human editorial decisions (with audit logging).

### 2.2 What Tone Engine Must Never Do (Hard Stop)

The Tone Engine must never:

- Introduce, modify, reinterpret, or “fix up” facts.
- Influence Writing Room selection: inclusion, exclusion, grouping, ranking, or ordering.
- Infer intent, emotion, motivations, “group mood,” or “fragile periods” from content.
- Personalize tone per individual, participant, or subgroup.
- Learn adaptively from outcomes (approvals, edits, usage, engagement).
- Consume artifact text, drafts, embeddings, or semantic summaries of narratives.

If the Tone Engine needs any of the above to function, the correct response is: **do less.**

---

## 3) Inputs

### 3.1 Allowed Inputs (Authoritative)

The Tone Engine may consume only:

- `ToneConfig` (explicit, group-scoped configuration state; versioned).
- `SafetyConstraints` (system-level constraints; safety overrides all tone).
- `HumanOverrides` (explicit, audited; may override tone outputs).
- Minimal `WindowRef` metadata sufficient to associate directives to a specific window and artifact request (no content semantics).

### 3.2 Forbidden Inputs

The Tone Engine must not consume:

- Raw MemoryEvents or event content.
- Selection set content or signal content.
- Artifact drafts or finalized artifact text.
- Any engagement/usage/retention metrics.
- Cross-window learned state or “profile” derived from artifacts.

---

## 4) State & Persistence

The Tone Engine persists **configuration state only** (not learned behavior).

State characteristics:

- Group-scoped.
- Append-only, versioned changes (no silent edits).
- Changes occur only via explicit human action.
- No self-modifying behavior; no adaptive loops.

---

## 5) Outputs

### 5.1 Output Type

The Tone Engine outputs a deterministic `ToneDirectiveSet`: a set of enumerable constraints (not prose).

### 5.2 Output Requirements

- Deterministic given identical inputs.
- Enumerable and auditable.
- Traceable to `ToneConfig` version + window reference.

---

## 6) Determinism & Guarantees

- Identical inputs MUST produce identical outputs.
- Absence of configuration MUST produce neutral defaults.
- Removing/bypassing the Tone Engine MUST NOT break correctness.

---

## 7) Precedence & Conflict Resolution

1. Safety constraints  
2. Canonical constitution + core invariants  
3. Editorial Attunement Layer  
4. Human overrides  
5. Tone Engine  
6. Creative Layer  

---

## 8) Failure Modes

If tone risks trust, the correct response is restraint.

---

## 9) Validation Strategy

- Automated determinism checks
- Interface boundary enforcement
- Human spot review

---

## 10) Canonical Declaration

Any behavior not explicitly permitted is forbidden.
"""

def main():
    if not os.path.exists(PATH):
        print(f"ERROR: missing file: {PATH}", file=sys.stderr)
        return 2

    cur = open(PATH, "r", encoding="utf-8").read()

    if cur.strip() == NEW.strip():
        print("OK: Tone Engine contract already canonical")
        return 0

    markers = [
        "## Purpose",
        "## In Scope",
        "## Out of Scope (Hard Stop)",
        "Tone is governed expression, not learned preference.",
    ]
    if not all(m in cur for m in markers):
        print("ERROR: refusing to overwrite unexpected file shape", file=sys.stderr)
        return 2

    with open(PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(NEW + "\n")

    print("OK: Tone Engine contract expanded to canonical form")
    return 0

if __name__ == "__main__":
    sys.exit(main())
PY

chmod +x "${PATCHER}"

python "${PATCHER}"
echo "==> DONE"
