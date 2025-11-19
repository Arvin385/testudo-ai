"""Pull instructor records (optionally active-only) and PlanetTerp ratings.

The function supports fetching instructors by name or slug, constraining by
average rating, and applying pagination or sorting directives. It returns
JSON-serializable dicts that include either the successful results or details
about validation failures (such as supplying both names and slugs) alongside
network errors bubbled up from JupiterP.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .jupiterp_client import JupiterPAPIError, build_client


def _join(items: Sequence[str]) -> str:
    return ",".join(item.strip() for item in items if item.strip())


def get_instructor_info(
    *,
    instructor_names: Optional[Sequence[str]] = None,
    instructor_slugs: Optional[Sequence[str]] = None,
    ratings: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_by: Optional[Sequence[str]] = None,
    active_only: bool = False,
    base_url: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Retrieve instructor information filtered by the provided criteria.

    Parameters
    ----------
    instructor_names:
        Sequence of instructor display names; mutually exclusive with slugs.
    instructor_slugs:
        Sequence of instructor slugs as defined by PlanetTerp identifiers.
    ratings:
        Sequence of rating inequality expressions (``gt.4.5`` etc.).
    limit, offset:
        Pagination arguments forwarded to JupiterP.
    sort_by:
        Sequence of ``column[.asc|.desc]`` sorting tokens.
    active_only:
        When ``True``, restricts requests to the ``/instructors/active``
        endpoint, returning only instructors currently teaching.
    base_url:
        Optional JupiterP base URL override.
    timeout:
        Timeout (seconds) applied to the HTTP request.

    Returns
    -------
    Dict[str, Any]
        Successful lookups return ``{"status": "success", "results": [...],
        "filters": {...}, "meta": {"result_count": N, "active_only": bool}}``.
        Validation failures or HTTP/runtime errors emit
        ``{"status": "error", "message": "..."}``.
    """

    if instructor_names and instructor_slugs:
        return {
            "status": "error",
            "message": "Provide either instructor_names or instructor_slugs, not both",
        }

    params: Dict[str, Any] = {}

    if instructor_names:
        params["instructorNames"] = _join(instructor_names)
    if instructor_slugs:
        params["instructorSlugs"] = _join(instructor_slugs)
    if ratings:
        params["ratings"] = [value.strip() for value in ratings if value.strip()]
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort_by:
        params["sortBy"] = _join(sort_by)

    endpoint = "instructors/active" if active_only else "instructors"
    client = build_client(base_url=base_url, timeout=timeout)

    try:
        data = client.get(endpoint, params=params)
    except JupiterPAPIError as exc:
        return {
            "status": "error",
            "message": str(exc),
            "filters": params,
        }

    return {
        "status": "success",
        "filters": params,
        "results": data,
        "meta": {"result_count": len(data), "active_only": active_only},
    }
