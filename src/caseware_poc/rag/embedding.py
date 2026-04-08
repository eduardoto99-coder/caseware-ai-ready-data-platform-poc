from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

import numpy as np


class HashEmbeddingProvider:
    """Stable, dependency-light embedding adapter for a runnable POC."""

    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def embed_text(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            bucket = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = -1.0 if digest[8] % 2 else 1.0
            vector[bucket] += sign
        norm = math.sqrt(float(np.dot(vector, vector)))
        if norm == 0:
            return vector
        return vector / norm

    def embed_many(self, texts: Iterable[str]) -> np.ndarray:
        rows = [self.embed_text(text) for text in texts]
        if not rows:
            return np.zeros((0, self.dimensions), dtype=np.float32)
        return np.vstack(rows)
