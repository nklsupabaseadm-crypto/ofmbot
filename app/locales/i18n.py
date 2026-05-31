"""
Lightweight i18n: loads locale JSON files and returns translated strings.
Usage:
    from app.locales.i18n import t
    text = t("welcome", lang="ru", name="Artem")
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_LOCALES_DIR = Path(__file__).parent
_SUPPORTED = {"en", "ru"}
_FALLBACK = "en"


@lru_cache(maxsize=8)
def _load(lang: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Return translated string for *key* in *lang*, formatted with **kwargs."""
    resolved = lang if lang in _SUPPORTED else _FALLBACK
    strings = _load(resolved)
    template = strings.get(key) or _load(_FALLBACK).get(key, key)
    return template.format(**kwargs) if kwargs else template
