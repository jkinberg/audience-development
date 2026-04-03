# Project Brief: Substack Neighborhood Mapper

**Status:** Draft
**Date:** March 27, 2026
**Author:** Josh Kinberg
**Type:** Working document — not for publication

---

## Problem

I have ~26 Substack subscribers after publishing 9 articles over 5 weeks. My content is strong — it generates quality engagement on LinkedIn and has driven real career opportunities. But my Substack audience isn't growing because I've treated Substack as a publishing destination and LinkedIn as the distribution engine.

Substack's discovery algorithm rewards in-platform engagement: commenting, restacking, posting Notes, and building relationships with other writers. The algorithm uses these signals to surface your content to new readers. I'm not doing any of this. My Notes feel like posting into the void because the algorithm doesn't know who to show them to — I haven't given it any signal about where I fit in the Substack ecosystem.

The underlying challenge: I don't know my neighborhood. I don't know which Substack publications have audience overlap with mine, which writers are worth building relationships with, or where my editorial thread (product leadership + AI builder + media industry) fits within Substack's network. Without that map, any engagement effort is unfocused.

---

## Goal

Build a tool that systematically maps the Substack landscape around my editorial focus, then use that map to run a focused audience development workflow. The tool reduces the research overhead; the workflow turns that research into subscribers.

**Target outcome:** Reach 100 subscribers within 30 working days (mid-April through mid-May 2026). Growth will come from three channels: Substack-native engagement, 1:1 outreach (Warmstart), and conversion optimization of existing traffic. The key finding is the channel attribution — learning how many subscribers each channel contributes is as valuable as the total number. If Substack-native tactics produce 5 subscribers and Warmstart produces 60, that's a clear signal about where to invest going forward.

---

## Appetite

**Build time box: 3-5 days.**

I don't know how to build this yet, even with Claude Code. The time box includes learning the `substack_api` library, figuring out the recommendation graph crawl, integrating Gemini Flash for topic scoring, and iterating on the output format.

**Day 0 (30-60 min, before committing to the build):** Two steps.

**Step 1: Extract topic signatures from my actual article corpus.** The 9 published articles exist as files in this project. Feed them to Gemini Flash (or run in this Claude project) and extract topic clusters and search keywords: civic data journalism, AI tools for newsrooms, product org design in media, generative AI creative production, leadership in media/tech, audience product strategy, etc. These become the actual search queries for Step 2 — not guesses.

**Step 2: Test the `substack_api` with those extracted keywords.** Install the library. Run `search_posts()` with 3-4 of the extracted topic keywords. Also test `get_recommendations()` on 1-2 secondary seed publications if available (e.g., Evan Shapiro). Evaluate: (a) Does search return relevant posts? (b) How many results per query — is it paginated at 10, 25, 100? This determines whether pre-filtering is needed before scoring. (c) Do recommendations return data? (d) What metadata is available per publication?

This determines which build path to take:

**Path A — Search + Recommendations both work:** Content-based topic search is the primary discovery method. Recommendation graph crawl from secondary seeds supplements with editorially connected publications. Richest output, best portfolio piece.

**Path B — Search works, Recommendations are thin:** Topic search is the only discovery method. Still useful — surfaces publications writing about the same topics. Simpler tool, still produces an actionable neighborhood map.

**Path C — Search is too noisy or limited:** If `search_posts()` doesn't return enough relevant results, the tool pivots to a lighter approach: manually curate an initial list from browsing Substack categories and search, then use the tool to gather metadata and score that list. Less automated discovery, but still saves time on the evaluation step.

**Minimum viable output for Day 1:** A Python script that takes topic keywords from one of my articles, searches Substack for matching posts, groups them by publication, and prints publication names + subscriber counts + recent post titles to the terminal. This is the narrowest vertical slice — everything else layers on top.

Days 1-2 are building the core tool (expanding to all topic queries, adding scoring, generating the output document). Days 3-4 are buffer for debugging, refining output, and re-running with different seeds. Day 5 is buffer. The build clock starts on Day 1 only after Day 0 confirms a viable path.

