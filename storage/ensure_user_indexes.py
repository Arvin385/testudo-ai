"""Tool: ensure_user_indexes — create recommended indexes for the users collection.

Inputs
- none

Behavior
- Calls storage.mongo_client.ensure_indexes().

Returns (JSON)
- Success: {"status":"success","created":[index_names]}
- Error:   {"status":"error","message": "..."}
"""

from __future__ import annotations

from typing import Any, Dict

from .mongo_client import ensure_indexes


def ensure_user_indexes() -> Dict[str, Any]:
    """Create indexes for users collection and return JSON result."""

    return ensure_indexes()
