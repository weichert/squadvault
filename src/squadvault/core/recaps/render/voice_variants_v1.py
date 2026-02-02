from __future__ import annotations

from dataclasses import dataclass

VOICE_IDS = ("neutral", "playful", "dry")


@dataclass(frozen=True)
class VoiceSpec:
    voice_id: str
    label: str
    disclaimer: str


def get_voice_spec(voice_id: str) -> VoiceSpec:
    v = (voice_id or "").strip().lower()
    if v not in VOICE_IDS:
        raise ValueError(f"Unknown voice_id: {voice_id}. Allowed: {', '.join(VOICE_IDS)}")

    if v == "neutral":
        return VoiceSpec(
            voice_id="neutral",
            label="NEUTRAL",
            disclaimer="Baseline voice. Expressive constraints disabled.",
        )

    if v == "playful":
        return VoiceSpec(
            voice_id="playful",
            label="PLAYFUL",
            disclaimer="Light framing only. No new facts. No speculation.",
        )

    return VoiceSpec(
        voice_id="dry",
        label="DRY",
        disclaimer="Minimal framing only. No new facts. No speculation.",
    )


def format_variant_block(*, voice_id: str, body: str) -> str:
    spec = get_voice_spec(voice_id)
    header = [
        "------------------------------------------------------------",
        f"NON-CANONICAL VARIANT — VOICE: {spec.label} ({spec.voice_id})",
        f"Voice contract: {spec.disclaimer}",
        "------------------------------------------------------------",
        "",
    ]
    return "\n".join(header) + body.strip() + "\n"