This is a functional tool, not a polished product. It needs to produce useful output that I can act on, not impress anyone with its interface. But it should be solid enough to demonstrate as a portfolio piece — clean code, clear output, documented approach.

The workflow it enables is ongoing — 15-20 minutes per weekday of Substack engagement, informed by the tool's output. The tool reduces friction in that workflow; it doesn't replace the human engagement.

---

## What the Neighborhood Mapper Does

### Input

**Primary input: my own published articles.** Rather than seeding from publications I follow (which skew toward big-name PM generalists I read as a *reader*, not peers), the tool starts from my content and searches for who else on Substack writes about the same topics. This finds my actual neighbors — not the neighborhood of Shreyas Doshi's audience.

- **Articles to extract topics from (full text available as project files — 9 articles):**
  - "I Found 100 NYC Schools Beating the Odds" — civic data, AI tools for journalism, responsible data product design
  - "The Labor Market They Aren't Measuring" — data journalism, AI and knowledge work, labor market analysis
  - "How I Built 'The Labor Market'" — behind-the-curtain build log, adversarial critique process, editorial product decisions
  - "The AI-Enabled Team Playbook Doesn't Exist Yet" — product team structure, AI transformation in orgs, Shape Up framework
  - "The Whole Product Flywheel" — product org design, capacity allocation, cross-functional leadership
  - "On Creativity with AI: Gravitational Pull vs. Escape Velocity" — AI and creativity, human-AI collaboration, earned wisdom
  - "Remixing Sports Highlights" — generative AI, media production, creative technology, build log
  - "The Mindset Underneath the Work" — leadership resilience, cultural storytelling (Giannis, Bruce Lee, Fred Rogers, Kara Lawson), navigating uncertainty
  - "Playing the Game Well" — leadership behaviors under pressure, accountability, team culture, behavioral frameworks

- **Ideal neighbor profile — the tool is searching for people who fit one or both of these:**
  1. Media/journalism people exploring tech and AI in their industry — newsroom technologists, digital media product thinkers, journalists experimenting with AI tools
  2. Product leaders at media or news companies (not big tech) — people building products for audiences, not enterprise SaaS

- **Secondary input (optional): 1-3 seed publications** that are already in or near this intersection, for recommendation graph crawling if the API supports it. These supplement the topic search — they're not required.
  - Media War & Peace (Evan Shapiro) — media industry strategy
  - Platformer (Casey Newton) — tech/platform journalism (large, but recommendations may point to smaller relevant writers)
  - Additional seeds may emerge from the topic search results — if a discovered publication is clearly in the intersection and has an active recommendation list, it becomes a seed retroactively.

  **Note:** The original approach depended entirely on seeds. This version doesn't. If no strong seed publications are available or currently active, the topic search stands on its own. Don't force a seed list.

  **Explicitly excluded as seeds:** Big PM generalists (Lenny, Shreyas, Elena Verna, etc.) — their recommendation graphs map the broad PM neighborhood, not the media-product-AI intersection. Keep subscribing to them as a reader. Don't use them to find your tribe.

### Process

1. **Extract topic signatures from my articles.** The full text of all 9 published articles is available as project files. Use Gemini Flash to analyze them and produce a set of topic keywords and themes: civic data journalism, AI tools for newsrooms, product org design in media, generative AI creative production, leadership in media/tech, audience product strategy, etc. These become the search queries. Note: this step can be done during Day 0 — it doesn't require the `substack_api` at all.

2. **Search Substack for publications matching those topics.** Use `substack_api`'s `search_posts()` to find posts about these topics. Note: search returns individual *posts*, not publications — multiple posts from the same publication may appear across different topic queries. Note the recency bias in search results: recently published posts surface more prominently, which is actually desirable — we want currently active neighbors, not dormant ones.

3. **Aggregate posts by publication.** Group discovered posts by their parent publication. Count how many topic-relevant posts each publication has, and across how many different topic queries they appear. A publication that surfaces for "AI journalism" AND "media product design" AND "newsroom technology" is a much stronger neighbor signal than one appearing in a single query. Deduplicate. This step likely reduces 100-250 raw post results down to 40-100 unique publications.

