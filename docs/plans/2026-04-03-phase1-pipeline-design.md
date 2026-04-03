# Design: Phase 1 Pipeline + Watchlist Discovery

**Date:** April 3, 2026  
**Updated:** April 3, 2026 (post design review — iteration 2)  
**Status:** Approved  
**Scope:** Phase 1 daily pipeline architecture, initial watchlist expansion via recommendation graph, and passive feedback monitoring

---

## Design Decisions

1. **Two-pass scoring for quality + efficiency.** Stage 1 scores from archive metadata only (title, subtitle, description, truncated_body_text, engagement metrics) — fast, one API call per publication. Full content fetched only for posts scoring ≥ 7 (HIGH SIGNAL threshold), which then get Stage 2 enrichment (quote extraction, angle suggestions). This minimizes API calls while concentrating quality scoring where it matters. Risk: some good content may score below threshold on metadata alone. Mitigate by monitoring skip patterns and adjusting threshold if needed.
2. **Two-stage model split** — Gemini Flash for Stage 1 classification (cheap, fast, sufficient for theme matching). Claude Sonnet or Gemini Pro for Stage 2 creative work (quote extraction, angle suggestions) on HIGH SIGNAL posts only (~5-7 per run).
3. **Delivery: markdown file only for Phase 1.** Markdown is the canonical output, always written. Zapier webhook integration is a distinct future feature — adds delivery flexibility (email, spreadsheet, Slack) but is not needed to validate the pipeline itself.
4. **Recommendation graph discovery in Phase 1** — crawl recommendations from active watchlist publications before first digest to grow from ~13 to 40-60 publications. More targeted than category browsing for the media/journalism/product/AI niche.
5. **Passive feedback loop** — system monitors Josh's Substack activity (Notes, restacks) and matches against digest suggestions. No manual logging required. Captures what was reshared, what was skipped, and the commentary added. Note: Substack Notes/restack API endpoint not yet validated — must test on Day 1. If unavailable, defer feedback.py to Week 2 with a manual fallback.
6. **Typed data models** — Pydantic models for all data flowing between pipeline stages. Prevents dict-key bugs and validates LLM output structure.
7. **Intermediate state persistence** — each run writes stage outputs to `data/runs/YYYY-MM-DD/` so partial failures don't require full re-runs.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          DAILY RUN                                │
│                    (cron, early morning ET)                        │
│                                                                   │
│  ┌───────────┐    ┌───────────┐    ┌────────────┐    ┌────────┐  │
│  │ 1. FETCH  │───▶│ 2. SCORE  │───▶│ 3. ENRICH  │───▶│4. EMIT │  │
│  │ Content   │    │ Stage 1   │    │ Stage 2    │    │ Digest │  │
│  │ Monitor   │    │ Gemini    │    │ Sonnet /   │    │        │  │
│  │           │    │ Flash     │    │ Gemini Pro │    │        │  │
│  └───────────┘    └───────────┘    └────────────┘    └────┬───┘  │
│                                                           │      │
│                                          ┌────────────────┼───┐  │
│                                          ▼                ▼   │  │
│                                     Markdown         Zapier   │  │
│                                     file             webhook  │  │
│                                                               │  │
│  ┌────────────────────────────────────────────────────────┐   │  │
│  │ 5. FEEDBACK MONITOR                                    │   │  │
│  │ Pull Josh's recent Substack Notes/restacks             │   │  │
│  │ Match against previous digest suggestions              │   │  │
│  │ Record: reshared (with commentary) / skipped           │   │  │
│  └────────────────────────────────────────────────────────┘   │  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                 DISCOVERY (one-time + periodic)                    │
│                                                                   │
│  Crawl recommendation     Score discovered      Human reviews     │
│  graphs from watchlist ──▶ pubs against      ──▶ and approves  ──▶│
│  publications (depth 2)    Signal Profile        additions        │
│                                                                   │
│  Expands watchlist from ~13 to 40-60 publications                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Content Monitor (`src/fetch.py`)

Pulls recent post metadata from all watchlist publications via raw Substack archive API. Does NOT fetch full content — that happens in Stage 2 for high-scoring posts only.

**Per publication:**
```
GET /api/v1/archive?sort=new&offset=0&limit={max_posts_per_pub}
    → Filter: post_date within lookback window
    → Filter: audience != "only_paid"
    → Deduplicate against digest_history.json
```

