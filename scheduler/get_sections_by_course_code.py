"""List Testudo section offerings for specific course codes or prefixes.

The tool accepts explicit course codes or a shared prefix, optional instructor
name filtering, seat availability toggles, and pagination controls. It returns
JSON-serializable dicts with either successful results, validation feedback, or
error details when the upstream JupiterP API cannot be reached.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .jupiterp_client import JupiterPAPIError, build_client


def _join(items: Sequence[str]) -> str:
    return ",".join(item.strip() for item in items if item.strip())


def _normalize_codes(codes: Sequence[str]) -> str:
    return _join(code.upper() for code in codes)


def get_sections_by_course_code(
    *,
    course_codes: Optional[Sequence[str]] = None,
    prefix: Optional[str] = None,
    instructor: Optional[str] = None,
    only_open: bool = False,
    total_class_size: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_by: Optional[Sequence[str]] = None,
    base_url: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Retrieve section metadata filtered by course code, prefix, or seats.

    Parameters
    ----------
    course_codes:
        Sequence of explicit course codes; mutually exclusive with ``prefix``.
    prefix:
        Course prefix such as ``"CMSC"`` or ``"CMSC1"`` to match multiple codes.
    instructor:
        Exact instructor name (case-sensitive) required in the section listing.
    only_open:
        When ``True``, only include sections reporting ``open_seats > 0``.
    total_class_size:
        Sequence of inequality expressions (``gte.40``) applied to section
        ``total_seats``.
    limit, offset:
        Pagination arguments passed to the API.
    sort_by:
        Sequence of column sort directives (``sec_code.asc`` etc.).
    base_url:
        Optional JupiterP base URL override.
    timeout:
        Timeout (seconds) applied to the HTTP request.

    Returns
    -------
    Dict[str, Any]
        On success, returns ``{"status": "success", "results": [...],
        "filters": {...}, "meta": {"result_count": N}}``. When mutually
        exclusive arguments are supplied or the API raises
        :class:`JupiterPAPIError`, the payload switches to
        ``{"status": "error", "message": "..."}``.
    """

    if course_codes and prefix:
        return {
            "status": "error",
            "message": "course_codes and prefix cannot both be provided",
        }

    params: Dict[str, Any] = {}

    if course_codes:
        params["courseCodes"] = _normalize_codes(course_codes)
    if prefix:
        params["prefix"] = prefix.strip().upper()
    if instructor:
        params["instructor"] = instructor.strip()
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort_by:
        params["sortBy"] = _join(sort_by)
    if total_class_size:
        params["totalClassSize"] = [
            value.strip() for value in total_class_size if value.strip()
        ]
    if only_open:
        params["onlyOpen"] = "true"

    client = build_client(base_url=base_url, timeout=timeout)

    try:
        data = client.get("sections", params=params)
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
        "meta": {"result_count": len(data)},
    }
