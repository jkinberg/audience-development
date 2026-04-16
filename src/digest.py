"""Digest Generator: assemble scored + enriched posts into markdown digest."""

import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from src.models import ScoredPost, EnrichedPost, DigestEntry, DigestRun

logger = logging.getLogger("pipeline.digest")


def build_digest_entries(
    scored_posts: list[ScoredPost],
    enriched_posts: list[EnrichedPost],
    high_signal_threshold: int = 7,
    digest_threshold: int = 6,
) -> list[DigestEntry]:
    """Build digest entries from scored and enriched posts.

    Posts scoring >= high_signal_threshold get enrichment data.
    Posts scoring == digest_threshold - 1 below that get listed as WORTH A LOOK.
    """
    enriched_by_id = {ep.post.post_id: ep for ep in enriched_posts}

    entries: list[DigestEntry] = []
    for sp in sorted(scored_posts, key=lambda x: x.score.total_score, reverse=True):
        score = sp.score.total_score
        if score >= high_signal_threshold:
            ep = enriched_by_id.get(sp.post.post_id)
            entries.append(DigestEntry(
                post=sp.post,
                score=sp.score,
                enrichment=ep.enrichment if ep else None,
                tier="high_signal",
            ))
        elif score >= digest_threshold:
            entries.append(DigestEntry(
                post=sp.post,
                score=sp.score,
                enrichment=None,
                tier="worth_a_look",
            ))

    return entries


def render_markdown(
    entries: list[DigestEntry],
    stats: dict,
    date: str | None = None,
) -> str:
    """Render digest entries into a markdown document."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    high_signal = [e for e in entries if e.tier == "high_signal"]
    worth_a_look = [e for e in entries if e.tier == "worth_a_look"]

    lines: list[str] = []
    lines.append(f"# Substack Signal Pipeline — {date}")
    lines.append(f"*{len(entries)} posts from {stats.get('publications_monitored', 0)} publications*")
    lines.append("")

    # HIGH SIGNAL section
    if high_signal:
        for i, entry in enumerate(high_signal, 1):
            p = entry.post
            s = entry.score
            post_date = p.post_date.strftime("%b %d")
            themes = ", ".join(s.theme_clusters) if s.theme_clusters else ""

            lines.append(f"## {i}. [{p.title}]({p.substack_url or p.canonical_url})")
            lines.append(f"{p.author_name} · {p.publication_name} · {post_date} · {s.total_score}/10")
            if themes:
                lines.append(f"*{themes}*")
            lines.append("")

            if entry.enrichment:
                lines.append(entry.enrichment.summary)
                lines.append("")
                for quote in entry.enrichment.pull_quotes:
                    lines.append(f"> {quote}")
                    lines.append("")
            else:
                lines.append(s.one_line_reason)
                lines.append("")

            lines.append("---")
            lines.append("")

    # WORTH A LOOK section
    if worth_a_look:
        lines.append("## Also noted")
        lines.append("")

        start_num = len(high_signal) + 1
        for i, entry in enumerate(worth_a_look, start_num):
            p = entry.post
            s = entry.score
            lines.append(f"{i}. [{p.title}]({p.substack_url or p.canonical_url}) — {p.author_name} · {s.one_line_reason}")

        lines.append("")
        lines.append("---")
        lines.append("")

    # No results
    if not entries:
        lines.append("*No posts scored above threshold today.*")
        lines.append("")
        lines.append("---")
        lines.append("")

    # PIPELINE STATS
    lines.append("## PIPELINE STATS")
    lines.append(f"- Publications monitored: {stats.get('publications_monitored', 0)}")
    lines.append(f"- New posts scanned: {stats.get('posts_scanned', 0)}")
    lines.append(f"- Posts scoring ≥ 7 (HIGH SIGNAL): {stats.get('high_signal_count', 0)}")
    lines.append(f"- Posts scoring 6 (WORTH A LOOK): {stats.get('worth_a_look_count', 0)}")
    if stats.get("fetch_errors", 0) > 0:
        lines.append(f"- Fetch errors: {stats['fetch_errors']}")
    if stats.get("scoring_failures", 0) > 0:
        lines.append(f"- Scoring failures: {stats['scoring_failures']}")
    if stats.get("enrichment_failures", 0) > 0:
        lines.append(f"- Enrichment failures: {stats['enrichment_failures']}")
    lines.append(f"- Pipeline run: {date}")
    lines.append("")

    return "\n".join(lines)


def write_digest(markdown: str, digest_dir: str = "output/digests", date: str | None = None) -> Path:
    """Write markdown digest to file."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    path = Path(digest_dir)
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{date}.md"
    filepath.write_text(markdown)
    logger.info(f"Digest written to {filepath}")
    return filepath


def update_digest_history(
    entries: list[DigestEntry],
    posts_scanned: int,
    date: str | None = None,
    history_path: str = "data/digest_history.json",
) -> None:
    """Append this run to digest history for deduplication."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(history_path) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"digests": []}

    run = DigestRun(
        date=date,
        post_ids=[e.post.post_id for e in entries],
        posts_scanned=posts_scanned,
        posts_in_digest=len(entries),
    )
    history["digests"].append(run.model_dump())

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"Digest history updated: {len(entries)} posts recorded for {date}")


def send_to_zapier(
    markdown: str,
    entries: list[DigestEntry],
    stats: dict,
    webhook_url: str,
    date: str | None = None,
) -> bool:
    """POST digest to Zapier webhook. Returns True on success."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    high_signal = [
        {
            "title": e.post.title,
            "author": e.post.author_name,
            "publication": e.post.publication_name,
            "url": e.post.canonical_url,
            "score": e.score.total_score,
            "themes": e.score.theme_clusters,
            "summary": e.enrichment.summary if e.enrichment else None,
            "pull_quotes": e.enrichment.pull_quotes if e.enrichment else [],
        }
        for e in entries if e.tier == "high_signal"
    ]

    payload = {
        "date": date,
        "digest_markdown": markdown,
        "high_signal_count": stats.get("high_signal_count", 0),
        "posts_scanned": stats.get("posts_scanned", 0),
        "high_signal": high_signal,
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info(f"Zapier webhook sent successfully ({resp.status_code})")
        return True
    except Exception as e:
        logger.warning(f"Zapier webhook failed (non-blocking): {e}")
        return False
