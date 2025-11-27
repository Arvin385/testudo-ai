"""Query JupiterP for courses that match flexible filtering criteria.

Supports combining course codes, department prefixes, course numbers,
Gen-Ed filters, credit constraints, pagination, and sorting flags. Optional
``include_sections`` toggles whether section data comes back with each course.
Responses are JSON-serializable dicts that report success, echo the filters
applied, and include error details when invalid filter combinations are
supplied or the upstream API fails.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Sequence

from .jupiterp_client import JupiterPAPIError, build_client


def _join(items: Sequence[str]) -> str:
    return ",".join(item.strip() for item in items if item.strip())


def _normalize_codes(codes: Iterable[str]) -> str:
    return _join(code.upper() for code in codes)


def get_courses_by_filters(
    *,
    course_codes: Optional[Sequence[str]] = None,
    prefix: Optional[str] = None,
    number: Optional[str] = None,
    gen_eds: Optional[Sequence[str]] = None,
    credits: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_by: Optional[Sequence[str]] = None,
    include_sections: bool = False,
    base_url: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Fetch courses that satisfy the provided filters from JupiterP.

    Parameters
    ----------
    course_codes:
        Sequence of explicit course codes. Mutually exclusive with ``prefix``.
    prefix:
        Department prefix matcher such as ``"CMSC1"``; cannot be combined with
        ``course_codes``.
    number:
        Course number string to match across departments (for example ``"433"``).
    gen_eds:
        Sequence of Gen-Ed requirement codes; all requirements must be satisfied.
    credits:
        Sequence of inequality expressions (``gt.3``, ``lte.4``) applied to the
        ``min_credits`` field.
    limit, offset:
        Pagination controls passed directly to the API.
    sort_by:
        Sequence of ``column[.asc|.desc]`` directives (for example
        ``("course_code.asc", "min_credits.desc")``).
    include_sections:
        When ``True``, query ``/courses/withSections`` instead of ``/courses``.
    base_url:
        Optional JupiterP base URL override.
    timeout:
        Timeout (seconds) applied to the HTTP request.

    Returns
    -------
    Dict[str, Any]
        JSON-serializable dict with keys:

        - ``status`` set to ``"success"`` when the API call succeeds.
        - ``filters`` echoing the sanitized parameters sent to JupiterP.
        - ``results`` containing the list returned by the API.
        - ``meta`` with ``result_count`` and the ``includes_sections`` flag.

        On validation failures or HTTP errors, ``status`` is set to ``"error"``
        and ``message`` describes the issue.
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
    if number:
        params["number"] = number.strip()
    if gen_eds:
        params["genEds"] = _normalize_codes(gen_eds)
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort_by:
        params["sortBy"] = _join(sort_by)
    if credits:
        params["credits"] = [credit.strip() for credit in credits if credit.strip()]

    endpoint = "courses/withSections" if include_sections else "courses"
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
        "meta": {"result_count": len(data), "includes_sections": include_sections},
    }
