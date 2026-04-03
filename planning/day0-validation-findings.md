# Day 0 Validation Findings: `substack_api` for Content Pipeline

**Date:** April 3, 2026  
**Status:** Complete  
**Verdict:** Build is viable. Proceed to Phase 1.  
**Build path:** Path B (per original brief) — no global search, but recommendations + category browsing + known watchlist monitoring are sufficient.

---

## What We Tested

- `Newsletter.get_posts()` — pull recent posts from publications
- `Post.get_metadata()` and `Post.get_content()` — per-post full content retrieval
- Raw archive API (`/api/v1/archive`) — batch metadata without per-post fetch
- `Newsletter.get_recommendations()` — recommendation graph for discovery
- `Newsletter.search_posts()` — search within a single publication
- Global cross-Substack search — attempted via `substack.com` base URL
- `list_all_categories()` and `Category.get_newsletter_urls()` — category-based discovery
- `User.get_raw_data()` — author profile lookup, publication associations, contributor roles
- Rate limiting behavior across multiple sequential requests

---

## The Discovery Challenge Is Real

The most important Day 0 finding isn't about the API — it's about the Substack landscape itself.

Of the ~15 authors from the project brief watchlist (drawn from LinkedIn reactions and Substack likes), we found:

- **~8 have active Substack publications** producing content regularly
- **~4 have dormant or "coming soon" publications** — they created a Substack but aren't publishing
- **~3 have no Substack publication at all** or publish only as occasional guest contributors on other people's publications

Substack is still a developing social network. Many of the media, product, and AI people I follow on LinkedIn haven't built an active Substack presence. Some are lurkers consuming content. Some post Notes occasionally. Some contribute guest posts to larger publications (e.g., Claire Vo publishing on Lenny's Newsletter). But few have established their own regular publications in the niche this project targets.

This makes the content pipeline **more valuable, not less.** You can't browse your way to good reshare candidates because the neighborhood is sparse and fragmented. The system needs to actively find and monitor the publications that *are* producing relevant content — and that set will change over time as more authors enter Substack and others go dormant.

The watchlist isn't "people I follow mapped to Substack URLs." It's a curated, actively maintained list of **publications producing reshare-worthy content right now.** Finding those is the core problem the system solves.

---

## API Capabilities: What Works

### Post retrieval and metadata
**Works reliably.** The raw archive API (`/api/v1/archive?sort=new&offset=0&limit=N`) returns rich metadata per post in a single request per publication:

- `title`, `subtitle`, `description`, `truncated_body_text` (~150 chars) — sufficient for theme scoring
- `post_date`, `wordcount` — recency and length filtering
- `reactions` (e.g. `{"❤": 25}`), `reaction_count`, `restacks`, `comment_count` — engagement metrics
- `publishedBylines` — author name, handle, bio (supports guest post detection)
- `canonical_url`, `slug` — linking, dedup, full content fetch
- `audience` — "everyone" vs. "only_paid" (paywall detection)

Tested successfully across: Evan Shapiro, Tim Shey (Creatorama), Brian Balfour, Aakash Gupta, Brad Stulberg, Julie Zhuo (both publications), Mike Troiano, Fort Human (Descript), John Cutler, Lenny's Newsletter, Everybody At Once, Felix Simon.

### Full post content (no auth)
**Works for free/public posts.** Full `body_html` available via per-post slug-based fetch (`/api/v1/posts/{slug}`). Content ranges from 7K to 51K chars. More than enough for quote extraction.

Not included in the archive list response — requires a second request per post. The two-pass approach (score from metadata first, fetch full content only for high-scoring posts) minimizes these extra calls.

### Author profile and publication lookup
**Works well.** `User.get_raw_data()` returns:
- `primaryPublication` — the author's main publication name and URL
- `publicationUsers` — all publications the author is associated with, including role (`admin`, `contributor`)

This is how we discovered Claire Vo contributes to Lenny's, Kenyatta Cheese contributes to Everybody At Once, and Julie Zhuo runs two separate publications.

### Recommendation graph
**Works.** `Newsletter.get_recommendations()` returned 11 recommended newsletters for Evan Shapiro, including Creatorama (Tim Shey). Returns Newsletter objects that can be queried recursively — viable for Phase 2 discovery.

### Category browsing
**Works.** 31 categories. `Category("Technology")` returned 525 newsletter URLs. A second discovery path for Phase 2.

### Within-publication search
**Works.** `search_posts("AI")` within a specific publication returned relevant results. Useful for finding topic-specific posts from a known publication.

### Rate limiting
**Not an issue at our scale.** 9+ sequential fetches with 0.5s delays completed cleanly. 40-60 publications daily should be fine.

---

## API Capabilities: What Doesn't Work

### Global cross-Substack search — BROKEN
`search_posts()` on `substack.com` (searching across all of Substack) returns 404. The library only searches within a single publication's archive.

**Impact:** Can't discover new publications by topic keyword via API. This was the primary discovery method in the original Neighborhood Mapper brief.

**Mitigation:** Recommendations + category browsing + manual curation cover this. Makes us Path B from the original brief.

