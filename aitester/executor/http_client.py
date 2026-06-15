import logging
from typing import Any

import httpx

from aitester.core.config import settings
from aitester.core.exceptions import HTTPClientError

logger = logging.getLogger("aitester.executor")


class ExecutorHTTPClient:
    """
    A configured HTTP client for executing tests against target APIs.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS)

    async def request(
        self,
        method: str,
        path: str,
        headers: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """
        Executes a single HTTP request and returns the response.
        """
        # Ensure path starts with slash if not a full URL (if base_url is set, it handles it mostly, but be safe)
        if not path.startswith("http"):
            url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        else:
            url = path

        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=query_params,
                    json=body if body else None,
                )
                return response
            except httpx.RequestError as e:
                logger.error(f"HTTP request failed: {e}")
                raise HTTPClientError(f"Failed to execute request to {url}: {str(e)}") from e
