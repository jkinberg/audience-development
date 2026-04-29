"""Weekly review: surface reshare-candidate publications worth promoting to the watchlist.

Reads data/reshare_candidates.json (written by src/feedback.flag_publications_from_unmatched).
Identifies candidates with >=2 reshares (worth adding) and 1-reshare entries older than
4 weeks (worth pruning), and posts a GitHub issue if there's anything to surface.

Designed to be invoked by cloud_run.py once a week. Exits cleanly with no issue if the
candidates list has nothing actionable.

Auth:
    GITHUB_TOKEN env var: a PAT with `repo` scope on the target repo.
    GITHUB_REPO env var: e.g. "jkinberg/audience-development". Defaults to that.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

logger = logging.getLogger("review_candidates")

CANDIDATES_PATH = "data/reshare_candidates.json"
WATCHLIST_PATH = "config/watchlist.json"
DEFAULT_REPO = "jkinberg/audience-development"
PROMOTE_THRESHOLD = 2
STALE_AFTER_WEEKS = 4


def load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def categorize_candidates(candidates: list[dict], now: datetime) -> tuple[list[dict], list[dict]]:
    """Split candidates into (to_promote, to_prune) lists."""
    to_promote: list[dict] = []
    to_prune: list[dict] = []
    stale_cutoff = now - timedelta(weeks=STALE_AFTER_WEEKS)

    for c in candidates:
        count = c.get("reshare_count", 0)
        if count >= PROMOTE_THRESHOLD:
            to_promote.append(c)
            continue

        if count == 1:
            first = parse_iso(c.get("first_reshared", ""))
            if first and first < stale_cutoff:
                to_prune.append(c)

    return to_promote, to_prune


def render_issue_body(to_promote: list[dict], to_prune: list[dict]) -> str:
    parts: list[str] = []

    if to_promote:
        parts.append(f"## Pubs to consider adding ({len(to_promote)})\n")
        parts.append(
            f"You've reshared posts from these publications {PROMOTE_THRESHOLD}+ times "
            "but they're not in your watchlist yet:\n"
        )
        for c in to_promote:
            parts.append(
                f"- **{c.get('name', 'Unknown')}** — {c.get('url', '')} "
                f"({c.get('reshare_count', 0)} reshares)"
            )
            example = c.get("example_post", "")
            if example:
                parts.append(f"  - Example: _{example}_")
        parts.append("")

    if to_prune:
        parts.append(f"## Stale single-reshare candidates ({len(to_prune)})\n")
        parts.append(
            f"Reshared once more than {STALE_AFTER_WEEKS} weeks ago and never again — "
            "consider whether to keep tracking:\n"
        )
        for c in to_prune:
            parts.append(
                f"- {c.get('name', 'Unknown')} — {c.get('url', '')} "
                f"(first reshared {c.get('first_reshared', '?')[:10]})"
            )
        parts.append("")

    parts.append("---")
    parts.append(
        "To add a publication: edit `config/watchlist.json` and add an entry with "
        "`\"source\": \"reshare\"`. The auto-add path in `src/subscriptions.py` only "
        "covers actual Substack subscriptions — reshare candidates are surfaced for review, "
        "not auto-added."
    )
    parts.append(
        "\nTo dismiss a candidate: remove it from `data/reshare_candidates.json` "
        "(in GCS: `gs://audience-development-agents-state/data/reshare_candidates.json`)."
    )
    return "\n".join(parts)


def post_github_issue(repo: str, token: str, title: str, body: str) -> str:
    """Create a GitHub issue and return its URL."""
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"title": title, "body": body, "labels": ["watchlist-review"]}
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    return r.json().get("html_url", "")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    data = load_json(CANDIDATES_PATH)
    candidates = data.get("candidates", [])
    if not candidates:
        logger.info("No reshare candidates — nothing to review")
        return 0

    now = datetime.now(timezone.utc)
    to_promote, to_prune = categorize_candidates(candidates, now)

    if not to_promote and not to_prune:
        logger.info(
            f"{len(candidates)} candidate(s) on file, but none meet promote/prune thresholds"
        )
        return 0

    today = now.strftime("%Y-%m-%d")
    title = f"Watchlist candidate review — {today}"
    body = render_issue_body(to_promote, to_prune)

    if os.getenv("REVIEW_DRY_RUN"):
        logger.info("DRY RUN — would post issue:")
        logger.info(f"Title: {title}")
        logger.info(f"Body:\n{body}")
        return 0

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN not set — printing issue contents instead of posting")
        logger.info(f"Title: {title}")
        logger.info(f"Body:\n{body}")
        return 0

    repo = os.getenv("GITHUB_REPO", DEFAULT_REPO)
    try:
        issue_url = post_github_issue(repo, token, title, body)
        logger.info(f"Opened issue: {issue_url}")
    except Exception as e:
        logger.error(f"Failed to post GitHub issue: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
