"""Pytest root conftest — ensures repo root is importable.

Lets tests do ``from runtime.event_bus import EventBus`` and
``from sdk.python.skill import Skill`` without installing the package.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
