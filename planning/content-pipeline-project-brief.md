# Project Brief: Signal-Based Content Pipeline

**Status:** Draft  
**Date:** April 3, 2026 (updated)  
**Author:** Josh Kinberg  
**Type:** Working document — not for publication  
**Build tool:** Claude Code  
**Replaces:** Neighborhood Mapper Project Brief (March 27, 2026) — the mapper's discovery function is now integrated as Phase 2 of this system  

---

## Problem

I'm trying to grow my Substack audience from ~26 subscribers to 100+ within 30 working days, and build the foundation for continued growth toward 200-500+ subscribers over the following months. I have three growth levers: content production (already working), Warmstart 1:1 outreach (high ROI, needs execution), and Substack Notes engagement (untapped, unproven).

The Substack Notes opportunity is specific: **resharing other creators' content with authentic, additive commentary.** This amplifies other creators' work, gets me visible to their audiences, and gives the Substack algorithm signal about where I fit in the ecosystem. Done well and consistently, this should produce subscriber growth through creator-to-creator engagement — other writers notice me, their readers discover me, and some percentage subscribes.

There are two connected problems:

1. **Discovery:** I don't know which Substack publications and authors are in my niche. My reaction history across Substack (57 likes) and LinkedIn (455 reactions) reveals my interests, but I haven't mapped the broader Substack landscape around those interests. The original Neighborhood Mapper was designed to solve this — but as a one-time tool, it produces a static map that gets stale.

2. **Daily friction:** Even once I know which publications to follow, finding the specific posts worth resharing takes 1-2 hours of manual browsing per day. That's unsustainable alongside job search, content production, and Warmstart outreach.

The solution is a single system that handles both: **discover my neighborhood, then monitor it daily and surface the best reshare candidates.** The discovery function and the daily pipeline are not separate tools — they're phases of the same system, connected by a feedback loop where my reshare choices continuously refine what "signal" means and expand the publications I'm monitoring.

A secondary opportunity exists on LinkedIn: the same resharing-with-commentary strategy works there too, potentially with higher immediate reach given my existing audience of 54%+ senior decision-makers. LinkedIn may produce faster results since hiring managers and executive search recruiters are already there. Whether this audience exists on Substack is an open question — but an engaged Substack audience is gaining credibility in the media space specifically, which makes it worth testing. The system should be designed to support both platforms eventually, with Substack as the Phase 1 build target and LinkedIn as a Phase 3 expansion.

---

## Goal

Build a **Signal-Based Content Pipeline** — a combined discovery + daily curation system that:

1. **Phase 1 (Daily Pipeline):** Monitors ~40-60 Substack publications daily for new posts, scores each post against a Signal Profile derived from my reaction history, identifies the best quotable moment, suggests 2-3 reshare angles, and delivers a daily email digest of the top 5-7 candidates.
2. **Phase 2 (Discovery Engine):** Periodically expands the publication watchlist by crawling recommendation graphs from authors I've reshared, running topic searches via `substack_api`, and surfacing 3-5 new publications weekly for me to evaluate and add.
3. **Phase 3 (LinkedIn Expansion):** Extends the same resharing-with-commentary strategy to LinkedIn, where my existing audience of senior decision-makers could produce faster visibility and lead generation results.

All three phases share the same Signal Profile, scoring logic, and feedback loop. Each reshare I make refines the system's understanding of what "signal" means for me.

**Target output (Phase 1):** 5-7 scored Substack candidates per week, from which I select 2-3 to reshare on Substack Notes. Cadence ramps to daily as the habit builds.

**Target output (Phase 2):** 3-5 new publication recommendations per week, surfaced in a "Discovery" section of the digest.

**Target output (Phase 3):** Same digest format extended to include LinkedIn reshare candidates, either from manual URL intake or from periodic reaction export processing.

**Expected ROI:** 1-2 hours/day finding signal → ~5 minutes/day reviewing the digest and selecting what to reshare. The writing of commentary remains human work (~10-15 min per reshare).

---

## Context: Where This Fits in the 100-Subscriber Sprint

This tool is **not** the primary path to 100 subscribers. The realistic breakdown:

