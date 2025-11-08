from __future__ import annotations

from random import randint
from typing import List

from ..models import SafetyReport


def evaluate_token(token_address: str) -> SafetyReport:
    """Mock risk scoring for a token."""
    score = randint(60, 95)
    issues: List[str] = []
    if score < 70:
        issues.append("High tax detected")
    if token_address.lower().startswith("0xdead"):
        issues.append("Owner may retain mint privileges")
    return SafetyReport(token_address=token_address, score=score, issues=issues)
