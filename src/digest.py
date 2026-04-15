"""Digest Generator: assemble scored + enriched posts into markdown digest."""

import json
import logging
from datetime import datetime
from pathlib import Path

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
    lines.append(f"# Signal Pipeline — {date} — {len(entries)} posts worth your attention")
    lines.append("")

    # HIGH SIGNAL section
    if high_signal:
        lines.append(f"## HIGH SIGNAL ({len(high_signal)} posts, score ≥ 7)")
        lines.append("")

        for i, entry in enumerate(high_signal, 1):
            p = entry.post
            s = entry.score
            post_date = p.post_date.strftime("%B %d, %Y")
            themes = ", ".join(s.theme_clusters) if s.theme_clusters else "general"

            lines.append(f"### {i}. {p.title}")
            lines.append(f"**by {p.author_name} · {p.publication_name} · {post_date}**")
            lines.append(f"Score: {s.total_score}/10 | Themes: {themes}")
            lines.append("")

            if entry.enrichment:
                lines.append(f"> \"{entry.enrichment.best_quote}\"")
                lines.append("")
                if entry.enrichment.quote_context:
                    lines.append(f"*{entry.enrichment.quote_context}*")
                    lines.append("")
                lines.append("**Reshare angles:**")
                for angle in entry.enrichment.angles:
                    angle_type = angle.get("type", "")
                    angle_text = angle.get("angle", "")
                    if angle_type:
                        lines.append(f"- **[{angle_type}]** {angle_text}")
                    else:
                        lines.append(f"- {angle_text}")
                lines.append("")
            else:
                lines.append(f"*{s.one_line_reason}*")
                lines.append("")

            lines.append(f"[Read post →]({p.canonical_url})")
            lines.append("")
            lines.append("---")
            lines.append("")

    # WORTH A LOOK section
    if worth_a_look:
        lines.append(f"## WORTH A LOOK ({len(worth_a_look)} posts, score 6)")
        lines.append("")

        for i, entry in enumerate(worth_a_look, len(high_signal) + 1):
            p = entry.post
            s = entry.score
            themes = ", ".join(s.theme_clusters) if s.theme_clusters else "general"

            lines.append(f"**{i}. {p.title}**")
            lines.append(f"by {p.author_name} · {p.publication_name} · Score: {s.total_score}/10 | {themes}")
            lines.append(f"*{s.one_line_reason}*")
            lines.append(f"[Read post →]({p.canonical_url})")
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
        for err in stats.get("error_details", []):
            lines.append(f"  - {err.get('publication', '?')}: {err.get('error', '?')}")
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
