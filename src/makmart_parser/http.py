"""HTTP client utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry


@dataclass(slots=True)
class HttpClient:
    """Thin wrapper around :class:`requests.Session` with retry and throttling."""

    base_url: str
    user_agent: str
    rate_limit_seconds: float
    timeout: int
    max_retries: int

    def __post_init__(self) -> None:
        self._session = Session()
        retries = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update({"User-Agent": self.user_agent})
        self._last_request_ts: float = 0.0

    def build_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url.rstrip('/')}{path}"

    def get(self, path: str, **kwargs: object) -> Response:
        self._respect_rate_limit()
        url = self.build_url(path)
        response = self._session.get(url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response

    def stream(self, path: str, **kwargs: object) -> Response:
        self._respect_rate_limit()
        url = self.build_url(path)
        response = self._session.get(url, timeout=self.timeout, stream=True, **kwargs)
        response.raise_for_status()
        return response

    def with_request(self, func: Callable[[Session], Response]) -> Response:
        self._respect_rate_limit()
        response = func(self._session)
        response.raise_for_status()
        return response

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_ts = time.monotonic()

    def close(self) -> None:
        self._session.close()


__all__ = ["HttpClient"]
