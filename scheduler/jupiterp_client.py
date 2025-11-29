"""Core HTTP client abstractions used by the JupiterP-backed scheduler tools.

Provides a thin wrapper around :mod:`requests` that normalizes base URLs,
applies a configurable timeout, and raises :class:`JupiterPAPIError` when the
remote JupiterP API cannot be reached or returns non-JSON payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional

import requests

DEFAULT_BASE_URL = "https://api.jupiterp.com/v0"


class JupiterPAPIError(RuntimeError):
    """Raised when the JupiterP API returns an error or cannot be reached."""


@dataclass
class JupiterPClient:
    """HTTP client for the JupiterP API with simple GET support."""

    base_url: str = DEFAULT_BASE_URL
    timeout: float = 10.0
    session: Optional[requests.Session] = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self._session = self.session or requests.Session()

    def get(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        """Perform a GET request against the JupiterP API and return parsed JSON.

        Parameters
        ----------
        endpoint:
            API path component such as ``"courses"`` or ``"sections"``. Leading
            slashes are ignored and the path is appended to ``base_url``.
        params:
            Optional mapping of query string parameters to pass through. ``None``
            values are stripped before the request is made.

        Returns
        -------
        Any
            Parsed JSON data (typically a list or dict) from the JupiterP API.

        Raises
        ------
        JupiterPAPIError
            If the HTTP request fails, times out, or the response body cannot be
            decoded as JSON.
        """

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_params: Optional[MutableMapping[str, Any]] = None
        if params:
            request_params = {
                key: value for key, value in params.items() if value is not None
            }

        try:
            response = self._session.get(
                url, params=request_params, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.Timeout as exc:  # pragma: no cover - thin wrapper
            raise JupiterPAPIError("JupiterP API request timed out") from exc
        except requests.RequestException as exc:  # pragma: no cover - thin wrapper
            raise JupiterPAPIError("JupiterP API request failed") from exc

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - depends on remote API
            raise JupiterPAPIError("JupiterP API returned invalid JSON") from exc


def build_client(
    base_url: Optional[str] = None, timeout: float = 10.0
) -> JupiterPClient:
    """Create a :class:`JupiterPClient` configured for the JupiterP API.

    Parameters
    ----------
    base_url:
        Alternate API base URL; defaults to ``https://api.jupiterp.com/v0``.
    timeout:
        Socket timeout (seconds) applied to outgoing requests.

    Returns
    -------
    JupiterPClient
        Client configured with the requested base URL and timeout.
    """

    return JupiterPClient(base_url=base_url or DEFAULT_BASE_URL, timeout=timeout)
