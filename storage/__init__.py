"""Storage tools package for MongoDB-backed user data.

Why this exists:
- Marks 'storage' as a package so sibling modules can use relative imports.
- Optionally re-exports helpers for convenience.
- A home for shared types or constants later.

Environment variables expected by tools in this package:
- MONGODB_URI: Atlas connection string (required in deployed environments)
- MONGODB_DB: Database name (default: 'userdata')
- MONGODB_USERS_COLL: Users collection name (default: 'users')
"""

from .mongo_client import ensure_indexes, get_collection  # re-export (optional)

__all__ = ["get_collection", "ensure_indexes"]
