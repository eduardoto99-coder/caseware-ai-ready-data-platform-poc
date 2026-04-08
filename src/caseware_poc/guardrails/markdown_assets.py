from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<frontmatter>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)


def load_markdown_asset(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text.strip()
    frontmatter = yaml.safe_load(match.group("frontmatter")) or {}
    body = match.group("body").strip()
    return frontmatter, body