### Library bugs with cross-posts and redirects
The `substack_api` library's `Post.get_metadata()` fails on:
- **Guest/cross-posted content** — when a publication hosts posts from another Substack (e.g., Julie Zhuo's The Looking Glass hosting Opinionated Intelligence content)
- **Notes-style canonical URLs** — some publications (e.g., Felix Simon) have posts where `canonical_url` uses a `p-{id}` format the library can't fetch

**Workaround:** Use the raw API directly instead of the library for the daily pipeline. The archive endpoint returns all metadata inline. Slug-based content fetch (`/api/v1/posts/{slug}`) works where the library's ID-based fetch fails. Both confirmed working.

---

## Architecture Decision: Library vs. Raw API

The library adds convenience but introduces fragility. Recommended hybrid approach:

| Function | Use | Reason |
|---|---|---|
| **Daily batch pull** | Raw archive API | Avoids library bugs. One request per publication. All scoring metadata inline. |
| **Full content fetch** | Raw slug-based fetch | More reliable than library's ID-based fetch. Only for posts scoring ≥ 6. |
| **Author → publication mapping** | Library `User` class | Works correctly. Needed for initial watchlist setup. |
| **Recommendation graph** | Library `Newsletter.get_recommendations()` | Works correctly. Phase 2 discovery. |
| **Category browsing** | Library `Category` class | Works correctly. Phase 2 discovery. |

---

## Watchlist Reality Check

### Active publications (confirmed producing content)

| Publication | URL | Author(s) | Notes |
|---|---|---|---|
| Media War & Peace | `eshap.substack.com` | Evan Shapiro | Weekly+. 11 recommendations. Media industry. |
| The Looking Glass | `lg.substack.com` | Julie Zhuo + guests | Active. Has guest posts (use raw API). Product/AI. |
| Opinionated Intelligence | `opinionatedintelligence.substack.com` | Julie Zhuo | Active. AI + data. |
| People Stuff | `miketrap.substack.com` | Mike Troiano | Weekly. Leadership, AI + writing. |
| Creatorama | `creatorama.substack.com` | Tim Shey | Active. Creator economy, media. |
| Brian Balfour | `brianbalfour.substack.com` | Brian Balfour | Active. Growth, AI. |
| Aakash's Newsletter | `www.news.aakashg.com` | Aakash Gupta | Active. PM frameworks. Custom domain. |
| Brad Stulberg | `bradstulberg.substack.com` | Brad Stulberg | Active. Resilience, performance. |
| Felix Simon | `felixsimon.substack.com` | Felix Simon | Active. Journalism + AI research. Needs slug-based fetch. |
| Fort Human | `descriptapp.substack.com` | Descript / Laura Burkhauser | Weekly. AI + creativity. |
| The Beautiful Mess | `cutlefish.substack.com` | John Cutler | Active. Product leadership. |
| Lenny's Newsletter | `www.lennysnewsletter.com` | Lenny Rachitsky + guests | Active. Hosts Claire Vo and other guest contributors. |
| Everybody At Once | `everybodyatonce.substack.com` | Kenyatta Cheese + team | Infrequent (last post Mar 2026, before that Oct 2025). Community/audience. |

### Inactive, dormant, or not on Substack

| Author | What we found |
|---|---|
| Claire Vo | Guest contributor on Lenny's. Own publications (SaaS PM, Milk Money) last posted 2020. |
| Kenyatta Cheese | Personal pub has 0 posts. Contributes infrequently to Everybody At Once. |
| Christina Wodtke | `cwodtke.substack.com` ("Curious Human") exists but only "Coming soon." |
| Evan Hirsch | Has Substack profile but no publication. Not publishing on Substack. |
| Scott Klein | `scottklein.substack.com` has only a "Coming soon" from 2021. |
| Laura Burkhauser | No personal Substack profile. Publishes through Descript's Fort Human. |

**The active watchlist today is ~13 publications.** The pipeline needs to grow this to 40-60 through Phase 2 discovery (recommendations, categories, manual curation). The sparsity of the current landscape makes that discovery engine essential.

---

## Two-Pass Scoring Approach

- **Pass 1 (all posts from all publications):** Score using title + subtitle + description + truncated_body_text from the archive endpoint. One API call per publication. Fast.
- **Pass 2 (high-scoring posts only):** Fetch full `body_html` via slug-based URL for posts scoring ≥ 6. Extract quotable moments and generate reshare angles. Limits extra API calls to the ~5-7 posts that make the digest.

---

## Unresolved Questions

### Must resolve before building

1. **Paywalled content behavior.** The `audience` field flags paid posts, but we haven't tested what `body_html` returns for a paywalled post fetched without auth. Need to know whether to filter these out in pass 1 or attempt scoring from whatever partial content is available. **→ Test with a known paywalled pub (e.g., Platformer) during Day 1.**

2. **Gemini Flash API access and cost.** Not tested in Day 0. Need to confirm: API key works, scoring prompt produces useful output, cost estimate for ~50 posts/day. **→ Test during Day 1.**

### Can resolve during build

3. **HTML-to-text stripping.** `body_html` needs conversion for LLM input. Standard library (`beautifulsoup4` or `html2text`).

4. **Deduplication across digest runs.** Track post IDs from previous digests. Simple JSON log.

5. **Optimal batch delay between publications.** 0.5s worked at 9 pubs. May need tuning at 40-60.

### Deferred to Phase 2

6. **Recommendation graph depth and density.** Only tested one level. Need to determine if the graph is rich enough for meaningful discovery at depth 2.

7. **Category browsing at scale.** 525 Technology newsletters need batch scoring and filtering.

8. **Growing the watchlist from ~13 to 40-60.** The current landscape is sparse. Phase 2 discovery (recommendations, categories, Substack web search, manual curation) is essential.

---

## Verdict

**The build is viable. Proceed to Phase 1.**

The API gives us everything we need for the daily pipeline — metadata for scoring, full content for quote extraction, engagement metrics, author identification. The library has some bugs but the raw API is reliable.

The bigger finding is about the landscape: the Substack ecosystem in this niche is sparse and fragmented. Most authors from the LinkedIn/Substack reaction corpus are either not on Substack, dormant, or publishing infrequently. This validates the project's core premise — **programmatic discovery and monitoring is the only way to find and track the publications that are actively producing reshare-worthy content in this space.**