**Collects per post (from archive endpoint — no per-post fetch needed):**
- title, subtitle, description, truncated_body_text (~150 chars)
- post_date, wordcount
- reactions, restacks, comment_count
- author_name, author_handle, author_bio (from publishedBylines)
- canonical_url, slug, post_id
- publication_name, publication_url

**Writes intermediate state:** `data/runs/YYYY-MM-DD/fetched.json` — so scoring can resume from here if it fails.

**Error handling:**
- Per-publication try/except — one failure doesn't block the run
- Retry once on timeout, skip on persistent failure
- Log failures, report in digest footer
- Polite delay between requests (0.75s default)

### 2. Stage 1 Scorer (`src/score.py`)

Scores every fetched post against the Signal Profile using metadata only. Classification task.

**Model:** Gemini Flash (temperature: 0 for scoring consistency)

**Prompt receives:** Signal Profile (5 theme clusters with weights, noise filters) + post metadata (title, subtitle, description, truncated_body_text, author name/bio, engagement metrics). Does NOT receive full post text — metadata is sufficient for classification.

**Output per post (validated via Pydantic model):**
```json
{
  "theme_fit": 4,
  "theme_clusters": ["AI + Product Craft", "Media Industry Dynamics"],
  "reshare_potential": 3,
  "creator_value": 1,
  "total_score": 8,
  "noise_flag": null,
  "one_line_reason": "Argues AI editing tools are changing content velocity for media companies"
}
```

**Scoring rubric (from project brief):**
- Theme fit (0-5): How strongly does this match one or more of the five clusters?
- Reshare potential (0-3): Does this contain a specific insight that invites commentary?
- Creator relationship value (0-2): Is the author in the target neighborhood (1K-50K subs, media/product/AI)?

**Posts sent individually, not batched.** Scoring quality matters more than minimizing API calls. ~50 calls at Gemini Flash pricing is negligible cost.

**LLM output validation:** Parse responses through Pydantic model. On invalid JSON or out-of-range scores: retry once, then log and skip the post. Clamp scores to valid ranges (0-5, 0-3, 0-2).

**Writes intermediate state:** `data/runs/YYYY-MM-DD/scored.json`

**Degraded mode:** If Gemini Flash is completely unavailable, emit a "fetch-only" digest listing new posts without scores rather than failing silently.

### 3. Stage 2 Enrichment (`src/enrich.py`)

For posts scoring ≥ 7 (HIGH SIGNAL threshold) only — typically ~5-7 per run. This is the only stage that fetches full post content.

**Process per post:**
1. Fetch full content: `GET /api/v1/posts/{slug}` → extract `body_html`
2. Strip HTML → plain text
3. Send to Stage 2 model for quote extraction + angle generation

**Model:** Claude Sonnet (primary), Gemini Pro (fallback/alternative — test both)

**Prompt receives:** Full post text (freshly fetched), Stage 1 score and matched themes, author info, and Josh's editorial context (positioning at media/product/AI intersection, NBC News Group background, editorial voice notes).

**Error handling:** If full content fetch or LLM call fails for a post, degrade gracefully to Stage 1 data only (score + one_line_reason, no quote or angles). The post still appears in the digest with its score.

**Output per post:**
```json
{
  "best_quote": "The actual quotable passage — 1-3 sentences",
  "quote_context": "Why this quote works for a reshare",
  "angles": [
    {
      "angle": "Connect to your NBC experience with editorial AI tools",
      "type": "personal experience"
    },
    {
      "angle": "Contrast with the 'AI replaces editors' narrative",
      "type": "contrarian take"
    },
    {
      "angle": "Ask your audience: how is your newsroom handling this?",
      "type": "community question"
    }
  ]
}
```

### 4. Digest Generator (`src/digest.py`)

Assembles scored and enriched posts into a markdown digest.

**Output: Markdown file** → `output/digests/YYYY-MM-DD.md`

```markdown
# Signal Pipeline — 2026-04-08 — 6 posts worth your attention

## HIGH SIGNAL (score ≥ 7, with quotes and angles)

### 1. [Post Title]
**by Author Name · Publication · April 7, 2026**
Score: 8/10 | Themes: AI + Product, Media Industry

> "Best quote extracted here — 1-3 sentences"

**Reshare angles:**
- Connect to your NBC experience with editorial AI tools
- Contrast with the 'AI replaces editors' narrative
- Ask your audience: how is your newsroom handling this?

[Read post →](https://...)

---

## WORTH A LOOK (score 6, metadata-only — title, score, one-line reason)

### 4. [Post Title]
**by Author Name · Publication · April 6, 2026**
Score: 6/10 | AI + Product Craft
> Explores how product teams are restructuring around AI capabilities

[Read post →](https://...)

---

## PIPELINE STATS
- Publications monitored: 47
- New posts scanned: 31
- Posts scoring ≥ 7 (HIGH SIGNAL): 5
- Posts scoring 6 (WORTH A LOOK): 3
- Fetch errors: 1 (felixsimon.substack.com — timeout)
```

