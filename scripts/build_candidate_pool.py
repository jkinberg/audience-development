"""LinkedIn Day 0 helper: score Connections.csv rows and emit a candidate pool.

Reads a LinkedIn data-export Connections.csv, scores each row by
seniority + relevance keywords, and writes a markdown table of the
top-N candidates. Used in Day 0 Step 0 to narrow ~2,000 connections
down to a ~150-row enrichment batch.

Position/Company fields in Connections.csv are at-time-of-connection
and may be stale. Score uses durable signals only: a senior title is
likely still senior; a relevant industry/role keyword suggests
possible current relevance. The output is NOT a finalist list —
it's the batch to send through profile enrichment so sample selection
can happen from current data.

Recency is intentionally not scored. Connection date doesn't correlate
with current data accuracy (LinkedIn doesn't refresh the Position
field after connection time), so a recency bonus would mislead.
Within each score band, results are sorted by connection date
descending purely as a UI hint — recent rows appear first.

Usage:
    python scripts/build_candidate_pool.py \\
        --connections /path/to/Connections.csv \\
        --output /path/to/candidate-pool.md \\
        --top 150
"""

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


SENIORITY_KEYWORDS = [
    "vp", "vice president", "svp", "evp",
    "director", "head of", "chief", "c-suite",
    "founder", "co-founder", "president", "ceo", "cto", "cpo", "cmo", "coo",
    "managing director", "general manager", "executive",
    "partner", "principal",
]

RELEVANCE_KEYWORDS = [
    # News / journalism orgs
    "nbc", "msnbc", "cnbc", "nbcuniversal", "nbcuni",
    "cnn", "nytimes", "new york times", "bloomberg", "reuters",
    "politico", "wsj", "wall street journal", "axios", "washington post",
    "vox", "vice", "buzzfeed", "guardian", "associated press",
    "abc news", "cbs news", "fox news", "propublica",
    "the athletic", "insider", "semafor", "puck", "atlantic",

    # News / journalism descriptors
    "news", "journalism", "newsroom", "newspaper", "newsletter",
    "editorial", "reporter", "correspondent", "anchor",

    # Streaming / entertainment
    "netflix", "hulu", "disney", "paramount", "warner",
    "peacock", "hbo", "spotify", "youtube", "tiktok",
    "streaming", "entertainment",

    # AI labs
    "openai", "anthropic", "perplexity", "cohere", "mistral",
    "artificial intelligence", "machine learning",

    # Product / audience / growth roles
    "product", "audience", "growth", "strategy",
    "editorial technology", "general management",

    # Generic "media"
    "media",
]


def has_keyword(text: str, keywords: list[str]) -> bool:
    """Return True if any keyword appears in text.

    Short single-word keywords use word-boundary matching to avoid
    substring false positives (e.g. "vp" matching "savepoint").
    Longer keywords and multi-word phrases use plain substring match.
    """
    if not text:
        return False
    text_lower = text.lower()
    for kw in keywords:
        if len(kw) <= 4 and " " not in kw and "-" not in kw:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                return True
        else:
            if kw in text_lower:
                return True
    return False


def parse_connected_on(date_str: str) -> datetime | None:
    """Parse '14 Apr 2026' style date. Returns None on failure."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d %b %Y")
    except ValueError:
        return None


def score_row(row: dict) -> int:
    position = row.get("Position") or ""
    company = row.get("Company") or ""
    combined = f"{position} {company}"

    score = 0
    if has_keyword(position, SENIORITY_KEYWORDS):
        score += 3
    if has_keyword(combined, RELEVANCE_KEYWORDS):
        score += 2
    return score


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--connections", required=True, type=Path,
        help="Path to Connections.csv from LinkedIn data export",
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Output path for candidate-pool.md (put it in your private location)",
    )
    parser.add_argument(
        "--top", type=int, default=150,
        help="Number of top-ranked candidates to emit (default 150 — Day 0 enrichment batch size)",
    )
    parser.add_argument(
        "--skip-rows", type=int, default=3,
        help="Preamble rows to skip before the header (default 3; LinkedIn export has 3)",
    )
    args = parser.parse_args()

    with args.connections.open(encoding="utf-8") as f:
        for _ in range(args.skip_rows):
            next(f)
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        row["_score"] = score_row(row)

    def sort_key(row: dict) -> tuple:
        connected = parse_connected_on(row.get("Connected On", ""))
        date_val = connected.timestamp() if connected else 0
        return (-row["_score"], -date_val)

    rows.sort(key=sort_key)
    scored_rows = [r for r in rows if r["_score"] > 0]
    top_rows = scored_rows[: args.top]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        f.write(f"# Candidate Pool — Top {len(top_rows)}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Source: `{args.connections}`\n")
        f.write(f"Scoring: seniority (3) + relevance (2). Recency not scored (would mislead — see script docstring).\n\n")
        f.write(
            "**Note:** `Position` and `Company` are at time of connection — stale for older entries. "
            "This pool is the **enrichment batch**, not a finalist list. Run head-to-head profile enrichment "
            "(Day 0 Step 2) on these rows, then pick sample profiles from the enriched data based on current roles.\n\n"
        )
        f.write("| # | Score | Name | Position (stale) | Company (stale) | Connected | URL |\n")
        f.write("|---|-------|------|------------------|-----------------|-----------|-----|\n")
        for i, row in enumerate(top_rows, 1):
            name = f"{row.get('First Name', '').strip()} {row.get('Last Name', '').strip()}".strip()
            position = (row.get("Position") or "").replace("|", r"\|").strip()
            company = (row.get("Company") or "").replace("|", r"\|").strip()
            connected_on = (row.get("Connected On") or "").strip()
            url = (row.get("URL") or "").strip()
            f.write(
                f"| {i} | {row['_score']} | {name} | {position} | {company} | {connected_on} | {url} |\n"
            )

    score_counts: dict[int, int] = {}
    for r in rows:
        score_counts[r["_score"]] = score_counts.get(r["_score"], 0) + 1
    print(f"Total rows read: {len(rows)}")
    print("Score distribution:")
    for score in sorted(score_counts.keys(), reverse=True):
        print(f"  {score}: {score_counts[score]} rows")
    print(f"\nWrote top {len(top_rows)} to {args.output}")


if __name__ == "__main__":
    main()
