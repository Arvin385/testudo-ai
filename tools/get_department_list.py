"""Fetch the complete list of department codes and names from JupiterP.

This lightweight tool has no input parameters beyond optional overrides for the
API base URL and request timeout. It emits JSON-serializable dicts that either
contain the department data or describe the error encountered when contacting
JupiterP.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from scheduler.jupiterp_client import JupiterPAPIError, build_client


def get_department_list(
    # *,
    # base_url: Optional[str] = None,
    # timeout: float = 10.0,
) -> Dict[str, Any]:
    """Return all department codes and names exposed by JupiterP.

    Parameters
    ----------
    base_url:
        Alternate JupiterP base URL for mocking or proxying scenarios.
    timeout:
        Timeout (seconds) applied to the HTTP request.

    Returns
    -------
    Dict[str, Any]
        ``{"status": "success", "results": [...], "meta": {"result_count": N}}``
        when the response is received. Transient or network errors surface as
        ``{"status": "error", "message": "..."}``.
    """
    base_url: Optional[str] = None
    timeout: float = 10.0

    client = build_client(base_url=base_url, timeout=timeout)

    try:
        data = client.get("deptList")
    except JupiterPAPIError as exc:
        return {
            "status": "error",
            "message": str(exc),
        }

    return {
        "status": "success",
        "results": data,
        "meta": {"result_count": len(data)},
    }