4. **Supplement with recommendation graph crawl (if API supports it and seeds are available).** For any secondary seed publications (e.g., Evan Shapiro, Casey Newton, or strong publications discovered through topic search), pull their recommendations. This extends the map through editorial endorsement, catching publications that might not appear in keyword search but are editorially adjacent.

5. **Gather publication metadata.** For each discovered publication: subscriber count (if public), recent post topics and titles, posting frequency, number of recommendations given and received. Note: Notes activity level is desirable but may not be available through the API — confirm during Day 0 validation. If unavailable, use posting frequency and comment volume on long-form posts as a proxy for engagement activity.

6. **Score for relevance against the ideal neighbor profile.** Use Gemini Flash to evaluate each publication against the two neighbor profiles: (a) media/journalism people exploring tech and AI in their industry, (b) product leaders at media or news companies, not big tech. Score on: profile fit, topic overlap with my published articles, cross-topic appearance count from the aggregation step, subscriber range (sweet spot 1K-50K), and posting activity. Gemini Flash handles this as a batch process — classification and pattern matching, not complex reasoning.

7. **Rank and tier.** Produce a ranked list organized into tiers:
   - **Tier 1 (5-8 publications):** High profile fit, active publishing, right subscriber range, strong relationship-building potential. These are the writers to engage with daily.
   - **Tier 2 (10-15 publications):** Moderate fit or less active. Worth following and occasionally engaging.
   - **Tier 3 (the rest):** Low relevance or too large/small for meaningful relationship building. Noted for reference but not prioritized.

### Output
- A ranked, tiered markdown document of publications with: name, URL, subscriber count, relevance scores (Profile A and B), topic summary, cross-topic appearance count, recommendation connections (listed as text, e.g., "recommended by Evan Shapiro, also recommends X and Y"), and 2-3 sentences explaining why each one matters to me

