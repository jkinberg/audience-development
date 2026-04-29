"""Subscription Sync: pull the user's Substack subscriptions/follows into the watchlist."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from substack_api import Newsletter, User

logger = logging.getLogger("pipeline.subscriptions")


def _normalize_url(domain: str) -> str:
    """Convert a bare domain into a canonical https URL with no trailing slash."""
    domain = domain.strip().rstrip("/").lower()
    if domain.startswith("http://"):
        domain = domain[len("http://"):]
    elif domain.startswith("https://"):
        domain = domain[len("https://"):]
    return f"https://{domain}"


def _watchlist_keys(publications: list[dict]) -> set[str]:
    """Build a set of normalized URL keys for fast membership checks."""
    keys: set[str] = set()
    for pub in publications:
        url = pub.get("url", "")
        if url:
            keys.add(_normalize_url(url.replace("https://", "").replace("http://", "")))
    return keys


def fetch_user_subscriptions(handle: str) -> list[dict]:
    """Fetch the user's public Substack subscriptions via substack_api."""
    user = User(handle)
    return user.get_subscriptions()


def _resolve_canonical_subdomain(url: str) -> str:
    """Resolve a Substack pub URL to its canonical *.substack.com form.

    Custom-domain pubs (e.g. blog.brianbalfour.com) and *.substack.com URLs
    point to the same publication. Fetches one archive entry to read the
    pub's subdomain. Returns the original URL on failure.
    """
    try:
        nl = Newsletter(url)
        posts = nl.get_posts(limit=1)
        if not posts:
            return url
        meta = posts[0].get_metadata()
        bylines = meta.get("publishedBylines", [])
        if not bylines:
            return url
        for pu in bylines[0].get("publicationUsers", []):
            subdomain = pu.get("publication", {}).get("subdomain", "")
            if subdomain:
                return f"https://{subdomain}.substack.com"
    except Exception as e:
        logger.debug(f"Failed to resolve canonical for {url}: {e}")
    return url


def diff_subscriptions(
    subscriptions: list[dict],
    watchlist: list[dict],
) -> list[dict]:
    """Return list of subscription dicts not already represented in the watchlist.

    Custom-domain subscriptions (e.g. blog.brianbalfour.com) are resolved to
    their canonical *.substack.com URL before comparison so they match
    existing subdomain-form entries in the watchlist.
    """
    existing = _watchlist_keys(watchlist)
    new_pubs: list[dict] = []
    seen_in_pass: set[str] = set()

    for sub in subscriptions:
        domain = sub.get("domain", "")
        if not domain:
            continue
        url = _normalize_url(domain)

        if url in existing:
            continue

        # Resolve custom domains to canonical subdomain to catch aliases.
        if not domain.endswith(".substack.com"):
            canonical = _resolve_canonical_subdomain(url)
            if canonical != url and canonical in existing:
                logger.info(f"Skipping {url} — resolves to existing watchlist entry {canonical}")
                continue
            target_url = canonical
        else:
            target_url = url

        if target_url in seen_in_pass:
            continue
        seen_in_pass.add(target_url)

        new_pubs.append({
            "url": target_url,
            "name": sub.get("publication_name", "").lstrip("@"),
            "author": "",
            "tier": 2,
            "added": datetime.now().strftime("%Y-%m-%d"),
            "source": "subscription",
        })

    return new_pubs


def sync_subscriptions_to_watchlist(
    handle: str | None = None,
    watchlist_path: str = "config/watchlist.json",
) -> list[dict]:
    """Fetch the user's subs, append any new ones to the watchlist.

    Returns the list of newly added publications. Writes the updated watchlist
    in-place. No-ops gracefully if the handle is unset or the API fails.
    """
    handle = handle or os.getenv("SUBSTACK_HANDLE")
    if not handle:
        logger.info("No SUBSTACK_HANDLE configured — skipping subscription sync")
        return []

    try:
        subs = fetch_user_subscriptions(handle)
    except Exception as e:
        logger.warning(f"Failed to fetch subscriptions for {handle}: {e}")
        return []

    logger.info(f"Fetched {len(subs)} Substack subscriptions for {handle}")

    path = Path(watchlist_path)
    with open(path) as f:
        wl_data = json.load(f)
    publications = wl_data.get("publications", [])

    new_pubs = diff_subscriptions(subs, publications)
    if not new_pubs:
        logger.info("Subscription sync: no new publications to add")
        return []

    publications.extend(new_pubs)
    wl_data["publications"] = publications
    with open(path, "w") as f:
        json.dump(wl_data, f, indent=2)

    logger.info(
        f"Subscription sync: added {len(new_pubs)} new publication(s) to watchlist"
    )
    for p in new_pubs:
        logger.info(f"  + {p['name']} ({p['url']})")

    return new_pubs