Note: the digest review takes ~5 minutes. The actual resharing (composing commentary, posting to Notes) is separate human work, ~10-15 minutes per reshare.

**Zapier webhook integration** is a future feature — not in Phase 1 scope. When added, the webhook will send both rendered markdown and structured JSON so downstream automations can use either format.

**After emitting:** Update `data/digest_history.json` with all scored post IDs (both HIGH SIGNAL and WORTH A LOOK).

**Digest history format:**
```json
{
  "digests": [
    {
      "date": "2026-04-08",
      "post_ids": [192883042, 192244974],
      "posts_scanned": 31,
      "posts_in_digest": 8
    }
  ]
}
```

### 5. Feedback Monitor (`src/feedback.py`)

Passively monitors Josh's Substack activity and matches against previous digest suggestions.

**How it works:**
```
1. Pull Josh's recent Substack activity:
   - Notes and restacks from his profile (via archive API or user activity endpoint)
   - Look for URLs or content matching posts from recent digests

2. For each digest item from the last N days:
   - Was it reshared? (URL appears in a Note or restack)
   - If reshared: capture the commentary text Josh wrote
   - If not reshared: mark as skipped

3. Write results to data/reshare_log.json:
   {
     "date": "2026-04-09",
     "digest_date": "2026-04-08",
     "reshared": [
       {
         "post_id": 192883042,
         "title": "AI is My Editor Now?",
         "author": "Evan Shapiro",
         "score": 8,
         "themes": ["AI + Product Craft", "Media Industry Dynamics"],
         "commentary": "Josh's actual Note text here...",
         "reshare_type": "note_with_link",
         "reshare_date": "2026-04-08T14:32:00Z"
       }
     ],
     "skipped": [
       {
         "post_id": 188960554,
         "title": "What Excellent Growth Teams See That Others Miss",
         "score": 7,
         "themes": ["AI + Product Craft"]
       }
     ]
   }
```

**Runs:** As part of the daily pipeline run, checking activity since the last run. Looks back at the last 7 days of digests to allow for delayed resharing.

**Future use (not built in Phase 1, but the data supports it):**
- Refine Signal Profile weights based on reshare-vs-skip patterns by theme cluster
- Develop editorial voice profile from accumulated commentary for better angle suggestions
- Track which reshares generate engagement (reactions, follows, profile views)
- Feed reshared authors into discovery engine for recommendation graph expansion

---

## Discovery Engine (`src/discover.py`)

Expands the watchlist from ~13 seed publications to 40-60 by crawling recommendation graphs.

**Process:**
```
For each publication in the current watchlist:
    Newsletter.get_recommendations()  → depth 1 recommendations
    For each recommended publication:
        Newsletter.get_recommendations()  → depth 2 recommendations

Deduplicate all discovered publications
Remove any already in watchlist

For each discovered publication:
    Fetch 5 most recent posts via archive API
    Score publication against Signal Profile (Gemini Flash):
        - Average theme fit across recent posts
        - Publishing frequency (active vs. dormant)
        - Subscriber range signal (if available)
        - How many watchlist publications recommend it (cross-reference count)

Rank by score
Output: candidates.json with ranked list for human review
```

**Output for review:**
```json
{
  "discovered": "2026-04-07",
  "seed_publications": 13,
  "total_discovered": 87,
  "after_scoring": 42,
  "candidates": [
    {
      "url": "https://example.substack.com",
      "name": "Example Newsletter",
      "author": "Jane Smith",
      "score": 7.2,
      "recommended_by": ["eshap.substack.com", "creatorama.substack.com"],
      "recent_posts": ["Post Title 1", "Post Title 2", "Post Title 3"],
      "reason": "Covers AI tools for media production. Recommended by 2 watchlist pubs."
    }
  ]
}
```

Josh reviews candidates and approves/rejects. Approved publications are added to `config/watchlist.json`.

---

## Configuration Files

### `config/watchlist.json`
```json
{
  "publications": [
    {
      "url": "https://eshap.substack.com",
      "name": "Media War & Peace",
      "author": "Evan Shapiro",
      "tier": 1,
      "added": "2026-04-03",
      "source": "seed"
    }
  ]
}
```

