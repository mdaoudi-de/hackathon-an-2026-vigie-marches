"""Cache TTL en mémoire, minimaliste et thread-safe.

Deux rôles : respecter les quotas des APIs publiques (7 req/s sur
recherche-entreprises) et rendre la démo instantanée au deuxième appel.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Optional


class CacheTTL:
    def __init__(self, ttl_secondes: int = 900):
        self.ttl = ttl_secondes
        self._donnees: dict[str, tuple[float, Any]] = {}
        self._verrou = threading.Lock()

    def get(self, cle: str) -> Optional[Any]:
        with self._verrou:
            entree = self._donnees.get(cle)
            if entree is None:
                return None
            expire, valeur = entree
            if time.monotonic() > expire:
                del self._donnees[cle]
                return None
            return valeur

    def set(self, cle: str, valeur: Any) -> None:
        with self._verrou:
            self._donnees[cle] = (time.monotonic() + self.ttl, valeur)
