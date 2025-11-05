#!/usr/bin/env python3
"""Download the latest Zwift ride image to the local www directory."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import logging

DEST_PATH = Path("/config/www/zwift/latest_ride.jpg")
TOKEN_PATH = Path("/config/zwift_access_token.txt")
USER_AGENT = "HomeAssistant-ZwiftImage/1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s download_latest_ride_image %(message)s",
)
LOGGER = logging.getLogger("download_latest_ride_image")


def _fetch(url: str, headers: dict[str, str]) -> Tuple[Optional[int], Optional[bytes]]:
    """Attempt to download the resource with the given headers."""
    LOGGER.debug("Attempting fetch: url=%s headers=%s", url, list(headers.keys()))
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=30) as response:  # nosec: B310 (trusted source)
            status = response.getcode()
            payload = response.read()
            LOGGER.info("Fetch success: status=%s bytes=%s", status, len(payload))
            return status, payload
    except HTTPError as err:  # pragma: no cover - network failure
        LOGGER.warning(
            "HTTP error during fetch: url=%s status=%s reason=%s", url, err.code, err.reason
        )
        return err.code, None
    except URLError as err:
        LOGGER.error("URL error during fetch: url=%s error=%s", url, err)
        return None, None


def _read_token() -> str:
    try:
        raw = TOKEN_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        LOGGER.info("Token file not found: path=%s", TOKEN_PATH)
        return ""
    token = raw.strip()
    if token:
        LOGGER.info("Token loaded from %s (length=%s)", TOKEN_PATH, len(token))
    else:
        LOGGER.warning("Token file %s is empty", TOKEN_PATH)
    return token


def main(argv: list[str]) -> int:
    LOGGER.info("Downloader invoked with argv=%s", argv)
    if len(argv) < 2:
        LOGGER.error("No URL argument provided; exiting.")
        return 0

    url = argv[1].strip()
    if not url:
        LOGGER.error("Provided URL argument is empty; exiting.")
        return 0

    LOGGER.debug("Ensuring destination directory exists: %s", DEST_PATH.parent)
    DEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    token = _read_token()
    headers = {"User-Agent": USER_AGENT}
    status: Optional[int] = None
    payload: Optional[bytes] = None

    if token:
        auth_headers = dict(headers)
        auth_headers["Authorization"] = f"Bearer {token}"
        LOGGER.info("Attempting authenticated download.")
        status, payload = _fetch(url, auth_headers)
    else:
        LOGGER.info("No token available; skipping authenticated download.")

    if payload is None:
        LOGGER.info("Falling back to unauthenticated download.")
        status, payload = _fetch(url, headers)

    if not payload or status is None or status < 200 or status >= 300:
        status_text = status if status is not None else "unknown"
        LOGGER.error("Download failed or returned invalid data: status=%s", status_text)
        return 0

    tmp_file: Optional[Path] = None
    try:
        LOGGER.debug("Creating temporary file under %s", DEST_PATH.parent)
        with tempfile.NamedTemporaryFile(
            "wb", delete=False, dir=str(DEST_PATH.parent), prefix="latest_ride_", suffix=".jpg"
        ) as tmp:
            tmp.write(payload)
            tmp_file = Path(tmp.name)
            LOGGER.info("Wrote %s bytes to temporary file %s", len(payload), tmp_file)
        LOGGER.debug("Replacing %s with %s", DEST_PATH, tmp_file)
        tmp_file.replace(DEST_PATH)
        LOGGER.info("Latest ride image updated: %s", DEST_PATH)
    finally:
        if tmp_file and tmp_file.exists():
            try:
                LOGGER.debug("Cleaning up temporary file %s", tmp_file)
                tmp_file.unlink()
            except OSError:
                LOGGER.warning("Failed to delete temporary file %s", tmp_file)
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
