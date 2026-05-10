from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentClassification:
    primary_intent: str
    secondary_intents: list[str]
    confidence: float
    reason: str
