"""Feedback Monitor: match reshared Notes against digest suggestions."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

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


def check_for_reshares(
    substack_url: str,
    digest_history_path: str = "data/digest_history.json",
    reshare_log_path: str = "data/reshare_log.json",
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

    return new_reshares
