"""Shared utilities: Substack API helpers, HTML stripping, logging."""

import logging
import time
from datetime import datetime, timezone

import html2text
import requests
from tenacity import retry, stop_after_attempt, retry_if_exception_type, retry_if_exception

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

# Substack rate-limits the archive/post endpoints (HTTP 429), especially when
# fetching the full watchlist in a tight loop. Retry those with backoff that
# honors a Retry-After header so we stop silently dropping publications.


def _is_rate_limited(exc: BaseException) -> bool:
    resp = getattr(exc, "response", None)
    return (
        isinstance(exc, requests.HTTPError)
        and resp is not None
        and resp.status_code == 429
    )


def _wait_substack_backoff(retry_state) -> float:
    """Honor a numeric Retry-After header on 429; else exponential backoff, capped at 30s."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    resp = getattr(exc, "response", None)
    if resp is not None:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), 30.0)
            except ValueError:
                pass  # HTTP-date form — fall through to exponential backoff
    return min(2.0 * (2 ** (retry_state.attempt_number - 1)), 30.0)


_SUBSTACK_RETRY = dict(
    stop=stop_after_attempt(4),
    wait=_wait_substack_backoff,
    retry=(
        retry_if_exception_type((requests.Timeout, requests.ConnectionError))
        | retry_if_exception(_is_rate_limited)
    ),
    reraise=True,
)


@retry(**_SUBSTACK_RETRY)
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
    # NOTE: Around 2026-11-06 Substack changed the archive API. Two changes:
    #   1. The `offset` param is now rejected with a 400 ("Invalid value") —
    #      they moved to cursor-based pagination. We only ever fetch the first
    #      page, so offset is unnecessary; omit it.
    #   2. The response is now a dict {"posts": [...], "nextCursor": ...}
    #      instead of a bare JSON array. Unwrap it to preserve this function's
    #      list-of-posts contract.
    params = {"sort": "new", "limit": limit}

    resp = _session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return data.get("posts", [])
    return data


@retry(**_SUBSTACK_RETRY)
def _fetch_post_content_raw(publication_url: str, slug: str, timeout: int = 15) -> str | None:
    """Fetch body_html for a post. Raises on 429 (retried) and network errors; returns None on other HTTP errors."""
    base = publication_url.rstrip("/")
    url = f"{base}/api/v1/posts/{slug}"

    resp = _session.get(url, timeout=timeout)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        if _is_rate_limited(e):
            raise  # let tenacity back off and retry
        logger.warning(f"Failed to fetch content for {slug} from {base}: {e}")
        return None
    return resp.json().get("body_html")


def fetch_post_content(publication_url: str, slug: str, timeout: int = 15) -> str | None:
    """Fetch full body_html for a single post by slug.

    Returns HTML string, or None on failure (including rate-limiting that
    survives all retries) — preserves the None-on-failure contract callers rely on.
    """
    try:
        return _fetch_post_content_raw(publication_url, slug, timeout)
    except (requests.HTTPError, requests.Timeout, requests.ConnectionError) as e:
        logger.warning(f"Failed to fetch content for {slug} after retries: {e}")
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
