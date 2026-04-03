# Knowledge Base — Audience Development Pipeline

## Day 0 Findings (2026-04-03)
- `substack_api` 1.2.0 works for post retrieval, recommendations, category browsing
- Global cross-Substack search is broken (404) — use recommendations + categories for discovery
- Library has bugs with cross-posted content and Notes-style URLs — use raw API for daily pipeline
- Raw archive API (`/api/v1/archive`) returns all metadata needed for scoring in one call per publication
- Full content available via slug-based fetch (`/api/v1/posts/{slug}`) without auth for free posts
- Rate limiting not an issue at 40-60 publications with 0.5s delays

## Substack Landscape (2026-04-03)
- Only ~8 of 15 watchlist authors have active Substack publications
- Many LinkedIn-followed authors are dormant, "coming soon," or guest contributors on other pubs
- The media/product/AI niche is sparse on Substack — discovery engine is essential
- Authors ≠ Publications: some authors contribute to other pubs (Claire Vo → Lenny's, Kenyatta → EAO)
- Current active watchlist is ~13 publications; need to grow to 40-60 via Phase 2 discovery
