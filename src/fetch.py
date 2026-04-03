"""Content Monitor: pull post metadata from all watchlist publications."""

import json
import logging
from datetime import datetime
from pathlib import Path

from src.models import Post
from src.utils import fetch_archive, is_within_window, polite_delay

logger = logging.getLogger("pipeline.fetch")


def load_watchlist(path: str = "config/watchlist.json") -> list[dict]:
    with open(path) as f:
        return json.load(f)["publications"]


def load_digest_history(path: str = "data/digest_history.json") -> set[int]:
    """Return set of post IDs already included in previous digests."""
    try:
        with open(path) as f:
            data = json.load(f)
        seen = set()
        for digest in data.get("digests", []):
            seen.update(digest.get("post_ids", []))
        return seen
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def parse_post(raw: dict, publication_url: str, publication_name: str) -> Post | None:
    """Parse a raw archive API dict into a Post model. Returns None on failure."""
    try:
        bylines = raw.get("publishedBylines", [])
        author_name = bylines[0].get("name", "") if bylines else ""
        author_handle = bylines[0].get("handle", "") if bylines else ""
        author_bio = bylines[0].get("bio", "") or "" if bylines else ""

        return Post(
            post_id=raw["id"],
            title=raw.get("title", ""),
            subtitle=raw.get("subtitle"),
            description=raw.get("description"),
            truncated_body_text=raw.get("truncated_body_text"),
            post_date=raw["post_date"],
            wordcount=raw.get("wordcount"),
            slug=raw.get("slug", ""),
            canonical_url=raw.get("canonical_url", ""),
            audience=raw.get("audience", "everyone"),
            reaction_count=raw.get("reaction_count", 0) or 0,
            reactions=raw.get("reactions") or {},
            restacks=raw.get("restacks", 0) or 0,
            comment_count=raw.get("comment_count", 0) or 0,
            author_name=author_name,
            author_handle=author_handle,
            author_bio=author_bio,
            publication_name=publication_name,
            publication_url=publication_url,
        )
    except (KeyError, ValueError) as e:
        logger.warning(f"Failed to parse post from {publication_name}: {e}")
        return None


def fetch_all_posts(
    watchlist: list[dict],
    lookback_days: int = 1,
    max_posts_per_pub: int = 10,
    delay: float = 0.75,
    seen_ids: set[int] | None = None,
) -> tuple[list[Post], list[dict]]:
    """Fetch metadata for recent posts from all watchlist publications.

    Returns:
        (posts, errors) — list of Post objects and list of error dicts
    """
    if seen_ids is None:
        seen_ids = set()

    all_posts: list[Post] = []
    errors: list[dict] = []

    for i, pub in enumerate(watchlist):
        url = pub["url"]
        name = pub.get("name", url)

        try:
            raw_posts = fetch_archive(url, limit=max_posts_per_pub)
            pub_posts = []

            for raw in raw_posts:
                # Skip paywalled posts
                if raw.get("audience") == "only_paid":
                    continue

                # Skip posts outside lookback window
                post_date = raw.get("post_date", "")
                if not is_within_window(post_date, lookback_days):
                    continue

                # Skip already-seen posts
                post_id = raw.get("id")
                if post_id in seen_ids:
                    continue

                post = parse_post(raw, url, name)
                if post:
                    pub_posts.append(post)

            all_posts.extend(pub_posts)
            logger.info(f"[{i+1}/{len(watchlist)}] {name}: {len(pub_posts)} new posts")

        except Exception as e:
            logger.error(f"[{i+1}/{len(watchlist)}] {name}: FAILED — {e}")
            errors.append({"publication": name, "url": url, "error": str(e)})

        if i < len(watchlist) - 1:
            polite_delay(delay)

    logger.info(f"Fetch complete: {len(all_posts)} posts from {len(watchlist)} publications, {len(errors)} errors")
    return all_posts, errors


def save_fetched_posts(posts: list[Post], run_dir: Path) -> Path:
    """Write fetched posts to intermediate state file."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "fetched.json"
    with open(path, "w") as f:
        json.dump([p.model_dump(mode="json") for p in posts], f, indent=2, default=str)
    return path
