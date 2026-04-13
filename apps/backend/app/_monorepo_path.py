"""Put repo ``packages/`` on ``sys.path`` so ``memory``, ``rag``, ``prompts`` import without ``PYTHONPATH``."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_packages_on_path() -> None:
    # apps/backend/app/_monorepo_path.py → parents[3] = monorepo root (…/cv-bot)
    repo_root = Path(__file__).resolve().parents[3]
    pkg_root = repo_root / "packages"
    if pkg_root.is_dir():
        s = str(pkg_root)
        if s not in sys.path:
            sys.path.insert(0, s)


ensure_packages_on_path()
