# Knowledge Base — Audience Development Pipeline

## Day 0 Findings (2026-04-03)
- `substack_api` 1.2.0 works for post retrieval, recommendations, category browsing
- Global cross-Substack search is broken (404) — use recommendations + categories for discovery
- Library has bugs with cross-posted content and Notes-style URLs — use raw API for daily pipeline
- Raw archive API (`/api/v1/archive`) returns all metadata needed for scoring in one call per publication
- Full content available via slug-based fetch (`/api/v1/posts/{slug}`) without auth for free posts
- Rate limiting not an issue at 40-60 publications with 0.5s delays
- **Notes API FOUND (2026-04-14):** `GET {publication_url}/api/v1/notes` returns user's Notes feed — 13 items with body text, timestamps, context. No auth required. This replaces the earlier finding that Notes were inaccessible.
- Notes are typed as `comment` with `context.type = "note"`, body text is truncated (~150 chars), timestamps in ISO format
- Endpoint: `https://joshkinberg.substack.com/api/v1/notes` → returns `{items: [...], nextCursor: ...}`
- This makes the passive feedback monitor buildable: pull Notes, match URLs/titles against digest items, capture commentary
- Open RSS (openrss.org) is unreliable — timed out during testing. Not needed now that the API works.
- Substack's built-in RSS (`/feed`) only returns newsletter posts, not Notes

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
- Run command: `./run.sh` (shell script handles venv activation and PYTHONPATH)
- Pipeline runtime ~3.5 min for 44 pubs, 18 posts scored, 7 enriched

## Email Delivery (2026-04-15)
- Gmail SMTP via app password works. Email delivers to inbox (not spam).
- Markdown → HTML conversion via `markdown2` with inline CSS for email compatibility
- Substack app deep links: custom domain URLs rewritten to `*.substack.com` by extracting subdomain from `publishedBylines[0].publicationUsers[0].publication.subdomain` in the archive response
- Deep links confirmed working on iPhone — opens directly in Substack app
- One edge case: Ben's Bites (`www.bensbites.com`) didn't get rewritten — byline data may not include subdomain for all publications
- Email subject: "Substack Signal Pipeline — {date} — N high signal"
- Delivery is non-blocking — if email fails, digest file is still written
- Config: `delivery.enabled`, `delivery.to_email`, `delivery.skip_empty` in pipeline.json
- Env vars: `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` in .env
- Claude Cowork sandbox couldn't run the pipeline (404 errors with Substack API) — local or cloud deployment required

## Feedback Monitor (2026-04-15)
- feedback.py built and tested. Matches Notes reshares against digest post IDs.
- Notes API: `GET {publication_url}/api/v1/notes` → returns `{items: [...]}` with comment body + attachments
- Reshares appear as Notes with `attachments[].type == "post"` containing full post metadata including `id`
- Post ID from attachment matches directly against `digest_history.json` post IDs — clean 1:1 matching
- Also captures: commentary text (comment.body), timestamp, note_id, author/publication of reshared post
- Notes without post attachments (original Notes, image posts) are skipped
- Notes resharing content NOT from the digest are logged with `matched: false` — still useful signal
- Dedup via `seen_note_ids` list in reshare_log.json — won't re-process on subsequent runs
- First run found 2 digest matches + 10 historical Notes (own article promos + pre-pipeline reshare)
- Runs automatically as last step of pipeline after digest delivery