### Future phase (if map proves useful)
- Recommendation graph visualization showing how publications connect to each other (which clusters exist, where I'd fit). The tiered markdown gives you the connection data — the visual is a nice-to-have that adds build time without changing the actionable output.
- Suggested "first moves" for each Tier 1 publication: which recent post to comment on, what angle to take. This requires real-time analysis of individual posts and understanding of my voice — a different capability than the map itself. Defer until after the map is built and the engagement workflow is running.

---

## The Workflow the Tool Enables

The Neighborhood Mapper produces the map. The following workflow is what I actually do with it. The tool reduces the ~2 hours of manual research into a structured output I can act on immediately.

### Setup (one-time, after running the tool)
1. Subscribe to all Tier 1 and selected Tier 2 publications. Turn off email delivery immediately — I follow them in the Substack app/feed, not my inbox.
2. Identify 3-5 posts to comment on in my first week.
3. Set up a simple tracking sheet: date, action taken (comment / restack / Note / DM), publication, any resulting profile views or follows.
4. As I browse Substack during the first 1-2 weeks, manually add any relevant publications I discover through Notes or search that weren't surfaced by the tool. The map is primarily tool-generated but I'll supplement it with what I find through hands-on exploration.

### Daily engagement experiment (25-35 min weeks 1-2, dropping to 15-20 min by week 3-4)

**Weeks 1-2: Try all engagement types and track what produces signal.**
1. Open Substack app or web. Browse feed from subscribed neighborhood publications. Also actively browse Substack search and category pages to discover writers and Notes beyond your home feed — the algorithm hasn't learned your interests yet, so the feed alone won't surface everything relevant.
2. Read 2-3 posts. Choose one to comment on substantively — add genuine value, share a relevant experience, ask a thoughtful question. The goal is a comment good enough to make other readers click my profile. (This takes longer in weeks 1-2 when the publications are unfamiliar.)
3. Restack 1-2 Notes or posts from Tier 1 writers. This is theoretically the highest-leverage algorithm signal — it tells Substack "my audience and this writer's audience overlap."
4. Post 1 original Note. Not article promotion — a standalone thought about product leadership, AI building, or media strategy. Test different types: personal observations, thinking-out-loud, questions to the community, behind-the-scenes of a project, contrarian takes.
5. Log what I did in the tracking sheet (1 min). Track: action type, publication, any resulting profile views or follows.

**Week 3-4: Narrow to the 1-2 highest-leverage activities based on data.** Which actions correlated with profile views and follows? Double down on those. Drop or reduce time on what isn't producing signal.

### Per-article distribution (when I publish, ~20 min)
1. Generate 3-4 Note variants from the article (different types: insight, personal story, question, connection to trending topic). Spread them over 4-7 days.
2. Identify which Tier 1 writers' audiences would specifically care about this article's topic.
3. Restack 1-2 thematically related posts from other writers on the same day — signals a topical cluster to the algorithm.
4. **After 2+ weeks of genuine engagement with a specific writer** (at least 3-4 substantive comments on their work), DM them with a brief personalized note — not "please share my article" but "I wrote something about [topic] that I think connects to what you wrote about [their recent piece]. Thought you might find it interesting." Do not cold-DM writers you haven't engaged with — this backfires on Substack.

### Weekly check-in (15 min, end of week)
1. Review tracking sheet: how many comments, restacks, Notes this week?
2. Check Substack stats: any subscriber growth? Profile views? Which actions correlated?
3. Adjust: which publications are most responsive? Which Notes formats get traction? Double down on what's working.

### 30-day checkpoint — Keep / Pivot / Kill

The tool and the workflow are an experiment. At 30 days, evaluate with these signals:

**Keep (continue and potentially increase investment):**
- The tool surfaced 5+ Tier 1 publications I wouldn't have found through manual browsing
- Substack-native engagement produced any measurable subscriber growth (even modest — 10-15 subscribers)
- I'm seeing profile views, follows, or comment replies from writers in my neighborhood
- The daily engagement routine feels sustainable and is producing compounding familiarity with the neighborhood

**Pivot (the tool works but the workflow needs to change):**
- The tool produced a useful map but daily engagement isn't generating subscriber growth
- The neighbors I found are relevant but their audiences don't convert to my subscribers — may indicate the audience reads Substack in their inbox, not on the platform's social features
- Engagement is producing connections with writers but not subscribers — pivot from broad engagement to focused cross-recommendation relationships

**Kill (deprioritize Substack-native growth):**
- The tool found very few relevant publications — the media-product-AI intersection is too sparse on Substack
- 30 days of daily engagement produced near-zero measurable growth
- The time investment consistently feels like it's competing with higher-value activities (job search, content creation, Warmstart outreach)
- Warmstart and LinkedIn are producing 10x+ the subscribers per hour invested

---

## Technical Approach

**Stack:** Python + `substack_api` library (unofficial, PyPI, last updated March 2026) + Google Gemini Flash API for topic scoring + output as human-readable markdown.

**Why Gemini Flash instead of Claude:** The scoring step is classification and pattern matching, not complex reasoning. Given 100+ publications to score, Gemini Flash is significantly cheaper, has a larger context window, and is fast enough for a batch process. Claude is overkill for this task.

**Build with:** Claude Code.

**Key dependencies:**
- `substack_api` Python library — provides `search_posts()`, `get_recommendations()`, `get_posts()`, post metadata. Read-only operations, no authentication required for public data. **Must validate on Day 0:** (1) Does `search_posts()` return useful results for topic keywords from my articles? (2) Does `get_recommendations()` return data for secondary seed publications? (3) What metadata is available per publication? (4) Is Notes data accessible through any endpoint?
- Google Gemini Flash API — for scoring discovered publications against ideal neighbor profiles. Already have access via Google AI Studio.
- No database needed — output is a human-readable markdown document organized by tier, not raw JSON. Each publication gets a name, URL, subscriber count, relevance score, and 2-3 sentences explaining why it matters to me and how it connects to my editorial focus. The markdown is the deliverable — it's what I act on.

**Rough scoring prompt (to be refined during build):**
```
Given these 5 recent post titles and excerpts from a Substack publication:
[post data]

I'm looking for two types of Substack neighbors:
Profile A: Media/journalism people exploring tech and AI in their industry — 
  newsroom technologists, digital media product thinkers, journalists 
  experimenting with AI tools
Profile B: Product leaders at media or news companies (not big tech) — 
  people building products for audiences, not enterprise SaaS

Score this publication 1-10 on fit with Profile A and 1-10 on fit with Profile B.
Write one sentence explaining the overlap or adjacency to my work.
Flag if this publication bridges both profiles.
Return JSON: { "profileA": N, "profileB": N, "summary": "...", "bridges": bool }
```

**What the tool does NOT do:**
- It does not post Notes, comments, or restacks. Those stay human.
- It does not monitor my engagement or track results. That's a simple spreadsheet.
- It does not require Substack authentication or session cookies. It only accesses public data.

---

## Product Hypotheses

**H1: My audience exists on Substack, just not in the obvious places.**
The big PM newsletters (Lenny, Shreyas, Elena Verna) aren't my neighborhood — they're the broad product community. My actual neighbors are media/journalism people exploring tech and AI, and product leaders at media companies rather than big tech. These people may be writing on Substack with small-to-mid-size audiences. The Neighborhood Mapper will reveal whether this intersection is populated on Substack or if it's too sparse to support a growth strategy.

**H2: Content-based discovery finds better neighbors than graph crawling from famous publications.**
Starting from my own article topics and searching for who else writes about those subjects should surface more relevant neighbors than crawling the recommendation graph of well-known PM generalists. The recommendation graph maps *their* neighborhood. Topic search finds *mine*.

**H3: Small-to-mid-size publications (1K-50K subscribers) are the right relationship targets.**
Writers with 500K subscribers (Lenny Rachitsky) won't notice my comments. Writers with 200 subscribers have no audience to share. The sweet spot is publications large enough to have reach but small enough that a thoughtful commenter gets noticed by both the writer and their readers.

**H4: Consistent engagement compounds faster than great content alone.**
Posting excellent articles without engagement is what I've been doing — and it's produced 26 subscribers. The hypothesis is that 15-20 min/day of strategic engagement, informed by the Neighborhood Mapper, will produce more subscriber growth than publishing a 4th article per month would.

**H5: Substack Notes work differently than LinkedIn posts.**
LinkedIn rewards professional positioning and polished insights. Substack Notes reward vulnerability, thinking-out-loud, and community interaction. The Notes strategy needs to be calibrated to Substack's culture, not just repurpose LinkedIn content. Testing different Note types (personal, question, observation, contrarian) will reveal what resonates with this audience.

---

## Research Questions

**About the landscape:**
- How many Substack publications exist at the media + product + AI intersection? Is this a populated niche or a sparse one?
- Are there writers who fit my ideal neighbor profiles (media/journalism exploring AI, product leaders at media companies) — or is this intersection mostly empty on Substack?
- Does content-based topic search surface different publications than recommendation graph crawling? Are the neighbors I find through my article topics different from the neighbors I'd find by following the PM thought leader recommendation graph?

**About the workflow:**
- What's the minimum daily engagement that produces measurable results? Is 15 min/day enough, or does it take more?
- Which engagement actions have the highest leverage: commenting, restacking, posting Notes, or DM'ing writers?
- How long does it take before the algorithm starts surfacing my content to new audiences? Days? Weeks? Some Substack growth writers claim a 2-3 week ramp-up period before the algorithm has enough signal to distribute your content effectively. Is this true for niche professional topics, or is it an artifact of the "Substack about Substack" echo chamber?

**About my audience:**
- Do the people who engage with product leadership content on Substack look like my LinkedIn audience (Directors, VPs at media/tech companies)? Or is it a different demographic?
- What's the overlap between "people who subscribe to product leadership Substacks" and "people who hire product leaders"? Are these the same people or different populations?
- Is my positioning at the intersection of media + product + AI an advantage (unique, nobody else is here) or a sign that this intersection is too niche to find a Substack audience?

**About content strategy (emerges from the mapping results):**
- Which of my topic areas finds the densest neighborhood on Substack? Do "AI tools for journalism" articles find more active neighbors than "product org frameworks" articles, or vice versa?
- Do those neighborhoods overlap or exist in isolation? If the journalism-AI neighborhood readers would also read my product leadership pieces, then journalism-AI is the entry point for audience building and the full range retains them. If the neighborhoods are siloed, I need to choose which audience to prioritize on Substack.
- My article corpus spans a wide range (civic data, NBA highlights, product frameworks, labor market analysis, leadership behaviors). On LinkedIn that variety works. On Substack, the algorithm builds a topic fingerprint — scattered topics may make it harder for the algorithm to match me with any single neighborhood consistently. The mapping results should reveal whether I need a tighter editorial focus for Substack specifically, even if LinkedIn continues to reward variety.

**About the tool as portfolio piece:**
- Does the Neighborhood Mapper concept resonate with other Substack writers as something they'd want?
- Is this tool novel enough to be worth writing about, or is it solving a problem only I care about?
- Could this extend into a more general "platform audience intelligence" tool that applies beyond Substack?

---

## Risks and Limitations

**The `substack_api` library is unofficial and could break.** Substack has no public API. The Python library reverse-engineers their internal endpoints. It could stop working at any time. Mitigation: the tool only needs to run once (or monthly), not continuously. If the library breaks, I have the map I already built.

**The topic search may surface too much noise.** Searching for "AI journalism" or "media product" on Substack might return hundreds of tangentially related results. Mitigation: the Gemini Flash scoring step filters for the specific neighbor profiles. Accept that the discovery step will be noisy and rely on the scoring step to separate signal from noise. If search is too broad, narrow with more specific keyword combinations extracted from actual article content.

**The recommendation graph from secondary seeds may not extend into my niche.** If the available seed publications don't heavily cross-recommend, the graph crawl adds little value. Mitigation: recommendations are supplemental to topic search, not primary. If the graph crawl produces nothing, the tool still works — it just relies entirely on topic search + scoring.

**Daily engagement requires consistency — my weakest skill.** 15-20 min/day is a daily habit, which I historically struggle with. Mitigation: treat it as a time-boxed morning routine attached to an existing habit (coffee + Substack before starting work). It's also bounded — 15-20 min, not open-ended.

**My audience may simply not be on Substack.** The product leaders and media executives I'm trying to reach may read Substacks in their inbox without ever using the platform's social features. The engagement and Notes strategy would be invisible to them. Mitigation: the 30-day checkpoint is explicitly designed to test this hypothesis. If Substack-native growth doesn't produce results, redirect time to higher-performing channels.

**This project competes with job search time.** April includes TEGNA interviews, spring break, and pipeline replenishment. Audience development cannot crowd out job search activity. Mitigation: the tool build is 3-5 days. The daily workflow is 15-20 min (25-35 in weeks 1-2). If job search demands spike, the daily engagement is the first thing to pause — it's the most dispensable component.

---

## What I'll Learn

Regardless of whether this hits 100 subscribers, running this experiment produces:

1. **A tested hypothesis about platform-native vs. cross-platform audience growth** — real data on whether Substack's discovery engine works for a niche professional audience
2. **A content strategy signal** — which of my topic areas finds the densest Substack neighborhood, whether those neighborhoods overlap, and whether I need a tighter editorial focus for Substack than I use on LinkedIn
3. **A portfolio-quality build** — the Neighborhood Mapper demonstrates product thinking about platform growth mechanics, API integration, and systematic approach to audience development
4. **A publishable story** — "How I mapped my Substack neighborhood and what I learned about building an audience on someone else's platform" works whether the experiment succeeds or fails
5. **Transferable knowledge about the Substack ecosystem** — directly relevant to product roles at media companies, many of which are evaluating or already using Substack
6. **Hands-on experience with agentic tooling** — building a tool that does research and surfaces recommendations is exactly the kind of AI-assisted workflow that product leaders need to understand
