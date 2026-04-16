"""Shared utilities: Substack API helpers, HTML stripping, logging."""

import logging
import time
from datetime import datetime, timezone

import html2text
import requests
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

logger = logging.getLogger("pipeline")

# Reusable session with connection pooling
_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
})


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# --- Substack raw API helpers ---


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
)
def fetch_archive(
    publication_url: str,
    limit: int = 10,
    timeout: int = 15,
) -> list[dict]:
    """Fetch recent posts from a publication's archive API.

    Returns raw JSON dicts — one per post with all metadata inline.
    Does NOT include full body_html (that requires a per-post fetch).
    """
    base = publication_url.rstrip("/")
    url = f"{base}/api/v1/archive"
    params = {"sort": "new", "offset": 0, "limit": limit}

    resp = _session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
)
def fetch_post_content(publication_url: str, slug: str, timeout: int = 15) -> str | None:
    """Fetch full body_html for a single post by slug.

    Returns HTML string, or None on failure.
    """
    base = publication_url.rstrip("/")
    url = f"{base}/api/v1/posts/{slug}"

    try:
        resp = _session.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("body_html")
    except requests.HTTPError as e:
        logger.warning(f"Failed to fetch content for {slug} from {base}: {e}")
        return None


# --- HTML stripping ---

_html_converter = html2text.HTML2Text()
_html_converter.ignore_links = False
_html_converter.ignore_images = True
_html_converter.ignore_emphasis = False
_html_converter.body_width = 0  # Don't wrap lines


def strip_html(html: str) -> str:
    """Convert HTML to clean plain text suitable for LLM input."""
    if not html:
        return ""
    return _html_converter.handle(html).strip()


# --- Date helpers ---


def is_within_window(post_date_str: str, lookback_days: int) -> bool:
    """Check if a post date string is within the lookback window."""
    try:
        post_dt = datetime.fromisoformat(post_date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - post_dt
        return delta.days <= lookback_days
    except (ValueError, TypeError):
        return False


def polite_delay(seconds: float) -> None:
    """Sleep between API calls with slight randomization."""
    import random
    jitter = seconds * random.uniform(0.5, 1.5)
    time.sleep(jitter)
