# Knowledge Base — Audience Development Pipeline

## Day 0 Findings (2026-04-03)
- `substack_api` 1.2.0 works for post retrieval, recommendations, category browsing
- Global cross-Substack search is broken (404) — use recommendations + categories for discovery
- Library has bugs with cross-posted content and Notes-style URLs — use raw API for daily pipeline
- Raw archive API (`/api/v1/archive`) returns all metadata needed for scoring in one call per publication
- Full content available via slug-based fetch (`/api/v1/posts/{slug}`) without auth for free posts
- Rate limiting not an issue at 40-60 publications with 0.5s delays
- Substack Notes/restack activity is NOT accessible via any public API endpoint — no endpoint found for user Notes, restacks, or activity feed without auth
- Open RSS (openrss.org) can theoretically generate an RSS feed from a Substack profile page (including Notes), but the service is unreliable — timed out during testing (2026-04-03). The original article (tinkeringwithideas.io) also noted server issues.
- Substack's built-in RSS (`/feed`) only returns newsletter posts, not Notes or restacks
- Feedback.py plan: manual CLI logger for Phase 1, revisit Open RSS or authenticated API later

## Substack Landscape (2026-04-03)
- Only ~8 of 15 original watchlist authors have active Substack publications
- Many LinkedIn-followed authors are dormant, "coming soon," or guest contributors on other pubs
- The media/product/AI niche is sparse on Substack — discovery engine is essential
- Authors ≠ Publications: some authors contribute to other pubs (Claire Vo → Lenny's, Kenyatta → EAO)

## Day 1 Build (2026-04-03)
- Watchlist expanded from 13 seed → 44 publications via recommendation graph crawl (depth 1)
- 21 Tier 1 + 23 Tier 2 publications, 13 seed + 31 discovered
- 3-day test fetch: 20 posts from 44 pubs, zero errors — volume looks right for 5-7 posts/day
- Discovery crawled 82 unique publications from 13 seeds, scored down to 77 candidates, ~31 approved
- Depth 2 crawling added zero new publications beyond depth 1 — recommend skipping depth 2 in future runs
- Newsletter.get_recommendations() returns URLs WITHOUT https:// prefix — must normalize in code
- feedback.py deferred to Week 2: Notes API not available, need manual fallback (CLI logger or digest marking)

## Key Publication URLs (non-obvious slugs)
- Julie Zhuo: `lg.substack.com` (The Looking Glass) + `opinionatedintelligence.substack.com`
- John Cutler: `cutlefish.substack.com` (The Beautiful Mess)
- Aakash Gupta: `www.news.aakashg.com` (custom domain)
- Lenny Rachitsky: `www.lennysnewsletter.com` (custom domain)

## Day 2 Build (2026-04-14)
- score.py and enrich.py built and tested end-to-end
- Gemini model IDs: `gemini-3.1-flash-lite-preview` (Stage 1), `gemini-3.1-pro-preview` (Stage 2)
- Claude Sonnet model ID: `claude-sonnet-4-20250514` (Stage 2 fallback)
- Note: `gemini-2.0-flash` is deprecated for new users — returns 404. Use 2.5 or 3.1 models.
- Stage 1 scoring: 47/47 posts scored, zero failures, good distribution (10/10 down to 0/10)
- Stage 2 enrichment: 5/5 posts enriched, zero failures, high-quality quotes and angles
- Noise filters working: mega-accounts flagged, milestone posts caught, off-topic content scored low
- 7-day fetch from 44 pubs: 47 posts. On daily cadence ~6-7 posts/day, expect 3-5 high signal after scoring.
- Full pipeline (fetch + score + enrich 5) runs in ~4 minutes

## Day 3 Build (2026-04-14)
- digest.py and run_pipeline.py built and tested end-to-end
- First digest was not useable — format was confusing, quotes out of context, reshare angles felt generic
- Reworked: replaced angles with 2-3 sentence article summaries + 1-3 pull quotes for scanning
- Title links are H2 headings with numbered entries, link is the first thing you see
- "Also noted" section for score-6 posts continues numbering from high signal
- Zapier webhook removed from config — delivery via local markdown file for now
- Run command: `PYTHONPATH=. python3 scripts/run_pipeline.py` (needs PYTHONPATH hack, should fix)
- Pipeline runtime ~3.5 min for 44 pubs, 18 posts scored, 7 enriched

## Design Decisions (from brainstorm + review, 2026-04-03)
- Two-stage scoring: Gemini 3.1 Flash (metadata, classification) → Sonnet/Gemini 3.1 Pro (full content, creative)
- Stage 1 threshold: score ≥ 7 = HIGH SIGNAL (gets enrichment), score 6 = WORTH A LOOK (no enrichment)
- Markdown-only output for Phase 1; Zapier webhook is a distinct future feature
- Pydantic models for all inter-stage data; intermediate state files for resumable runs
- Passive feedback loop (watch Josh's Substack activity) was preferred design, but Notes API unavailable
