"""Feedback Monitor: match reshared Notes against digest suggestions."""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger("pipeline.feedback")


def fetch_notes(substack_url: str, timeout: int = 15) -> list[dict]:
    """Fetch user's Notes feed from the Substack API."""
    url = f"{substack_url.rstrip('/')}/api/v1/notes"
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        logger.warning(f"Failed to fetch notes from {url}: {e}")
        return []


def parse_note(item: dict) -> dict | None:
    """Extract reshare data from a Note item.

    Returns dict with post_id, title, author, commentary, timestamp
    if the Note has a post attachment (i.e., it's a reshare).
    Returns None for Notes without post attachments.
    """
    comment = item.get("comment") or {}
    context = item.get("context") or {}
    attachments = comment.get("attachments", [])

    # Find post attachment
    post_attachment = None
    for att in attachments:
        if att.get("type") == "post":
            post_attachment = att
            break

    if not post_attachment:
        return None

    post = post_attachment.get("post") or {}
    pub = post_attachment.get("publication") or {}

    return {
        "post_id": post.get("id"),
        "title": post.get("title", ""),
        "slug": post.get("slug", ""),
        "canonical_url": post.get("canonical_url", ""),
        "author": pub.get("author_name") or pub.get("name", ""),
        "publication": pub.get("name", ""),
        "commentary": comment.get("body", ""),
        "note_timestamp": context.get("timestamp", ""),
        "note_id": item.get("entity_key", ""),
    }


def load_digest_history(path: str = "data/digest_history.json") -> dict:
    """Load digest history and return a map of post_id → digest_date."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    post_to_digest: dict[int, str] = {}
    for digest in data.get("digests", []):
        date = digest.get("date", "")
        for pid in digest.get("post_ids", []):
            post_to_digest[pid] = date

    return post_to_digest


def load_reshare_log(path: str = "data/reshare_log.json") -> dict:
    """Load existing reshare log."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"reshares": [], "seen_note_ids": []}