### `config/signal_profile.json`
```json
{
  "theme_clusters": [
    {
      "name": "AI + Product Craft",
      "weight": "HIGH",
      "description": "How AI agents change building, team structure, and product development",
      "example_signals": ["AI coding workflows", "agent architecture", "human-AI collaboration"]
    },
    {
      "name": "Media Industry Dynamics",
      "weight": "HIGH",
      "description": "Business, distribution, and survival of news and media companies",
      "example_signals": ["media business models", "streaming economics", "platform shifts"]
    },
    {
      "name": "Journalism + AI Tooling",
      "weight": "HIGH",
      "description": "Intersection of newsroom workflows and AI capabilities",
      "example_signals": ["AI for fact-checking", "newsroom automation", "local news innovation"]
    },
    {
      "name": "Career Identity & Resilience",
      "weight": "MEDIUM",
      "description": "Job transitions, leadership under uncertainty, what work means",
      "example_signals": ["layoff recovery", "identity beyond title", "resilience frameworks"]
    },
    {
      "name": "Creator/Audience Building Mechanics",
      "weight": "MEDIUM",
      "description": "How individuals build audiences, platform mechanics, content strategy",
      "example_signals": ["Substack growth", "newsletter strategy", "audience engagement"]
    }
  ],
  "noise_filters": [
    {
      "name": "Personal milestone celebrations",
      "action": "reduce_score",
      "exception": "Contains substantive industry commentary beyond the announcement"
    },
    {
      "name": "Pure political commentary",
      "action": "reduce_score",
      "exception": "Connected to media/tech/product themes"
    },
    {
      "name": "Art/visual without editorial substance",
      "action": "reduce_score",
      "exception": null
    },
    {
      "name": "Generic motivational content",
      "action": "reduce_score",
      "exception": "Contains specific, earned insight"
    },
    {
      "name": "Mega-accounts (500K+ followers)",
      "action": "reduce_score",
      "exception": "Genuinely contrarian or additive take"
    }
  ],
  "scoring": {
    "theme_fit_max": 5,
    "reshare_potential_max": 3,
    "creator_value_max": 2,
    "digest_threshold": 6,
    "high_signal_threshold": 7
  }
}
```

### `config/pipeline.json`
```json
{
  "user": {
    "substack_handle": "joshkinberg",
    "substack_url": "https://joshkinberg.substack.com"
  },
  "fetch": {
    "lookback_days": 1,
    "first_run_lookback_days": 3,
    "delay_between_pubs_seconds": 0.75,
    "max_posts_per_pub": 10,
    "timeout_seconds": 15
  },
  "scoring": {
    "stage1_model": "gemini-3.1-flash",
    "stage1_temperature": 0,
    "stage2_model": "claude-sonnet-4-6",
    "stage2_fallback_model": "gemini-3.1-pro"
  },
  "output": {
    "digest_dir": "output/digests"
  },
  "feedback": {
    "lookback_days": 7,
    "enabled": true
  },
  "discovery": {
    "recommendation_depth": 2,
    "min_recent_posts": 3,
    "min_publication_score": 5.0
  }
}
```

---

## File Structure

```
audience-development/
├── src/
│   ├── __init__.py
│   ├── models.py           # Pydantic models: Post, ScoredPost, EnrichedPost, DigestEntry
│   ├── fetch.py            # Content monitor — archive metadata pull
│   ├── score.py            # Stage 1 — Gemini Flash scoring (metadata only)
│   ├── enrich.py           # Stage 2 — Sonnet/Pro full content + quotes + angles
│   ├── digest.py           # Output — markdown digest generation
│   ├── feedback.py         # Feedback monitor — match reshares to digests
│   ├── discover.py         # Discovery — recommendation graph crawl
│   └── utils.py            # HTML stripping, API helpers, logging
├── config/
│   ├── watchlist.json      # Publication watchlist
│   ├── signal_profile.json # Theme clusters, noise filters, scoring
│   └── pipeline.json       # Runtime config (models, delays, thresholds)
├── data/
│   ├── runs/               # Intermediate state per run (YYYY-MM-DD/)
│   ├── digest_history.json # Post IDs from previous digests
│   └── reshare_log.json    # Feedback: what was reshared, skipped, commentary
├── output/
│   └── digests/            # Generated markdown digests (YYYY-MM-DD.md)
├── scripts/
│   ├── run_pipeline.py     # Main entry point — daily run
│   ├── run_discovery.py    # Discovery crawl entry point
│   └── day0_validation.py  # API validation (exists)
├── tests/
│   └── golden_set/         # 5 "definitely reshare" + 5 "definitely skip" posts for scoring validation
├── corpus/                 # Reaction data (exists)
├── planning/               # Strategy docs (exists)
├── docs/plans/             # Design docs
├── .env                    # API keys (gitignored)
├── pyproject.toml          # Package config + entry points
└── requirements.txt
```