## Cloud Deployment (2026-04-15)
- **GitHub Actions: BLOCKED.** All `*.substack.com` API calls return 403 from GitHub Actions runners. User-Agent and delay changes didn't help — it's an IP-level block. Custom domain publications (e.g., `newsletter.eng-leadership.com`, `refactoring.fm`) worked fine from GH Actions.
- **Google Cloud Run: WORKS.** Tested with a Cloud Run Job in us-east1 — `eshap.substack.com` returned 200 successfully. Substack does not block Google Cloud IPs.
- Deployment target: Google Cloud Run Jobs with Cloud Scheduler for daily cron
- Need a new GCP project (not reusing nyc-school-explorer)
- State persistence: Cloud Storage bucket for digest_history.json and reshare_log.json
- Secrets: GCP Secret Manager for API keys and Gmail credentials
- GitHub Actions workflow removed from repo
- **Deployed to Cloud Run:** Project `audience-development-agents`, region us-east1
- Container: `gcr.io/audience-development-agents/signal-pipeline`
- State bucket: `gs://audience-development-agents-state` (digest_history.json, reshare_log.json)
- Scheduler: `signal-pipeline-daily` — cron `0 13 * * *` (9 AM ET)
- First cloud run: 22 posts scanned, 8 HIGH SIGNAL, 0 fetch errors, email delivered
- To redeploy after code changes: `gcloud config set project audience-development-agents && gcloud builds submit --tag gcr.io/audience-development-agents/signal-pipeline && gcloud run jobs update signal-pipeline --image gcr.io/audience-development-agents/signal-pipeline --region us-east1`
- To manually trigger: `gcloud run jobs execute signal-pipeline --region us-east1`

## Public Release + Subscription Sync (2026-04-29)
- Repo flipped from private to public on GitHub (`jkinberg/audience-development`)
- Personal corpus, analytics, runtime data, and digest history moved out to sibling dir `~/Projects/audience-development-private/`
- History rewritten with `git-filter-repo` to scrub `corpus/`, `data/*.json`, and `output/digests/*.md` from all commits — repo `.git` shrank ~80M → ~270K
- Personal config (substack handle/url, delivery email) parameterized to env vars in `.env`; `pipeline.json` uses `null` and the consumers fall back to `os.getenv(...)`
- `src/subscriptions.py` added: `User.get_subscriptions()` → diff against watchlist → append new pubs with `source: "subscription"`. Resolves custom-domain pubs (e.g. `blog.brianbalfour.com` → `brianbalfour.substack.com`) via archive lookup so duplicates are caught. First run: 35 subs → 18 new pubs added (44 → 62 watchlist entries)
- `src/feedback.py` extended with `flag_publications_from_unmatched()`: writes off-digest reshare publications to `data/reshare_candidates.json`. Dedupes by URL host, publication name, and author. Skips self-reshares and bare-substack.com URLs that can't identify a publication
- `scripts/review_candidates.py` + Monday gate in `cloud_run.py`: weekly review opens a GitHub issue listing pubs with ≥2 reshares (promote) and 1-reshare pubs older than 4 weeks (prune candidates). Uses `GITHUB_TOKEN` env var on Cloud Run; falls back to logging the would-be issue if the token is unset
- `STATE_FILES` in `cloud_run.py` now includes `config/watchlist.json` and `data/reshare_candidates.json` so subscription-sync mutations and reshare candidates persist across image deploys
- Backup of pre-rewrite repo at `~/Projects/audience-development-backup-pre-public/` (preserved original 80M history before force-push)

## LinkedIn Pipeline Planning (2026-05-13)
- Project brief reached v7 at `audience-development-private/docs/linkedin-network-intelligence-brief-v7.md`. Day 0 validation plan v2 at `audience-development-private/docs/linkedin-day0-validation-plan.md`. `scripts/build_candidate_pool.py` committed to public repo. Day 0 execution not yet started.
- Brainstorm decisions: single-stage scoring with Gemini Pro (not two-stage like Substack); v1 scope is posts-only with comments-as-signal deferred to v1.5 contingency; head-to-head Proxycurl vs. Apify on a 150-row pre-enrichment scout pass during Day 0 Gate 1a; sample selection happens from enriched data, not from stale-CSV scoring.
- Repo convention formalized: `audience-development-private/` is a local-only sibling repo (not a `private/` subdirectory in the public repo). Source CSVs at `audience-development-private/corpus/linkedin/`. Source code in the public repo references private paths via config files like `config/linkedin_pipeline.json`. Builds on the April 2026 public-release split but treats the private side as a separate repo rather than a gitignored subdirectory.
- Day 0 budget revised: ~5 hours, ~$25-35 API cost (was 2-3h, no head-to-head). The increase buys (a) grounded sample selection from current-state enriched data, (b) provider comparison on 150 profiles rather than 25.

