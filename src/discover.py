"""Discovery Engine: expand watchlist via recommendation graph crawling."""

import json
import logging
from pathlib import Path

from substack_api import Newsletter

from src.models import DiscoveredPublication
from src.utils import fetch_archive, polite_delay

logger = logging.getLogger("pipeline.discover")


def crawl_recommendations(
    watchlist: list[dict],
    depth: int = 2,
    delay: float = 0.75,
) -> dict[str, dict]:
    """Crawl recommendation graphs from watchlist publications.

    Returns dict keyed by publication URL with metadata:
        {url: {"name": str, "recommended_by": [str], "depth": int}}
    """
    discovered: dict[str, dict] = {}
    watchlist_urls = {pub["url"].rstrip("/") for pub in watchlist}

    def _normalize_url(nl_obj) -> str | None:
        """Extract URL from a Newsletter object and ensure it has https:// prefix."""
        url = getattr(nl_obj, "url", None)
        if not url:
            return None
        url = url.rstrip("/")
        if not url.startswith("http"):
            url = f"https://{url}"
        return url

    # Depth 1: direct recommendations from watchlist
    depth1_urls: set[str] = set()

    for pub in watchlist:
        url = pub["url"]
        name = pub.get("name", url)

        try:
            nl = Newsletter(url)
            recs = nl.get_recommendations()
            logger.info(f"[depth 1] {name}: {len(recs)} recommendations")

            for rec in recs:
                rec_url = _normalize_url(rec)
                if not rec_url or rec_url in watchlist_urls:
                    continue

                if rec_url not in discovered:
                    discovered[rec_url] = {
                        "url": rec_url,
                        "name": "",
                        "recommended_by": [],
                        "depth": 1,
                    }
                if name not in discovered[rec_url]["recommended_by"]:
                    discovered[rec_url]["recommended_by"].append(name)
                depth1_urls.add(rec_url)

        except Exception as e:
            logger.warning(f"[depth 1] {name}: failed to get recommendations — {e}")

        polite_delay(delay)

    logger.info(f"Depth 1 complete: {len(depth1_urls)} unique publications discovered")

    # Depth 2: recommendations of recommendations
    if depth >= 2:
        for rec_url in list(depth1_urls):
            try:
                nl = Newsletter(rec_url)
                recs = nl.get_recommendations()

                for rec in recs:
                    rec2_url = _normalize_url(rec)
                    if not rec2_url or rec2_url in watchlist_urls:
                        continue

                    if rec2_url not in discovered:
                        discovered[rec2_url] = {
                            "url": rec2_url,
                            "name": "",
                            "recommended_by": [],
                            "depth": 2,
                        }
                    source_name = discovered.get(rec_url, {}).get("name", rec_url)
                    if source_name not in discovered[rec2_url]["recommended_by"]:
                        discovered[rec2_url]["recommended_by"].append(source_name)

            except Exception as e:
                logger.debug(f"[depth 2] {rec_url}: failed — {e}")

            polite_delay(delay * 0.5)  # Faster at depth 2

        logger.info(f"Depth 2 complete: {len(discovered)} total unique publications")

    return discovered


def score_discovered_publications(
    discovered: dict[str, dict],
    min_recent_posts: int = 3,
    delay: float = 0.5,
) -> list[DiscoveredPublication]:
    """Fetch recent posts from discovered publications and build candidate list.

    Scores publications by:
    - Number of watchlist pubs that recommend them (cross-reference count)
    - Number of recent posts (activity signal)
    - Depth (depth 1 > depth 2)

    Note: Full Signal Profile scoring via Gemini happens separately.
    This is a pre-filter to identify active, well-connected publications.
    """
    candidates: list[DiscoveredPublication] = []

    for url, info in discovered.items():
        try:
            raw_posts = fetch_archive(url, limit=5, timeout=10)

            if len(raw_posts) < min_recent_posts:
                continue

            # Extract publication name from first post
            pub_name = ""
            recent_titles = []
            author_name = ""
            for post in raw_posts[:5]:
                if not pub_name:
                    bylines = post.get("publishedBylines", [])
                    if bylines:
                        author_name = bylines[0].get("name", "")
                recent_titles.append(post.get("title", "Untitled"))

            # Simple scoring heuristic (pre-Gemini)
            cross_ref_score = min(len(info["recommended_by"]), 3)  # 0-3
            depth_score = 2 if info["depth"] == 1 else 1  # depth 1 is stronger
            activity_score = min(len(raw_posts), 3)  # 0-3
            score = cross_ref_score + depth_score + activity_score

            candidate = DiscoveredPublication(
                url=url,
                name=pub_name or url.split("//")[1].split(".")[0],
                author=author_name,
                score=score,
                recommended_by=info["recommended_by"],
                recent_posts=recent_titles,
                reason=f"Recommended by {len(info['recommended_by'])} watchlist pub(s). {len(raw_posts)} recent posts. Depth {info['depth']}.",
            )
            candidates.append(candidate)

        except Exception as e:
            logger.debug(f"Skipping {url}: {e}")

        polite_delay(delay)

    # Sort by score descending
    candidates.sort(key=lambda c: c.score, reverse=True)
    logger.info(f"Scored {len(candidates)} candidate publications from {len(discovered)} discovered")
    return candidates


def save_candidates(
    candidates: list[DiscoveredPublication],
    seed_count: int,
    total_discovered: int,
    output_path: str = "data/discovery_candidates.json",
) -> Path:
    """Save discovery results for human review."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "discovered_date": str(Path()),  # Will be set properly in run script
        "seed_publications": seed_count,
        "total_discovered": total_discovered,
        "candidates_after_filtering": len(candidates),
        "candidates": [c.model_dump() for c in candidates],
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(candidates)} candidates to {path}")
    return path
