# Audience Development — Signal-Based Content Pipeline

## Project Overview
A content pipeline for Substack audience development. Monitors publications, scores posts against a Signal Profile, and surfaces reshare candidates via daily digest.

## Architecture
- **Language:** Python 3.14
- **Substack data:** `substack_api` library + raw Substack API (`/api/v1/archive`, `/api/v1/posts/{slug}`)
- **Scoring:** Google Gemini Flash API for classification/scoring, not Claude (cost optimization)
- **Config:** JSON files for watchlist, Signal Profile, scoring thresholds, reshare history
- **Output:** Markdown digest, delivery mechanism TBD
- **Runtime:** Local dev, cloud deployment (TBD) for production cron

## Key Technical Decisions
- Use raw Substack archive API for daily batch pulls (library has bugs with cross-posts and redirects)
- Use slug-based content fetch (`/api/v1/posts/{slug}`) for full text — more reliable than library's ID-based fetch
- Use library's `User`, `Newsletter.get_recommendations()`, and `Category` classes where they work correctly
- Two-pass scoring: metadata-only pass 1 (all posts), full content pass 2 (posts scoring ≥ 6 only)

## Project Structure
```
planning/          — strategy docs, project briefs, Day 0 findings
corpus/            — reaction data exports (LinkedIn, Substack)
scripts/           — pipeline scripts and utilities
```

## Commands
```bash
source .venv/bin/activate    # activate virtualenv
python scripts/day0_validation.py  # run API validation
```

## Dependencies
Managed via pip in `.venv/`. No requirements.txt yet — create one before deployment.
