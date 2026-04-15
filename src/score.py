"""Stage 1 Scorer: classify posts against Signal Profile using Gemini Flash."""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import ValidationError

from src.models import Post, Stage1Score, ScoredPost

load_dotenv()
logger = logging.getLogger("pipeline.score")

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        _client = genai.Client(api_key=api_key)
    return _client


def load_signal_profile(path: str = "config/signal_profile.json") -> dict:
    with open(path) as f:
        return json.load(f)


def load_pipeline_config(path: str = "config/pipeline.json") -> dict:
    with open(path) as f:
        return json.load(f)


def _build_scoring_prompt(post: Post, signal_profile: dict) -> str:
    """Build the Stage 1 scoring prompt for a single post."""
    clusters = signal_profile["theme_clusters"]
    noise_filters = signal_profile["noise_filters"]
    scoring = signal_profile["scoring"]

    cluster_text = "\n".join(
        f"  {i+1}. {c['name']} (Weight: {c['weight']}): {c['description']}"
        for i, c in enumerate(clusters)
    )

    noise_text = "\n".join(
        f"  - {f['name']}" + (f" (exception: {f['exception']})" if f.get("exception") else "")
        for f in noise_filters
    )

    # Build metadata text from what we have
    metadata_parts = [f"Title: {post.title}"]
    if post.subtitle:
        metadata_parts.append(f"Subtitle: {post.subtitle}")
    if post.description:
        metadata_parts.append(f"Description: {post.description}")
    if post.truncated_body_text:
        metadata_parts.append(f"Excerpt: {post.truncated_body_text}")
    metadata_parts.append(f"Author: {post.author_name}")
    if post.author_bio:
        metadata_parts.append(f"Author bio: {post.author_bio}")
    metadata_parts.append(f"Publication: {post.publication_name}")
    metadata_parts.append(f"Engagement: {post.reaction_count} reactions, {post.restacks} restacks, {post.comment_count} comments")
    if post.wordcount:
        metadata_parts.append(f"Word count: {post.wordcount}")

    post_text = "\n".join(metadata_parts)

    return f"""You are a content scoring system. Score this Substack post against the Signal Profile below.

SIGNAL PROFILE — THEME CLUSTERS:
{cluster_text}

NOISE FILTERS (reduce score or flag):
{noise_text}

SCORING RUBRIC:
- theme_fit (0-{scoring['theme_fit_max']}): How strongly does this match one or more theme clusters? Weight HIGH clusters more heavily.
- reshare_potential (0-{scoring['reshare_potential_max']}): Does this contain a specific insight, data point, or argument that invites commentary? A post worth resharing with a "here's my take" response scores high. Generic or purely informational posts score low.
- creator_value (0-{scoring['creator_value_max']}): Is the author in the target neighborhood (1K-50K subscribers, media/product/AI intersection)? Mega-accounts (500K+) score 0 unless the take is genuinely contrarian.
- total_score: Sum of theme_fit + reshare_potential + creator_value (0-10).

POST TO SCORE:
{post_text}

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "theme_fit": <int 0-{scoring['theme_fit_max']}>,
  "theme_clusters": [<list of matching cluster names>],
  "reshare_potential": <int 0-{scoring['reshare_potential_max']}>,
  "creator_value": <int 0-{scoring['creator_value_max']}>,
  "total_score": <int 0-10>,
  "noise_flag": <string or null>,
  "one_line_reason": "<one sentence explaining the score>"
}}"""


def _parse_score_response(response_text: str) -> Stage1Score | None:
    """Parse and validate Gemini's response into a Stage1Score."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON from response: {text[:200]}")
        return None

    # Clamp scores to valid ranges
    scoring_max = {"theme_fit": 5, "reshare_potential": 3, "creator_value": 2, "total_score": 10}
    for field, max_val in scoring_max.items():
        if field in data and isinstance(data[field], (int, float)):
            data[field] = max(0, min(int(data[field]), max_val))

    # Recalculate total if components don't sum
    if "theme_fit" in data and "reshare_potential" in data and "creator_value" in data:
        data["total_score"] = data["theme_fit"] + data["reshare_potential"] + data["creator_value"]

    try:
        return Stage1Score(**data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return None


def score_post(post: Post, signal_profile: dict, model: str = "gemini-3.1-flash-lite-preview", temperature: float = 0) -> Stage1Score | None:
    """Score a single post using Gemini Flash. Returns None on failure."""
    client = _get_client()
    prompt = _build_scoring_prompt(post, signal_profile)

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"temperature": temperature},
            )
            score = _parse_score_response(response.text)
            if score:
                return score
            logger.warning(f"Attempt {attempt+1}: unparseable response for '{post.title[:50]}'")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}: API error for '{post.title[:50]}': {e}")

    return None


def score_all_posts(
    posts: list[Post],
    signal_profile: dict | None = None,
    config: dict | None = None,
) -> list[ScoredPost]:
    """Score all posts against the Signal Profile.

    Returns list of ScoredPost objects (posts that failed scoring are skipped).
    """
    if signal_profile is None:
        signal_profile = load_signal_profile()
    if config is None:
        config = load_pipeline_config()

    model = config.get("scoring", {}).get("stage1_model", "gemini-2.5-flash")
    temperature = config.get("scoring", {}).get("stage1_temperature", 0)

    scored: list[ScoredPost] = []
    failed = 0

    for i, post in enumerate(posts):
        score = score_post(post, signal_profile, model=model, temperature=temperature)
        if score:
            scored.append(ScoredPost(post=post, score=score))
            logger.info(
                f"[{i+1}/{len(posts)}] {score.total_score}/10 — {post.title[:60]} "
                f"({', '.join(score.theme_clusters) or 'no themes'})"
            )
        else:
            failed += 1
            logger.warning(f"[{i+1}/{len(posts)}] FAILED — {post.title[:60]}")

    logger.info(f"Scoring complete: {len(scored)} scored, {failed} failed out of {len(posts)}")
    return scored


def save_scored_posts(scored: list[ScoredPost], run_dir: Path) -> Path:
    """Write scored posts to intermediate state file."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "scored.json"
    with open(path, "w") as f:
        json.dump([sp.model_dump(mode="json") for sp in scored], f, indent=2, default=str)
    return path
