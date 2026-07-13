import os
import re
from typing import Any


REDACTED = "***REDACTED***"

RAW_TOKEN_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]+"),
)

PREFIXED_TOKEN_PATTERNS = (
    re.compile(r"(Authorization:\s*(?:Bearer|token)\s+)([^\s\"']+)", re.IGNORECASE),
    re.compile(r"(Bearer\s+)([A-Za-z0-9._-]{20,})", re.IGNORECASE),
    re.compile(r"((?:GITHUB_TOKEN|GITHUB_API_TOKEN)\s*=\s*)([^\s\"']+)", re.IGNORECASE),
    re.compile(r"((?:-t|--token|--github-token)\s+)([^\s\"']+)", re.IGNORECASE),
)


def _configured_secret_values() -> list[str]:
    values = []
    for name in ("GITHUB_TOKEN", "GITHUB_API_TOKEN"):
        value = os.getenv(name)
        if value and len(value) > 3:
            values.append(value)
    return values


def mask_secret(secret: Any) -> str:
    text = "" if secret is None else str(secret)
    suffix = text[-5:] if len(text) >= 5 else text
    return f"{REDACTED}{suffix}"


def sanitize_text(value: Any) -> str:
    text = "" if value is None else str(value)

    for secret in _configured_secret_values():
        text = text.replace(secret, mask_secret(secret))

    for pattern in RAW_TOKEN_PATTERNS:
        text = pattern.sub(lambda match: mask_secret(match.group(0)), text)

    for pattern in PREFIXED_TOKEN_PATTERNS:
        text = pattern.sub(
            lambda match: f"{match.group(1)}{mask_secret(match.group(2))}",
            text,
        )

    return text


def sanitize_data(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if "token" in key_text or "authorization" in key_text:
                result[key] = mask_secret(item) if item else item
            else:
                result[key] = sanitize_data(item)
        return result

    if isinstance(value, list):
        return [sanitize_data(item) for item in value]

    if isinstance(value, tuple):
        return tuple(sanitize_data(item) for item in value)

    if isinstance(value, str):
        return sanitize_text(value)

    return value
