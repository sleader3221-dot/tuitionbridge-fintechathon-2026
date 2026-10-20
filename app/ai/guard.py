"""Untrusted-text handling. Memos and questions are data, never instructions."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_LEN = 500
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PATTERNS = {
    "override_instructions": re.compile(r"ignore\s+(all|any|the|your|previous|prior|above)\s+(previous\s+|prior\s+)?(instructions|rules|guidance)", re.I),
    "system_prompt_probe": re.compile(r"\b(system\s+prompt|developer\s+message)\b", re.I),
    "action_request": re.compile(r"\b(approve|execute|transfer|send|pay|wire)\b.{0,40}\b(all|everything|entire|full\s+balance|immediately|now)\b", re.I),
    "markup_injection": re.compile(r"<\s*/?\s*(script|system|instruction|tool)", re.I),
    "role_hijack": re.compile(r"\byou\s+are\s+now\b", re.I),
}


@dataclass
class Sanitized:
    text: str
    flagged: bool
    reasons: list[str] = field(default_factory=list)
    truncated: bool = False


def sanitize_untrusted(text: str | None) -> Sanitized:
    if text is None:
        return Sanitized("", False)
    cleaned = _CONTROL.sub("", str(text)).strip()
    truncated = len(cleaned) > MAX_LEN
    cleaned = cleaned[:MAX_LEN]
    reasons = [name for name, pat in _PATTERNS.items() if pat.search(cleaned)]
    return Sanitized(cleaned, bool(reasons), reasons, truncated)
