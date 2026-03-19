"""Gestion simple des traductions.

Chaque langue est un module dans `lang/` avec un dictionnaire `TEXTS`.
"""

from importlib import import_module

_current = {}


def set_language(code: str):
    """Charge la langue spécifiée (fichier lang/<code>.py)."""
    global _current
    try:
        mod = import_module(f"lang.{code}")
        _current = getattr(mod, "TEXTS", {})
    except Exception:
        # Fallback : anglais si la langue demandée n'existe pas
        try:
            mod = import_module("lang.en")
            _current = getattr(mod, "TEXTS", {})
        except Exception:
            _current = {}


def t(key: str, default: str = None) -> str:
    """Retourne la traduction pour la clé donnée."""
    if default is None:
        default = key
    return _current.get(key, default)