| Channel | Expected Subscribers (30 days) | Confidence |
|---------|-------------------------------|------------|
| Warmstart 1:1 outreach | 20-45 | High — warm contacts, just needs execution |
| Content production + existing traffic | 5-10 | Medium — depends on conversion optimization |
| Substack Notes resharing | 5-15 | Low — unproven hypothesis |
| Conversion optimization (About page, CTAs) | 5-10 | Medium — improves all channels |

**Warmstart gets you to 100. The Content Pipeline builds the engine that gets you from 100 to 500.** Both need to happen in April, but Warmstart has higher urgency and should start first.

---

## Appetite

### Phase 1: Daily Pipeline (Build time box: 3-5 days with Claude Code)

This is the immediate build. A functional tool that produces a useful daily email digest I can act on in 5 minutes. Clean code, documented approach, but no UI beyond the email output.

**Day 0 (1-2 hours): Validate the `substack_api` for this use case.**
- Can `Newsletter.get_posts()` pull recent posts from a publication with enough content to score? (title, subtitle, excerpt or full text, date, engagement metrics)
- Can we pull from 40-60 publications in a single batch run without rate limiting issues?
- How much post content is available without authentication? (We need enough text to identify quotable moments — ideally full post text or at least first 500+ words)

**Days 1-3: Build the core pipeline.**
- Signal Profile scorer (from reaction corpus analysis)
- Substack content monitor (batch pull from publication watchlist)
- Scoring + quotable moment extraction + angle suggestion (Gemini Flash API; upgrade to Claude if output quality insufficient)
- Email digest generation and delivery

