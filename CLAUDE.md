# Audience Development — Signal-Based Content Pipeline

## Project Overview
A content pipeline for Substack audience development. Monitors ~44 publications, scores posts against a Signal Profile (5 theme clusters), and surfaces reshare candidates via daily markdown digest.

## Architecture
- **Language:** Python 3.14
- **Substack data:** Raw Substack API for daily fetches (`/api/v1/archive`, `/api/v1/posts/{slug}`). Library (`substack_api`) used only for discovery (`get_recommendations()`, `User`, `Category`).
- **Scoring (Stage 1):** Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite-preview`) — classifies posts from metadata only. Temp 0.
- **Enrichment (Stage 2):** Gemini 3.1 Pro (`gemini-3.1-pro-preview`) — full content fetch + quote extraction + angle suggestions. Only for posts scoring ≥ 7. Claude Sonnet (`claude-sonnet-4-20250514`) as fallback.
- **Config:** JSON files in `config/` — watchlist, signal_profile, pipeline settings
- **Output:** Markdown digest in `output/digests/`. Zapier webhook is a future feature.
- **Data models:** Pydantic models in `src/models.py` for typed data flow between stages
- **Runtime:** Local dev now, cloud cron (GitHub Actions or Railway) for production

## Key Technical Decisions
- Raw Substack archive API for daily batch pulls (library has bugs with cross-posts and redirects)
- Slug-based content fetch (`/api/v1/posts/{slug}`) for full text — more reliable than library's ID-based fetch
- Two-stage scoring: metadata-only Stage 1 (all posts via Gemini Flash), full content Stage 2 (posts ≥ 7 via Sonnet/Pro)
- Substack Notes API is NOT publicly accessible — feedback.py deferred to Week 2 with manual fallback
- Intermediate state files in `data/runs/YYYY-MM-DD/` for resumable pipeline runs

## Project Structure
```
src/                — pipeline source code (models, fetch, score, enrich, digest, discover, utils)
config/             — runtime config (watchlist.json, signal_profile.json, pipeline.json)
data/               — runtime data (digest_history.json, reshare_log.json, runs/, discovery_candidates.json)
output/digests/     — generated markdown digests
scripts/            — entry points (run_pipeline.py, run_discovery.py, day0_validation.py)
planning/           — strategy docs, project briefs, Day 0 findings
docs/plans/         — design documents
corpus/             — reaction data exports (LinkedIn, Substack articles)
tests/golden_set/   — scoring validation posts (to be populated)
```

## Commands
```bash
source .venv/bin/activate              # activate virtualenv
python scripts/day0_validation.py      # API validation
python -c "from src.fetch import load_watchlist, fetch_all_posts; ..."  # test fetch
```

## Build Status (as of 2026-04-14)
- **Day 0:** Complete — API validated, findings documented
- **Day 1:** Complete — fetch, discover, watchlist expanded to 44 publications, Notes API validated (not available)
- **Day 2:** Complete — score.py (Gemini 3.1 Flash Lite) + enrich.py (Gemini 3.1 Pro) built and tested. 47 posts scored, 5 enriched, zero failures.
- **Day 3:** Complete — digest.py + run_pipeline.py built. First real digest: 17 posts scanned, 7 HIGH SIGNAL enriched, zero failures. ~3.5 min runtime.
- **Next:** Days 4-5 polish + deploy (error handling, cloud cron, dedup across runs)

## Running the Pipeline
```bash
./run.sh                                       # full daily run (recommended)
```
Output: `output/digests/YYYY-MM-DD.md`

## Dependencies
Managed via pip in `.venv/` and `requirements.txt`. Key packages: substack_api, google-genai, anthropic, pydantic, beautifulsoup4, html2text, tenacity, python-dotenv.

## Environment Variables
```
GEMINI_API_KEY=     # Stage 1 scoring + discovery publication scoring
ANTHROPIC_API_KEY=  # Stage 2 enrichment (Claude Sonnet)
```