---

## Build Sequence

### Day 1: Foundation + Fetch + Discovery
- Project setup: `pyproject.toml`, `requirements.txt`, `.env` template, config files
- `src/models.py` — Pydantic models for Post, ScoredPost, EnrichedPost, DigestEntry
- `src/utils.py` — HTML stripping, raw API helpers, retry logic, logging
- `src/fetch.py` — archive API metadata pull, dedup against history
- `src/discover.py` — recommendation graph crawl, publication scoring
- Run discovery to expand watchlist from ~13 to 40-60
- Validate Substack Notes/restack API endpoint for feedback.py feasibility

### Day 2: Scoring + Enrichment
- `src/score.py` — Gemini Flash scoring prompt, Pydantic output validation
- `src/enrich.py` — full content fetch + Sonnet/Pro quote extraction + angle generation
- Create golden set: 5 "definitely reshare" + 5 "definitely skip" posts from watchlist
- Test scoring on real posts, tune Signal Profile prompt
- Note: prompt tuning may extend into Day 3 if Flash output quality needs iteration

### Day 3: Digest + Pipeline Integration
- `src/digest.py` — markdown digest generation
- `scripts/run_pipeline.py` — orchestrate full daily run (fetch → score → enrich → digest)
- Intermediate state persistence (`data/runs/YYYY-MM-DD/`)
- First full pipeline run → first real digest
- `src/feedback.py` — if Notes API validated on Day 1; otherwise defer to Week 2

### Days 4-5: Polish + Deploy
- Error handling: degraded modes, LLM output validation, retry logic
- Dedup working across multiple runs
- Deploy to cloud for daily cron (GitHub Actions or Railway)
- First automated morning digest
- Document required env vars: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`

---

## Future Enhancements (Not in Phase 1 Scope)

- **Zapier webhook delivery** — POST structured JSON to Zapier for routing to email, spreadsheet, Slack, etc. Distinct feature scope that enhances utility once pipeline is working.
- **Signal Profile refinement** from reshare_log.json — adjust theme weights based on actual reshare patterns
- **Editorial voice profile** from accumulated commentary — improve angle suggestions to match Josh's voice
- **Engagement tracking** — did the reshare generate reactions, follows, profile views on Substack?
- **LinkedIn expansion** (Phase 3) — extend feedback monitor to LinkedIn via periodic Apify exports
- **Agentic wrapper** (Phase 4) — modular architecture supports wrapping in a persistent agent framework

---

## Design Review Log

### Review Iteration 1 (April 3, 2026)
**Reviewers:** Product Manager, Architect, CTO  
**Verdict:** All three APPROVED with non-blocking suggestions.

**Key revisions applied:**
1. Resolved two-pass vs. two-stage contradiction: Stage 1 scores from metadata only, full content fetched only for posts scoring ≥ 7 before Stage 2 enrichment.
2. Fixed enrichment threshold inconsistency: score ≥ 7 = HIGH SIGNAL (gets enrichment), score 6 = WORTH A LOOK (metadata only, no enrichment).
3. Added Pydantic models for typed data flow between stages.
4. Added intermediate state persistence (`data/runs/YYYY-MM-DD/`).
5. Added LLM output validation and degraded mode definitions.
6. Deferred Zapier webhook to future feature scope.
7. Added golden set for scoring validation.
8. Added `pyproject.toml` for clean import paths.
9. Specified `digest_history.json` format.
10. Added model temperature and env var documentation.

**Open items carried forward:**
- Validate Substack Notes/restack API on Day 1 (feedback.py feasibility)
- If Notes API unavailable, defer feedback.py to Week 2 with manual fallback
- Monitor whether metadata-only Stage 1 scoring misses quality content; adjust threshold if needed

**Success metrics (from project brief — Keep/Pivot/Kill at 30 days):**
- Digest produces 3+ actionable items per week
- 2-3 creators engage back within 30 days
- Profile views increasing week-over-week
- Workflow feels sustainable at ~15-20 min total (5 min review + 10-15 min per reshare)