**Days 4-5: Polish + buffer.**
- Digest formatting and delivery refinement
- Deduplication logic (don't resurface posts already included in previous digests)
- Documentation and initial watchlist curation

### Phase 2: Discovery Engine (Build time box: 1-2 days, after Phase 1 has been running for 1-2 weeks)

This is the Neighborhood Mapper function, integrated into the pipeline rather than built as a separate tool. It requires reshare data from Phase 1 to work well — the system needs to learn from my actual reshare choices, not just my historical likes.

**What it does:**
- Runs weekly (not daily) — discovery doesn't need real-time cadence
- Pulls recommendation lists from authors I've reshared via `Newsletter.get_recommendations()`
- Runs `substack_api` topic searches using keywords from my corpus (already extracted)
- Scores discovered publications against the Signal Profile
- Surfaces 3-5 new publication recommendations in a "Discovery" section of the weekly digest
- I review and add/reject — accepted publications join the daily watchlist

**Why it waits:** The discovery engine is more useful after I've been resharing for 1-2 weeks because (a) my reshare choices are a tighter signal than my historical likes, and (b) the recommendation graphs of authors I've reshared are more relevant than the graphs of authors I've merely liked.

### Phase 3: LinkedIn Expansion (Build time box: 2-3 days, after Phase 1 proves the resharing hypothesis)

Extends the system to support LinkedIn resharing. Only worth building if Phase 1 demonstrates that the resharing-with-commentary approach generates engagement and/or subscriber growth on Substack — or if I decide the approach is worth testing on LinkedIn regardless because the audience is larger and more immediately valuable.

**What it adds:**
- Manual LinkedIn URL intake (email forwarding or simple form) — when I see something worth resharing on LinkedIn, I drop the URL and the system scores it and suggests angles
- Periodic Apify LinkedIn Reactions export ($2/1,000 reactions) — processes new reactions since last run, identifies posts I liked but didn't reshare, flags high-signal candidates
- Digest format expands to include a LinkedIn section with platform-appropriate angle suggestions (LinkedIn reshares have different norms than Substack Notes)
- Potentially: monitoring LinkedIn profiles of key authors via RSS or periodic scraping, though this adds complexity and cost

**Why it waits:** LinkedIn isn't where I need the tool's help most — I'm already scrolling my feed daily and the friction there is habit, not discovery. The Substack side is where programmatic access (via `substack_api`) gives the tool its biggest advantage. If the resharing strategy proves effective on Substack, extending it to LinkedIn is a high-ROI expansion. If it doesn't work on Substack, the LinkedIn version might still be worth building because the audience is there — but that's a pivot decision, not a pre-planned phase.

### The Feedback Loop (Connects All Phases)

The system gets smarter over time through a continuous feedback loop:

```
Historical reactions (512 from today's analysis)
        │
        ▼
Signal Profile (seed: 5 theme clusters + noise filters)
        │
        ▼
Phase 1: Daily digest → I reshare 2-3 posts/week
        │
        ▼
Reshare history (stronger signal than likes — I put my name on these)
        │
        ├──▶ Refines Signal Profile scoring weights
        │
        └──▶ Phase 2: Discovery engine uses reshared authors'
             recommendation graphs to find new publications
                    │
                    ▼
             New publications enter watchlist
                    │
                    ▼
             Next day's digest includes them → cycle repeats
```

**Periodic re-export of reactions** (bi-weekly or monthly) adds fresh signal:
- Re-run Substack likes HTML export → diff against previous → new likes update Signal Profile
- Re-run Apify LinkedIn Reactions scraper → diff against previous → new reactions update Signal Profile

This means the Signal Profile is never static. It evolves as my interests evolve, my network grows, and my resharing patterns reveal what I actually find worth amplifying (vs. what I passively consume).

---

## Signal Profile

Derived from analysis of 512 reactions across both platforms (57 Substack likes, 455 LinkedIn reactions, January-April 2026). Five theme clusters with weighted scoring:

### Theme Clusters

**1. AI + Product Craft (Weight: HIGH)**
How AI agents change building, team structure, and product development. Includes: AI coding workflows, agent architecture, AI-assisted product management, human-AI collaboration patterns, AI transformation in organizations.
- *Example signals:* Lenny Rachitsky on Simon Willison, Teresa Torres on AI agents, Laura Burkhauser on generalized agents, Tal Raviv on AI product sense, Aakash Gupta on Claude Code patterns

**2. Media Industry Dynamics (Weight: HIGH)**
The business, distribution, and survival questions facing news and media companies. Includes: media business models, streaming economics, audience development for publishers, platform shifts, creator economy intersections with traditional media.
- *Example signals:* Evan Shapiro's Media Universe Map, Dan Rayburn on streaming, Tim Shey/Creatorama on creator economy, Richard Hudock on MSNBC/MS NOW, Anna Magliocco on fandom

**3. Journalism + AI Tooling (Weight: HIGH)**
The specific intersection of newsroom workflows and AI capabilities. Includes: AI for fact-checking, newsroom automation, AI and editorial ethics, open-source journalism tools, local news innovation.
- *Example signals:* Felix Simon on journalists using AI, Evan Hirsch on AI in newsrooms, Scott Klein on open journalism tools, Mark Glaser on shared services for local newsrooms, Sonia Dasgupta/Maria Blanco on young news audiences

**4. Career Identity & Resilience (Weight: MEDIUM)**
Job transitions, what work means, leadership under uncertainty. Includes: layoff recovery, identity beyond title, navigating career change, leadership philosophy, resilience frameworks.
- *Example signals:* Carmen Van Kerckhove ("You are not your job"), Amanda Jane Lee on interview confidence, Brad Stulberg on playing the game in front of you, Leslie Grandy on believing in your capacity, PJ C. on visibility vs. clarity

**5. Creator/Audience Building Mechanics (Weight: MEDIUM)**
How individuals build audiences, platform mechanics, content strategy. Includes: Substack growth tactics, newsletter strategy, video/podcast production, audience engagement patterns.
- *Example signals:* Jay Clouse on content strategy, Kenyatta Cheese/Everybody At Once, Baratunde Thurston on community, Ben Collins on The Onion's strategy

### Noise Filters (reduce score or exclude)

- **Personal milestone celebrations** — "I'm happy to share I'm starting a new position" posts. These are personal-connection reactions, not content-interest signal. Exception: if the post includes substantive commentary about the role/industry beyond the announcement.
- **Pure political commentary** — partisan takes without connection to media/tech/product themes.
- **Art/visual posts without editorial substance** — beautiful but not reshare-worthy for positioning purposes.
- **Generic motivational content** — "believe in yourself" without specific, earned insight.
- **Content from mega-accounts (500K+ followers)** — resharing Scott Galloway or Adam Grant doesn't differentiate you. Exception: if you have a genuinely contrarian or additive take.

### Scoring Approach

Each post gets scored 0-10 on:
- **Theme fit** (0-5): How strongly does this match one or more of the five clusters?
- **Reshare potential** (0-3): Does this post contain a specific insight, data point, or argument that I can add genuine value to with commentary? (vs. content that's interesting to read but doesn't invite a "here's my take" response)
- **Creator relationship value** (0-2): Is the author someone in my target neighborhood (1K-50K subscribers, media/product/AI intersection) where engagement could build a real relationship? Bonus for authors I've already engaged with.

**Threshold for inclusion in digest:** Score ≥ 6/10. Aim for 5-7 posts per digest, ranked by score.

---

## Technical Architecture

### System Overview (All Phases)

```
┌─────────────────────────────────────────────────────────────┐
│                     SIGNAL PROFILE                           │
│  5 theme clusters + noise filters + scoring weights          │
│  Seeded from: 512 historical reactions (Substack + LinkedIn) │
│  Updated by: reshare history + periodic reaction re-exports  │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────────┐
          │                │                    │
          ▼                ▼                    ▼
   ┌─────────────┐  ┌─────────────┐   ┌──────────────────┐
   │  PHASE 1    │  │  PHASE 2    │   │  PHASE 3         │
   │  Daily      │  │  Weekly     │   │  LinkedIn        │
   │  Pipeline   │  │  Discovery  │   │  Expansion       │
   └──────┬──────┘  └──────┬──────┘   └────────┬─────────┘
          │                │                    │
          ▼                ▼                    ▼
   ┌─────────────────────────────────────────────────────────┐
   │                   DAILY DIGEST EMAIL                     │
   │  🟢 High Signal (reshare candidates from watchlist)      │
   │  🔍 Discovery (new publications to evaluate) [Phase 2]   │
   │  📥 LinkedIn (manual intake candidates) [Phase 3]        │
   └──────────────────────────┬──────────────────────────────┘
                              │
                              ▼
                     I reshare 2-3/week
                              │
                              ▼
                ┌─────────────────────────┐
                │    FEEDBACK LOOP         │
                │  Reshare choices refine  │
                │  Signal Profile +        │
                │  expand watchlist via    │
                │  recommendation graphs   │
                └─────────────────────────┘
```

### Phase 1 Components (Daily Pipeline)

```
┌─────────────────────────────────────────────────┐
│                PUBLICATION WATCHLIST              │
│  ~40-60 Substack publications (JSON config)      │
│  Seeded from: reaction corpus + manual curation  │
│  Expanded by: Phase 2 discovery engine           │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              CONTENT MONITOR                     │
│  Daily batch pull via substack_api               │
│  Get new posts from each publication (last 24h)  │
│  Extract: title, subtitle, excerpt, URL, date,   │
│  author, engagement metrics                      │
│  Deduplicate against previous digests            │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
              ┌──────────────────────────┐
              │     SIGNAL SCORER        │
              │  Gemini Flash API        │
              │  Score against 5 themes  │
              │  Apply noise filters     │
              │  Extract best quote      │
              │  Suggest 2-3 angles      │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │     DIGEST GENERATOR     │
              │  Filter: score ≥ 6       │
              │  Rank and format         │
              │  Generate email digest   │
              │  Send via SendGrid/SES   │
              └──────────────────────────┘
```

### Stack (Phase 1)

- **Python 3.12+** — primary language
- **`substack_api` v1.2.0** — Substack content retrieval (read-only, no auth required for public posts)
- **Google Gemini Flash API** — scoring, quote extraction, angle suggestion. This is classification and pattern matching, not complex reasoning — Gemini Flash is significantly cheaper than Claude and fast enough for a batch process of 40-60 posts. Already have access via Google AI Studio. If angle suggestion quality is insufficient with Flash, upgrade that specific step to Claude Sonnet while keeping scoring on Flash.
- **Email delivery** — SendGrid free tier (100 emails/day) or Amazon SES ($0.10/1,000 emails). Just one email per day to one recipient.
- **JSON config files** — publication watchlist, Signal Profile weights, scoring thresholds, reshare history log. No database needed.
- **Cron job or scheduled task** — runs once daily, early morning ET (6-7am), so digest is waiting when I start my day.

### Additional Dependencies (Phase 2)

- **`substack_api` `get_recommendations()`** — pulls recommendation lists from publications I've reshared
- **`substack_api` topic search** — periodic search using keywords from my corpus to discover new publications
- **Reshare history log** (JSON or simple CSV) — tracks which posts I reshared, to which platform, and when. Fed back into Signal Profile refinement and used to determine which authors' recommendation graphs to crawl.

### Additional Dependencies (Phase 3)

- **LinkedIn URL intake** — email forwarding (Gmail alias) or simple web form for manual URL submission
- **Apify LinkedIn Profile Reactions scraper** — periodic batch export ($2/1,000 reactions) to capture new reactions for Signal Profile updates
- **LinkedIn content fetching** — when a URL is submitted, fetch post content for scoring. Options: web scraping (fragile) or require pasting content alongside URL (more reliable).

### Hosting / Runtime

**Production runtime: cloud webserver.** My laptop is a traveling machine — lid closed, not always plugged in, not always on. This cannot run locally in production. It needs a cheap, always-on server.

**Options (pick during build):**
- GitHub Actions (free for public repos, 2,000 min/month for private) — simplest for a scheduled job
- Railway ($5/month) or Render cron job — simple deployment, minimal cost
- Any lightweight hosting that supports a daily Python cron job

**Local machine for dev/testing only.** Build and iterate locally with Claude Code, deploy to cloud when the pipeline is working.

### Output & Delivery

**Primary output: markdown file.** The digest is generated as a structured markdown document. This is the canonical output regardless of delivery mechanism.

**Delivery is flexible — decide during build:**
- Email (SendGrid free tier, Amazon SES) — shows up in inbox each morning
- Zapier webhook — can route the markdown output to any connected service (email, Slack, Notion, etc.)
- Claude Cowork pickup — if Cowork supports reading from a cloud-hosted file or webhook, the digest could surface as a Dispatch notification
- Direct file access — the markdown file lives on the server and can be accessed via URL

**Don't over-engineer delivery.** The delivery mechanism is the least important design decision. Start with whatever is fastest to implement. Change it later if a better option emerges.

### Future State: Agentic Architecture

The phased build path points toward a persistent agent — a system that monitors, scores, surfaces, and eventually drafts reshare content autonomously. This is a genuine interest beyond just audience development: building an agent is itself a portfolio-worthy capability and aligns with the "AI + Product Craft" theme cluster.

The progression:
- **Phase 1-3 (current scope):** Scheduled script. Runs daily, produces output, I act on it. Not agentic — it's automation.
- **Phase 4 (future, not scoped):** Persistent agent. Could be a Cowork plugin, an OpenClaw-style agent, or whatever the agentic platform landscape looks like by then. The agent monitors feeds continuously (not just daily), learns from my reshare patterns in real-time, and potentially drafts commentary in my editorial voice (using the Editorial Voice skill or a derivative).

**Phase 4 is not in scope for this build.** But the architecture should be designed so that the scoring logic, Signal Profile, and feedback loop are modular enough to be wrapped in an agentic framework later without a rewrite. This means: clean separation between content fetching, scoring, and output generation. No monolithic script.

---

## Publication Watchlist (Initial Seed)

Derived from reaction corpus analysis. To be expanded after Day 0 validation and manual curation.

### Tier 1 — High Signal (engage actively, monitor daily)

**From Substack reactions (already liked their content):**
- Evan Shapiro (@eshap) — Media War & Peace — media industry strategy, Media Universe Map
- Julie Zhuo (@joulee) — The Looking Glass — product leadership, AI + product
- Mike Troiano (@miketrap) — People Stuff — leadership, scaling, AI + writing
- Tim Shey (@timshey) — Creatorama — creator economy, YouTube, media
- Kenyatta Cheese (@kenyatta) — Everybody At Once — audience, community, media
- Felix Simon (@felixsimon) — journalism + AI research
- Claire Vo (@clairevo) — AI agents, product leadership
- Brian Balfour (@brianbalfour) — Reforge, growth, product leadership

**From LinkedIn reactions (high weighted score, may have Substack):**
- Evan Hirsch — AI for journalists and creators (verify Substack presence)
- Christina Wodtke — product leadership, OKRs (verify Substack presence)
- Laura Burkhauser / Descript (@descriptapp) — AI creative tools, Fort Human
- John Cutler — product leadership (verify Substack presence)
- Scott Klein — open journalism, newsroom tools (verify Substack presence)

### Tier 2 — Moderate Signal (monitor, engage selectively)

- Aakash Gupta (@aakashgupta) — PM frameworks, Claude Code
- Brad Stulberg (@bradstulberg) — resilience, performance
- Carmen Van Kerckhove (@carmenvankerckhove) — career identity
- Derek Thompson (@derekthompson) — cultural analysis, economics
- Erika Lee Sears (@erikaleesears) — visual artist (unlikely reshare candidate but community engagement)
- Lenny Rachitsky — PM generalist (too large for relationship-building, but content is reshare-worthy)
- Scott Galloway (@profgalloway) — media/business (too large, but occasional reshare-worthy takes)

### Tier 3 — Discovery Pool (to be populated)

- Publications found through `substack_api` topic searches using keywords from my corpus
- Publications recommended by Tier 1 writers (via `get_recommendations()`)
- Publications I discover manually through Substack browsing

---

## Digest Format (Email)

```
Subject: Signal Pipeline — [Date] — [N] posts worth your attention

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 HIGH SIGNAL

1. [Post Title]
   by [Author Name] · [Publication] · [Date]
   Score: 8/10 | Themes: AI + Product, Media Industry
   
   📌 Best quote: "[Extracted quotable moment — 1-2 sentences]"
   
   Reshare angles:
   • [Angle 1: e.g., "Connect to your NBC experience with editorial AI tools"]
   • [Angle 2: e.g., "Contrast with the 'AI replaces editors' narrative"]
   • [Angle 3: e.g., "Ask your audience: how is your newsroom handling this?"]
   
   🔗 [Substack URL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. [Post Title]
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 WORTH A LOOK

3. [Post Title]
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 DISCOVERY (Phase 2 — weekly)

New publications found via recommendation graphs and topic search:
• [Publication Name] — [Subscriber count] — [Why it matches your signal]
  → Add to watchlist? [Y/N — respond to this email or update config]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 LINKEDIN INTAKE (Phase 3 — from your manual submissions)

4. [LinkedIn Post Title/First Line]
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PIPELINE STATS
Publications monitored: 47
New posts scanned today: 23  
Posts scoring ≥ 6: 5
Reshares this week: 2
Signal Profile last updated: [date]
```

---

## Hypotheses

**H1: Strategic resharing with commentary on Substack Notes produces subscriber growth.**
Resharing high-quality content from neighborhood creators with genuine, additive commentary gets me visible to their audiences. Some percentage of those readers click my profile, read my content, and subscribe. This is a slower growth channel than direct outreach but compounds over time as creator relationships develop.

**H2: A curated watchlist produces better signal than algorithmic feed browsing.**
Monitoring a deliberately chosen set of 40-60 publications, filtered through my Signal Profile, surfaces more reshare-worthy content than scrolling Substack's algorithmic feed. The algorithm doesn't know my interests yet; the watchlist does.

**H3: Reshare-driven discovery finds better neighbors than one-time topic search.**
The original Neighborhood Mapper relied on topic keyword searches to find publications. This system discovers new publications through the recommendation graphs of authors I've actually reshared — a tighter signal than keyword matching. Over time, the watchlist should converge on my true niche more accurately than a one-shot search could.

**H4: Pre-identified quotes and angles reduce the activation energy enough to make resharing sustainable.**
The reason I don't reshare consistently isn't lack of interest — it's the friction of finding content, identifying the right angle, and drafting the commentary. Reducing discovery + angle identification to a 5-minute email scan makes the habit sustainable. This maps to my known weakness with daily habits: structured, completable tasks work; open-ended browsing doesn't.

**H5: Creator engagement through resharing leads to reciprocal engagement.**
When I consistently reshare and amplify a Tier 1 creator's work with substantive commentary, they notice. This leads to follows, restacks of my content, cross-recommendations, and access to their audience. This is the compounding mechanism.

**H6: The same resharing strategy works on LinkedIn, possibly with higher immediate ROI.**
LinkedIn already has my audience (54%+ senior decision-makers, hiring managers, executive recruiters). Resharing content with a smart take positions me as a thoughtful voice without requiring original long-form content for every post. The reach per reshare on LinkedIn may exceed Substack Notes significantly in the near term, even if the Substack audience is more durable long-term.

**H7: The Signal Profile refines itself through reshare feedback faster than through likes.**
Resharing is a higher bar than liking — I'm putting my name and reputation behind the content. Posts I reshare are a tighter definition of "signal" than posts I passively like. The feedback loop from reshare history should produce a more accurate Signal Profile within 2-3 weeks than the initial seed from 512 historical reactions.

---

## Keep / Pivot / Kill Signals (30-Day Checkpoint)

### Keep (continue and increase investment)
- Reshared content is getting engagement (likes, restacks, comments on my Notes)
- At least 2-3 creators from the watchlist have engaged back (liked my reshare, followed me, commented on my content)
- Substack profile views are increasing week-over-week
- Any measurable subscriber growth attributable to Notes activity (even 5-10 subscribers)
- The digest is producing 3+ actionable items per week consistently
- The daily workflow feels sustainable at ~15-20 min total (5 min digest review + 10-15 min writing commentary)

### Pivot (tool works, strategy needs adjustment)
- Digest surfaces good content but resharing isn't generating engagement → pivot to commenting on original posts instead of resharing (lower visibility but more direct relationship-building)
- Substack resharing isn't working but LinkedIn resharing is → redirect the tool's output toward LinkedIn-first distribution
- The watchlist is too narrow → add periodic `substack_api` topic searches to discover new publications weekly
- Creators are engaging back but their audiences aren't converting → pivot to cross-recommendation requests instead of hoping for organic discovery

### Kill (deprioritize this tool)
- 30 days of consistent resharing produces near-zero engagement or subscriber growth
- The digest quality is poor — most scored posts aren't actually reshare-worthy despite high scores (Signal Profile needs fundamental rework)
- The time investment consistently competes with higher-value activities (Warmstart, job search, content production)
- Warmstart and direct outreach are producing 10x the subscribers per hour invested, making Notes engagement a poor use of time

---

## Sequencing (April–May 2026)

### Week of April 7-11 (back from spring break)
- **Priority 1:** Start Warmstart 14-day free trial. Create account, run first contact scan, send first 20-30 personalized outreach emails. (14-day trial runs through April 21.)
- **Priority 2:** Day 0 validation for Content Pipeline — test `substack_api` with publication watchlist
- **Priority 2:** Begin Phase 1 build with Claude Code (Days 1-3)

### Week of April 14-18
- **Warmstart:** Continue outreach, aim for 50+ total messages sent
- **Phase 1:** Complete build (Days 4-5), first daily digest delivered
- **Resharing experiment begins:** 2-3 Substack Notes reshares from digest per week
- **TEGNA:** Final interview process resolving this week

### Week of April 21-25
- **Warmstart trial ends ~April 21:** Evaluate — worth paying $99/month, or switch to manual outreach?
- **Resharing:** Continue 2-3/week cadence, track engagement (profile views, follows, engagement from creators)
- **Content:** Publish 1 new article, distribute via existing workflow
- **Phase 2 build decision:** If Phase 1 is running smoothly and producing actionable digests, begin Phase 2 discovery engine build (1-2 days)

### Week of April 28 – May 2
- **Phase 2:** First weekly discovery scan runs, surfaces new publication recommendations
- **Resharing:** Evaluate ramping to daily cadence if 2-3/week is sustainable and producing signal
- **Feedback loop:** First Signal Profile refinement based on 2-3 weeks of reshare data

### Week of May 5-9 (30-day checkpoint)
- **Warmstart evaluation:** How many subscribers did outreach produce? Channel attribution.
- **Resharing experiment evaluation:** Keep / Pivot / Kill based on signals below
- **Subscriber count check:** Where are we relative to 100? Which channel produced what?
- **Phase 3 decision:** If resharing is working on Substack, is it worth extending to LinkedIn? If resharing isn't working on Substack, is LinkedIn worth trying as a pivot?
- **Tool assessment:** Is the digest useful? Is the discovery engine expanding the watchlist meaningfully?

---

## What I'll Learn

Regardless of subscriber count:

1. **Whether Substack Notes resharing produces measurable growth** for a niche professional audience — real data, not theory
2. **Whether reshare-driven discovery finds my actual neighborhood** — does the recommendation graph of authors I reshare lead to better publications than keyword search alone?
3. **Which theme clusters generate the most engagement** when reshared — this informs both content strategy and which neighborhood to invest in
4. **Whether the Signal Profile accurately predicts my interest** — the scoring model is derived from past reactions, but it may need tuning as I learn what's actually reshare-worthy vs. just interesting to read
5. **Whether the feedback loop actually works** — does the system get smarter over 30 days? Do my reshare choices produce a tighter Signal Profile and a more relevant watchlist?
6. **Channel attribution data** across Warmstart, Notes resharing, and organic traffic — the most valuable strategic finding for deciding where to invest post-30-days
7. **Whether this approach should expand to LinkedIn** — if resharing works on Substack, LinkedIn is a natural expansion. If it doesn't, LinkedIn might be the better platform for this strategy given the larger, more established audience.
8. **A portfolio-quality build** demonstrating product thinking about content curation, recommendation systems, API integration, and AI-assisted workflow design — stronger portfolio story than the original Neighborhood Mapper because it's an operational system, not a one-shot tool
9. **A publishable story** — "How I built an AI-powered content pipeline to grow my Substack audience" works as a future article whether the experiment succeeds or fails

---

## Open Questions (Resolve During Build)

### Phase 1 (resolve during Days 0-5)
1. **How much post content does `substack_api` return without authentication?** If only titles and excerpts, the scoring and quote extraction will be less precise. May need to supplement with web fetching of full post content.
2. **Rate limiting on `substack_api`?** Pulling from 40-60 publications daily = 40-60 API calls minimum. Need to test whether this triggers rate limits and add appropriate delays.
3. **Gemini Flash API cost at scale?** ~50 posts/day scored with Flash. Estimate ~500-1,000 tokens per scoring call. Flash pricing is significantly cheaper than Claude — likely well under $0.10/day. Confirm during build.
4. **Email delivery reliability?** SendGrid free tier has 100 emails/day limit — more than enough. But need to handle formatting (HTML email with the digest structure above) and ensure it doesn't land in spam. Alternative: skip email entirely and use Zapier webhook or direct markdown file access.
5. **Is Gemini Flash sufficient for angle suggestion, or does that step need Claude?** Scoring and quote extraction are straightforward classification. Angle suggestion is more nuanced — it needs to understand my specific positioning and experience to suggest genuinely useful reshare angles. Test with Flash first; upgrade to Claude Sonnet for angle generation only if needed.

### Phase 2 (resolve after 1-2 weeks of Phase 1 usage)
6. **Does `get_recommendations()` return useful data for the publications I'm resharing?** Some publications may not have public recommendation lists. Need to test during Phase 2 build.
7. **How many new publications does the discovery scan surface per week?** If the recommendation graphs are thin, topic search may need to carry more weight. If they're rich, the discovery engine could expand the watchlist faster than expected (which creates its own curation problem).
8. **How should the Signal Profile refinement work mechanically?** Options: manually adjust weights based on reshare patterns, or build an automated adjustment based on reshare frequency by theme cluster. Start manual, automate later if patterns are clear.

### Phase 3 (resolve before LinkedIn expansion)
9. **LinkedIn content fetching?** When I submit a LinkedIn URL, how do we get the post content? LinkedIn doesn't have a public content API. Options: web scraping (fragile), or I paste the content alongside the URL (more manual but reliable).
10. **Is the Apify periodic batch export worth the cost for Signal Profile updates?** At $2/1,000 reactions, a monthly re-export is cheap. But does the incremental signal improve the system meaningfully, or is reshare history sufficient?
11. **Should LinkedIn reshares be tracked differently than Substack reshares?** LinkedIn has different engagement norms (comments, reactions, shares) and the reshare format differs. The angle suggestions may need platform-specific calibration.
