"""Stage 2 Enrichment: extract quotes and generate reshare angles using Gemini 3.1 Pro."""

import json
import logging
import os

from dotenv import load_dotenv
from google import genai
from pydantic import ValidationError

from src.models import ScoredPost, EnrichedPost, EnrichmentResult
from src.utils import fetch_post_content, strip_html

load_dotenv()
logger = logging.getLogger("pipeline.enrich")

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        _client = genai.Client(api_key=api_key)
    return _client


EDITORIAL_CONTEXT = """Josh Kinberg is a product leader with 15+ years of experience at NBC News Group,
building audience products at the intersection of media, technology, and AI. He writes about
product leadership, AI-assisted workflows, media industry dynamics, and the craft of building
with AI. His Substack covers: civic data journalism with AI tools, product org design,
human-AI collaboration, leadership under uncertainty, and behind-the-curtain build logs.

His reshare commentary should reflect: real experience (not theory), a product leader's lens
on media/AI topics, willingness to share contrarian takes, and genuine engagement with the
creator community rather than self-promotion."""


def _build_enrichment_prompt(post: ScoredPost, full_text: str) -> str:
    """Build the Stage 2 enrichment prompt."""
    themes = ", ".join(post.score.theme_clusters) or "general"

    return f"""You are helping a Substack creator identify the best quotable moment and reshare angles for a post they want to reshare with commentary on Substack Notes.

CREATOR CONTEXT:
{EDITORIAL_CONTEXT}

POST DETAILS:
Title: {post.post.title}
Author: {post.post.author_name} ({post.post.publication_name})
Matched themes: {themes}
Score reason: {post.score.one_line_reason}

FULL POST TEXT:
{full_text[:8000]}

INSTRUCTIONS:
1. Extract the single best quotable moment (1-3 sentences) that would work well in a reshare. The quote should be specific, insightful, and invite commentary — not a generic summary.
2. Explain briefly why this quote works for a reshare.
3. Suggest exactly 3 reshare angles — specific ways Josh could add value with his commentary. Each angle should connect to his experience or perspective, not just summarize the post. Vary the types: personal experience, contrarian take, community question, connection to another trend, etc.

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "best_quote": "<the actual quoted text from the post — 1-3 sentences>",
  "quote_context": "<why this quote works for a reshare — 1 sentence>",
  "angles": [
    {{"angle": "<specific reshare angle>", "type": "<personal experience|contrarian take|community question|trend connection|build on this>"}},
    {{"angle": "<specific reshare angle>", "type": "<type>"}},
    {{"angle": "<specific reshare angle>", "type": "<type>"}}
  ]
}}"""


def _parse_enrichment_response(response_text: str) -> EnrichmentResult | None:
    """Parse and validate Claude's response into an EnrichmentResult."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON from enrichment response: {text[:200]}")
        return None

    try:
        return EnrichmentResult(**data)
    except ValidationError as e:
        logger.warning(f"Enrichment validation error: {e}")
        return None


def enrich_post(
    scored_post: ScoredPost,
    model: str = "gemini-3.1-pro-preview",
) -> EnrichedPost | None:
    """Enrich a single high-scoring post with quotes and angles.

    Fetches full content, sends to Gemini 3.1 Pro, returns EnrichedPost.
    Returns None if content fetch or LLM call fails.
    """
    post = scored_post.post

    # Fetch full content
    html = fetch_post_content(post.publication_url, post.slug)
    if not html:
        logger.warning(f"Could not fetch content for '{post.title[:50]}' — skipping enrichment")
        return None

    full_text = strip_html(html)
    if len(full_text) < 100:
        logger.warning(f"Content too short for '{post.title[:50]}' ({len(full_text)} chars) — skipping")
        return None

    # Call Gemini 3.1 Pro
    client = _get_client()
    prompt = _build_enrichment_prompt(scored_post, full_text)

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            result = _parse_enrichment_response(response.text)
            if result:
                return EnrichedPost(
                    post=post,
                    score=scored_post.score,
                    enrichment=result,
                    full_text=full_text[:5000],  # Store truncated for reference
                )
            logger.warning(f"Attempt {attempt+1}: unparseable enrichment for '{post.title[:50]}'")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}: enrichment API error for '{post.title[:50]}': {e}")

    return None


def enrich_top_posts(
    scored_posts: list[ScoredPost],
    threshold: int = 7,
    config: dict | None = None,
) -> tuple[list[EnrichedPost], list[ScoredPost]]:
    """Enrich posts scoring at or above the high signal threshold.

    Returns:
        (enriched_posts, failed_posts) — enriched results and posts that failed enrichment
    """
    if config is None:
        from src.score import load_pipeline_config
        config = load_pipeline_config()

    model = config.get("scoring", {}).get("stage2_model", "gemini-3.1-pro-preview")
    high_signal = [sp for sp in scored_posts if sp.score.total_score >= threshold]

    logger.info(f"Enriching {len(high_signal)} posts scoring >= {threshold}")

    enriched: list[EnrichedPost] = []
    failed: list[ScoredPost] = []

    for i, sp in enumerate(high_signal):
        result = enrich_post(sp, model=model)
        if result:
            enriched.append(result)
            logger.info(f"[{i+1}/{len(high_signal)}] Enriched: {sp.post.title[:60]}")
        else:
            failed.append(sp)
            logger.warning(f"[{i+1}/{len(high_signal)}] Failed enrichment: {sp.post.title[:60]}")

    logger.info(f"Enrichment complete: {len(enriched)} enriched, {len(failed)} failed")
    return enriched, failed
