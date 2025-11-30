"""Return detailed JupiterP course data for a user-supplied course code.

Expected inputs are the canonical Testudo course code (for example,
``"CMSC131"``), a flag for including section payloads, and optional override
settings for the API base URL or timeout. The function emits JSON-serializable
dicts that describe one of three outcomes: successful data retrieval,
``not_found`` when the course is missing, or ``error`` when input validation or
network issues prevent a lookup.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .jupiterp_client import JupiterPAPIError, build_client


def get_course_by_code(
    course_code: str,
    include_sections: bool = False,
    *,
    base_url: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Look up a single course by code and format the JupiterP response.

    Parameters
    ----------
    course_code:
        Raw course code supplied by the caller; whitespace is stripped and the
        value is upper-cased prior to the request.
    include_sections:
        When ``True``, hits the ``/courses/withSections`` endpoint to include
        section metadata alongside the base course information. Defaults to
        ``False``.
    base_url:
        Optional alternative JupiterP base URL to support testing or proxying.
    timeout:
        Timeout (seconds) applied to the underlying HTTP request.

    Returns
    -------
    Dict[str, Any]
        JSON-serializable payload with ``status`` plus one of:

        - ``{"status": "success", "results": [...], "meta": {...}}`` when the
          API responds with at least one record.
        - ``{"status": "not_found"}`` when the API returns an empty list.
        - ``{"status": "error", "message": "..."}`` when validation fails or
          the API request raises :class:`JupiterPAPIError`.
    """

    normalized_code = course_code.strip().upper() if course_code else ""
    if not normalized_code:
        return {
            "status": "error",
            "message": "course_code is required",
        }

    endpoint = "courses/withSections" if include_sections else "courses"
    client = build_client(base_url=base_url, timeout=timeout)

    try:
        data = client.get(endpoint, params={"courseCodes": normalized_code})
    except JupiterPAPIError as exc:
        return {
            "status": "error",
            "message": str(exc),
            "course_code": normalized_code,
        }

    if not data:
        return {
            "status": "not_found",
            "course_code": normalized_code,
        }

    return {
        "status": "success",
        "course_code": normalized_code,
        "results": data,
        "meta": {"result_count": len(data), "includes_sections": include_sections},
    }
