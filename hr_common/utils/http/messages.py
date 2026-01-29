# hr_common/utils/http/messages.py

from __future__ import annotations


def show_message(text: str, *, duration: int | None = None) -> dict:
    payload = {"text": text}
    if duration is not None:
        payload["duration"] = duration
    return payload