def save_reshare_log(log: dict, path: str = "data/reshare_log.json") -> None:
    """Save reshare log."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=2, default=str)


def _publication_url_from_canonical(canonical_url: str) -> str | None:
    """Extract a publication's base URL (scheme + host) from a post's canonical URL."""
    if not canonical_url:
        return None
    try:
        parsed = urlparse(canonical_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}".lower()
    except Exception:
        return None


def flag_publications_from_unmatched(
    reshares: list[dict],
    user_substack_url: str | None,
    watchlist_path: str = "config/watchlist.json",
    candidates_path: str = "data/reshare_candidates.json",
) -> list[dict]:
    """Flag publications from unmatched reshares that aren't in the watchlist.

    Skips the user's own publication (self-reshares). Skips pubs already in
    the watchlist. Appends new candidates to candidates_path with a count of
    how many times each pub has been reshared.

    Returns the list of newly flagged publications (newly added candidates only).
    """
    user_host = _publication_url_from_canonical(user_substack_url) if user_substack_url else None

    try:
        with open(watchlist_path) as f:
            wl = json.load(f).get("publications", [])
    except (FileNotFoundError, json.JSONDecodeError):
        wl = []
    wl_hosts = {_publication_url_from_canonical(p.get("url", "")) for p in wl}
    wl_hosts.discard(None)
    wl_names = {p.get("name", "").lower().strip() for p in wl if p.get("name")}
    wl_authors = {p.get("author", "").lower().strip() for p in wl if p.get("author")}

    try:
        with open(candidates_path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"candidates": []}

    by_url: dict[str, dict] = {c["url"]: c for c in data.get("candidates", [])}
    newly_flagged: list[dict] = []

    for r in reshares:
        if r.get("matched"):
            continue
        pub_url = _publication_url_from_canonical(r.get("canonical_url", ""))
        if not pub_url:
            continue

        # Generic substack.com URLs (e.g. /home/post/p-XXX) don't identify a
        # specific publication — fall back to name/author matching.
        is_generic = pub_url in ("https://substack.com", "https://www.substack.com")

        if user_host and pub_url == user_host:
            continue
        if not is_generic and pub_url in wl_hosts:
            continue

        # Dedup against watchlist by publication name or author when URL is generic
        # or when the same pub is listed under a different URL form.
        pub_name = (r.get("publication") or "").lower().strip()
        author = (r.get("author") or "").lower().strip()
        if pub_name and pub_name in wl_names:
            continue
        if author and author in wl_authors:
            continue
        if is_generic:
            # Skip generic substack.com URLs — can't store as a useful candidate
            continue

        if pub_url in by_url:
            entry = by_url[pub_url]
            entry["reshare_count"] = entry.get("reshare_count", 0) + 1
            entry["last_reshared"] = r.get("note_timestamp", "")
        else:
            entry = {
                "url": pub_url,
                "name": r.get("publication", ""),
                "author": r.get("author", ""),
                "source": "reshare",
                "reshare_count": 1,
                "first_reshared": r.get("note_timestamp", ""),
                "last_reshared": r.get("note_timestamp", ""),
                "example_post": r.get("title", ""),
            }
            by_url[pub_url] = entry
            newly_flagged.append(entry)
            logger.info(f"Flagged candidate from reshare: {entry['name']} ({pub_url})")

    data["candidates"] = list(by_url.values())
    Path(candidates_path).parent.mkdir(parents=True, exist_ok=True)
    with open(candidates_path, "w") as f:
        json.dump(data, f, indent=2)

    return newly_flagged


def check_for_reshares(
    substack_url: str,
    digest_history_path: str = "data/digest_history.json",
    reshare_log_path: str = "data/reshare_log.json",
    watchlist_path: str = "config/watchlist.json",
    candidates_path: str = "data/reshare_candidates.json",
) -> list[dict]:
    """Check Notes for reshares that match digest suggestions.

    Returns list of new reshares found.
    """
    notes = fetch_notes(substack_url)
    if not notes:
        logger.info("No notes found or fetch failed")
        return []

    post_to_digest = load_digest_history(digest_history_path)
    if not post_to_digest:
        logger.info("No digest history — nothing to match against")
        return []

    log = load_reshare_log(reshare_log_path)
    seen_note_ids = set(log.get("seen_note_ids", []))

    new_reshares: list[dict] = []

    for item in notes:
        note_id = item.get("entity_key", "")

        # Skip already-processed notes
        if note_id in seen_note_ids:
            continue

        reshare = parse_note(item)
        if not reshare:
            continue

        post_id = reshare["post_id"]
        if post_id and post_id in post_to_digest:
            reshare["digest_date"] = post_to_digest[post_id]
            reshare["matched"] = True
            new_reshares.append(reshare)
            logger.info(
                f"Reshare matched: \"{reshare['title'][:50]}\" "
                f"(digest {reshare['digest_date']})"
            )
        else:
            # Reshare of something not from the digest — still interesting to log
            reshare["digest_date"] = None
            reshare["matched"] = False
            new_reshares.append(reshare)
            logger.info(
                f"Reshare (not from digest): \"{reshare['title'][:50]}\""
            )

        seen_note_ids.add(note_id)

    # Update log
    log["reshares"].extend(new_reshares)
    log["seen_note_ids"] = list(seen_note_ids)
    save_reshare_log(log, reshare_log_path)

    matched = [r for r in new_reshares if r["matched"]]
    unmatched = [r for r in new_reshares if not r["matched"]]
    logger.info(
        f"Feedback check: {len(matched)} digest matches, "
        f"{len(unmatched)} other reshares, "
        f"{len(notes)} total notes scanned"
    )

    # Flag unmatched-reshare publications as watchlist candidates.
    if unmatched:
        flag_publications_from_unmatched(
            unmatched,
            user_substack_url=substack_url,
            watchlist_path=watchlist_path,
            candidates_path=candidates_path,
        )

    return new_reshares