## LinkedIn Pipeline Day 0 Execution (2026-05-21)
- **Proxycurl shut down before Day 0 ran.** Brief bumped to v8, plan to v3: Apify-only, no head-to-head. Backup actor candidates noted (`curious_coder/linkedin-profile-scraper`, `bebity/linkedin-profile-scraper`) but not tested. The platform-risk concern flagged in the original brainstorm landed in real life within ~2 weeks.
- **Gate 1a passed.** 150 profiles enriched via `harvestapi/linkedin-profile-scraper`, 100% pass rate, $0.60. Spot-check accuracy confirmed qualitatively (heavy NBC/Versant alumni overlap matched expectations).
- **Supplemental enrichment confirmed pool-may-be-larger hypothesis.** 15 non-pool profiles enriched ($0.06) across 3 stale-CSV score buckets (0, 2, 3). Found 4-of-5 clear fails in score-0 bucket AND 3 hidden ideals in score-2 bucket (PJ C. Senior Mgr Product Data Sci @ PlayStation; Prit Roy Sr. Product Manager @ Versant Media; Greg Rosenstein Sports Editor @ NBC News). The `build_candidate_pool.py` scoring missed these because the keyword list lacked "Sr.", "Senior", and "Editor" as seniority signals.
- **Gate 1b: 27% post in 30 days, 73% lurkers.** All 150 enriched profiles fetched for posts (30-day lookback, $0.33). 41 profiles posted ≥1 time; 109 returned empty. 187 posts total, average 4.6 per active poster. Four super-posters (Carlos Villaumbrosia, Erich Buerger, Chris Hoskins, Polly Allen) drove ~50% of volume. Most posts are thought-leadership/marketing; signal mix skews toward `industry_critique`/`strategic_uncertainty` (content-idea side) rather than `problem_narration` (job-search side).
- **Gate 2 in progress** — LLM-assisted classification approach chosen (Gemini Pro on all 187 posts via the brief's signal_profile prompt). Script not yet written. Total Day 0 spend so far: $1.03 of $5 Apify free credit; Gemini classification est. $0.10-0.20 additional.
- **Day 0 sample-selection framework simplified mid-execution.** Original v3 plan: 10 ideal + 10 fail + 5 edge cases. Mid-Gate-1b realized the fail/edge categories were inherited from the head-to-head era and serve Phase 1 filter validation that doesn't exist yet. Simpler path: run posts on the full 150 (cheap), score everything, decide volume from the actual data. Pattern captured below.
- **New scripts in public repo, uncommitted as of pause:** `enrich_profiles_apify.py`, `review_enriched_profiles.py`, `rank_enriched_profiles.py`, `select_supplemental_profiles.py`, `fetch_posts_apify.py`, `summarize_posts.py`.

## Nov 2026 Outage + Operational Fixes (2026-11-16)
- **Daily emails stopped Nov 5–16.** A chain of three independent failures: (1) Substack changed `/api/v1/archive` — dropped the `offset` param (now 400) and reshaped the response to `{posts, nextCursor}` (was a bare array); (2) Gemini prepaid credits depleted (`402 RESOURCE_EXHAUSTED`); (3) a rebuild pulled a newer `google-genai` SDK whose default endpoint flipped to `v1`, which 404s `-preview` model IDs. The job exits 0 on fetch/score failures, so it went unnoticed for 10 days.
- **Fixes:** `fetch_archive()` drops `offset` and unwraps `posts`; a guard in `run_pipeline.py` now exits non-zero when ALL pubs fail to fetch (surfaces a total outage as a FAILED execution). Models moved to GA — `gemini-3.5-flash-lite` (Stage 1), `gemini-3.8-flash` (Stage 2), `claude-sonnet-4-6` (fallback, still dormant/not wired into `enrich.py`). `google-genai` pinned `>=1.70,<2.0`.
- **Model IDs live in BOTH `config/pipeline.json` and hardcoded defaults in `score.py`/`enrich.py`** — update both or a missing config key falls back to a dead model. There is **no GA `gemini-3.x-pro`**, so Stage 2 uses the newest GA flash, not a pro tier.
- **429 coverage fix:** the first clean scheduled run still dropped ~14/69 pubs to HTTP 429. Substack rate-limits the full-watchlist loop even on a single daily run (NOT just repeated manual test runs). Added `Retry-After`-aware backoff/retry to `fetch_archive`/`fetch_post_content` (exp. fallback, cap 30s, 4 attempts) + widened `delay_between_pubs_seconds` 0.75→1.25.
- **`Tech in LA` dead custom domain** (`www.techinla.io` → NXDOMAIN) repointed to `techinla.substack.com`. The cloud watchlist is authoritative in **GCS** (`gs://<project>-state/config/watchlist.json`, now 69 pubs via subscription-sync), NOT git — the committed watchlist lags production.
- **"No email" is often normal:** `delivery.skip_empty=true` suppresses the digest when 0 posts clear HIGH SIGNAL (≥7). A clean run showing `Scoring complete: N scored, 0 failed` and `HIGH SIGNAL: 0` is a quiet day, not a failure.

## Gotchas & Patterns (consolidated from build sessions)

### Gotchas — will bite you if you forget
- **Substack blocks GitHub Actions IPs.** All `*.substack.com` 403. Custom domains work. Google Cloud Run works. It's IP-level, not User-Agent.
- **`substack_api` library redirect bugs.** Cross-posted content and `p-{id}` canonical URLs cause 404 in `Post.get_metadata()`. Always use raw archive API + slug-based fetch.
- **`get_recommendations()` returns URLs without `https://`.** Must normalize before API calls.
- **Gemini model IDs change frequently.** `gemini-2.0-flash` deprecated (404). Always list available models before assuming an ID works: `client.models.list()`.
- **Custom domain Substack URLs don't open in the app.** Rewrite to `*.substack.com` using subdomain from `publishedBylines` data in archive response.
- **Ben's Bites (`www.bensbites.com`) byline data lacks subdomain** — URL rewriting doesn't work for all custom domains.
- **`resolve_handle_redirect()` only handles handle renames, NOT custom-domain → subdomain.** Returns `None` for both `blog.brianbalfour.com` and `brianbalfour.substack.com`. To canonicalize a custom-domain pub to `*.substack.com`, fetch one archive post via `Newsletter(url).get_posts(limit=1)` and read `publishedBylines[0].publicationUsers[0].publication.subdomain`.
- **Notes reshares can have bare-substack.com `canonical_url`.** Some reshares use `https://substack.com/home/post/p-XXX` with no publication subdomain — the URL alone can't identify the publication. When deduping reshares against a watchlist, also match by publication name and author, not just URL host.
- **`/schedule` (RemoteTrigger) sandbox has no gcloud or gh CLI auth.** Only auth available is via MCP connectors (currently Drive/Gmail/Calendar). Tasks needing GCP or GitHub access must either use a connector path or run inside an already-authenticated environment (e.g., Cloud Run itself). Don't propose remote scheduled agents for GCS+gh tasks without restructuring auth.
- **LinkedIn `Connections.csv` Position field is frozen at connection time.** LinkedIn data exports snapshot `Position`/`Company` at the moment you connected and never refresh them. Connection date doesn't correlate with current-data accuracy — only with how recently the snapshot was taken. A "recent" connection just means LinkedIn captured their role closer to now; six months later they may have changed jobs. Don't use connection recency as a proxy for data freshness when picking sample profiles or filtering candidates. Ground-truth current state via profile enrichment instead — algorithmic filtering on stale CSV produces misleading results.
- **`json.dumps(ensure_ascii=False)` silently breaks NDJSON via U+2028.** Python's `json` module with `ensure_ascii=False` lets U+2028 (LINE SEPARATOR) and U+2029 (PARAGRAPH SEPARATOR) chars from text fields pass through unescaped. Some readers — notably `str.splitlines()` and `Path.read_text().splitlines()` — treat these as line terminators, silently splitting one JSON object across multiple "lines" and breaking the one-object-per-line NDJSON invariant. For NDJSON writers use default `ensure_ascii=True`. For readers iterate with `for line in f:` (only splits on `\n`) rather than `.splitlines()`.
- **Apify input field names vary across actors from the same vendor.** Within `harvestapi`: `linkedin-profile-scraper` takes `{"urls": [...]}` while `linkedin-profile-posts` takes `{"targetUrls": [...]}`. Never assume the field name from another actor — always check the actor's input schema at `https://apify.com/<vendor>/<actor>/input-schema` (or the Apify Console UI) before writing the input payload. Apify API rejects with `"The input JSON must be object, got 'array' instead"` or similar if the top-level shape is wrong.
- **Apify harvestapi posts return `author.linkedinUrl` with query-string crud.** Post items returned by `harvestapi/linkedin-profile-posts` have an `author.linkedinUrl` shaped like `https://www.linkedin.com/in/<slug>?miniProfileUrn=urn%3Ali%3Afsd_profile%3AACoAAB...`. Exact-string matching against clean input URLs silently fails (zero matches). Match on `author.publicIdentifier` against the URL slug instead — it's a stable identifier without query-string params.
- **`scripts/build_candidate_pool.py` SENIORITY_KEYWORDS list misses `editor`, `sr.`, and `senior` (standalone).** Confirmed on 2026-05-21: Day 0 supplemental enrichment surfaced multiple watchlist-quality profiles (Sports Editor @ NBC News, Sr. Product Manager @ Versant Media) that the keyword filter undercounted because these seniority indicators aren't in the list. Add before running Phase 1 production enrichment on the full Connections.csv — otherwise the filter will miss legitimate watchlist candidates.
- **Gemini `-preview` model IDs 404 on google-genai's default `v1` endpoint.** Preview models are served only on `v1beta`; newer SDK versions default to `v1`. Use GA model names (no `-preview`) and pin `google-genai` (`>=1.70,<2.0`) so a rebuild can't silently flip the endpoint and orphan the model IDs. There is no GA `gemini-3.x-pro` — use a GA flash tier for Stage 2. Supersedes the older "list available models" advice for this specific failure mode.
- **`ScheduleWakeup` is a local in-session timer, not a cloud job.** It re-invokes the running Claude Code process, clamps each sleep to ≤3600s (re-arm hourly for longer waits), and CANNOT wake a sleeping Mac. For a multi-hour wait keep the machine awake with `caffeinate -i -s` (AC power + lid open only; display sleep is fine), or use a cloud routine for laptop-independence. Note: the actual GCP cron/email fires regardless of the laptop — only the local confirmation depends on this.
- **Don't add a trailing `&` inside a `run_in_background` Bash command.** It double-backgrounds: the shell returns instantly and the harness reports the task "completed" while the real process keeps running orphaned (looked like `caffeinate` had died when `pgrep` showed it alive). Pass the bare command with `run_in_background`; verify with `pgrep -lf`/`pmset -g assertions` if needed.

### Patterns — do this, it works
- **Day 0 validation before building.** Test API assumptions, rate limits, library bugs before committing to a build path.
- **Don't over-engineer delivery.** Start with simplest working option. Zapier → spam. Gmail SMTP → inbox.
- **Digest = scanning tool, not commentary tool.** Surface content with links, summaries, quotes. Don't suggest what to say.
- **Watchlist = publications, not authors.** Some authors guest-contribute elsewhere.
- **Two-pass scoring.** Metadata-only Stage 1 (cheap, all posts) → full content Stage 2 (expensive, top posts only).
- **Substack niche is sparse.** Expect ~50% of watchlist authors to be inactive. Discovery engine is essential.
- **Cloud Run state-file round-trip rule.** Any file mutated by code at runtime (e.g., `config/watchlist.json` after subscription sync, `data/reshare_candidates.json` from feedback) must be in `STATE_FILES` in `cloud_run.py` so it round-trips with GCS. Otherwise the mutation is lost on the next image deploy. Don't bake mutable state into the container image.
- **Subscription sync runs BEFORE fetch in `run_pipeline.py`.** New pubs from `User.get_subscriptions()` are picked up on the same run rather than waiting a day. Stage order in `scripts/run_pipeline.py` is intentional: subscription sync → fetch → score → enrich → digest → deliver → feedback.
- **Two-stage scoring is only worth its complexity when content is long AND Stage 2 fetches additional content.** The Substack pipeline uses two-stage because posts are 1000-5000 words and Stage 2 does a slug-based full-body fetch beyond what Stage 1 sees. When neither condition applies (e.g., LinkedIn posts at 100-500 words with text already in hand after fetch), single-stage Gemini Pro is sufficient. Two-stage adds two prompts to tune, two degraded-mode branches, intermediate state plumbing, and harder end-to-end reasoning — pay these costs only when filter savings or additional content fetches justify them.
- **Public + private sibling repos for personal-data projects.** Pattern: `audience-development/` (public, on GitHub) holds source code, configs, scripts, and READMEs. `audience-development-private/` (local-only sibling at `~/Projects/audience-development-private/`, never pushed) holds source data (LinkedIn export CSVs), planning briefs, Day 0 artifacts, golden sets, and any artifacts containing real names or post text. Code is parameterized — config files like `config/linkedin_pipeline.json` reference private-repo paths locally. Refinement of the April 2026 public-release split: treat the private side as a separate repo, not a `private/` subdirectory inside the public repo.
- **Day 0 gates should test signal volume, not just existence.** "Find 5 examples in N profiles" tests whether the signal *exists* but doesn't tell you the rate. For an actionable go/no-go decision: extrapolate observed (high-signal posts / profile-days) × target_watchlist × 7 × discount_factor → expected weekly volume → map to GO / GO-with-contingency / STOP thresholds. The volume formulation produces decisions that map directly to Keep/Pivot/Kill criteria. Existence-only tests can pass even when the hypothesis fails at scale.
- **Head-to-head provider testing for third-party API dependencies.** When provider quality is hard to assess from docs and switching cost after build starts is high (LinkedIn scraping providers like Proxycurl vs. Apify are the clear example), test 2+ providers on the same sample set before committing. Cost is ~$10-30 total at typical sample sizes; cheap insurance against building on a provider with bad coverage. Apply when (a) coverage varies between providers in ways docs don't reveal, (b) building requires committing to one. Build the comparison into a Day 0 gate, not a post-build retrofit.
- **Validate broadly first when the API is cheap; reserve curation for expensive downstream steps.** At validation gates, the temptation is to pick a small "ideal" sample upfront to minimize API calls. But when per-call cost is trivial (e.g., Apify post-fetch at $0.002/post → $0.33 to query 150 profiles for 30 days of posts), broad-coverage testing produces more information for less total effort than sampling-then-spending. The expensive step is usually manual scoring, LLM classification, or human review — sample for *those*, not for the cheap API. Anti-pattern: spending an hour curating "the right 10" when running the full pool costs $0.30 and 5 minutes.

### API Behaviors — undocumented but confirmed
- `{publication_url}/api/v1/notes` returns user's Notes feed (body, timestamps, post attachments). No auth.
- `/api/v1/archive` returns all scoring metadata inline (title, subtitle, description, truncated_body_text, engagement, bylines). No `body_html`.
- `/api/v1/posts/{slug}` returns full `body_html`. More reliable than library's ID-based fetch.
- Notes reshares have `attachments[].type == "post"` with full post metadata including `id` for matching.
- `substack_api.User(handle).get_subscriptions()` returns the user's **public** Substack subscriptions without auth — `[{publication_id, publication_name, domain, membership_state}]`. Used by `src/subscriptions.py` to sync the user's follows into the watchlist. Private/paid subs may not appear; only what shows on the public profile.

## Design Decisions (from brainstorm + review, 2026-04-03)
- Two-stage scoring: Gemini 3.1 Flash (metadata, classification) → Sonnet/Gemini 3.1 Pro (full content, creative)
- Stage 1 threshold: score ≥ 7 = HIGH SIGNAL (gets enrichment), score 6 = WORTH A LOOK (no enrichment)
- Markdown-only output for Phase 1; Zapier webhook is a distinct future feature
- Pydantic models for all inter-stage data; intermediate state files for resumable runs
- Passive feedback loop (watch Josh's Substack activity) was preferred design, but Notes API unavailable
