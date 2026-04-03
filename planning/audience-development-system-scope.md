# Audience Development System — Full Scope

**Author:** Josh Kinberg
**Date:** March 27, 2026
**Status:** Draft — System Design
**Purpose:** Systematic approach to growing Substack newsletter subscribers through two parallel funnels, with agentic tools to reduce manual overhead

---

## The Core Insight

The email subscriber list is the asset. Substack is the infrastructure. Discovery happens through multiple channels. The system's job is to turn discovery into subscriptions efficiently — and to make the process measurable so you know what's working.

Current state: ~1,000 visits, ~26 subscribers (~2.6% conversion). Industry benchmark for a well-optimized Substack: 5-15% conversion. **Doubling subscriber count may not require more traffic — just better conversion of existing traffic.**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DISCOVERY LAYER                       │
│                                                         │
│  Funnel 1: LinkedIn          Funnel 2: Substack-Native  │
│  (Proven, declining reach)   (Unproven, testing)        │
│                                                         │
│  • LinkedIn posts            • Notes engagement         │
│  • 1:1 outreach (Warmstart)  • Cross-recommendations    │
│  • Community seeding         • Strategic restacking      │
│  • Professional word-of-mouth• Neighborhood commenting  │
│                                                         │
└──────────────────┬──────────────────┬───────────────────┘
                   │                  │
                   ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                  CONVERSION LAYER                        │
│                                                         │
│  • About page (first impression for new visitors)       │
│  • Article CTAs (in-content subscribe prompts)          │
│  • Welcome email (confirms value of subscribing)        │
│  • Content quality (the actual reason to stay)          │
│                                                         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   THE ASSET: EMAIL LIST                  │
│                                                         │
│  Subscribers receive content in their inbox regardless  │
│  of whether they use Substack, LinkedIn, or neither.    │
│  Direct relationship. No algorithm dependency.          │
│                                                         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  MEASUREMENT LAYER                       │
│                                                         │
│  • Subscriber source tracking (which funnel?)           │
│  • Conversion rate by article and channel               │
│  • Engagement tracking (opens, clicks)                  │
│  • Feedback loop → refine discovery + conversion        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### COMPONENT 1: Conversion Optimization
**Priority: HIGH — do this first**
**Type: Manual / one-time setup**
**Estimated effort: 2-3 hours**

This is the highest-leverage move because it improves every channel simultaneously. Every LinkedIn click, every Substack Note view, every 1:1 outreach that drives someone to your page — all benefit from better conversion.

Tasks:
- [ ] Audit current About page — does it clearly answer "why subscribe?"
- [ ] Rewrite About page as a conversion page: who you are, what you write about, what a subscriber gets, social proof (Chalkbeat quote, LinkedIn reach stats)
- [ ] Add/improve subscribe CTAs within articles (not just at the bottom — early and mid-article)
- [ ] Draft welcome email for new subscribers (what to expect, 2-3 best articles to start with)
- [ ] Establish conversion baseline: track visits vs. new subscribers per article

**Buildable tool: None needed.** This is editorial and design work. Manual but high-impact.

---

### COMPONENT 2: LinkedIn Funnel Optimization
**Priority: HIGH — your proven channel**
**Type: Mostly manual, some tracking automation**
**Estimated effort: Ongoing (already doing this)**

You're already doing the hard part (creating and posting content). The optimization is about tracking what converts to subscribers, not just what gets impressions.

Tasks:
- [ ] For each LinkedIn post promoting a Substack article, track: impressions, clicks (if available), resulting Substack visits, resulting subscribers
- [ ] Identify which article types convert best (project posts vs. think pieces vs. frameworks)
- [ ] Test different LinkedIn post formats: link in body vs. comments, different hooks, different CTAs
- [ ] Continue existing 2x/month posting cadence

**Buildable tool: Conversion Tracker.**
- Input: LinkedIn post metrics (manual entry from analytics exports) + Substack subscriber data
- Function: Correlate LinkedIn posts with subscriber spikes; identify which content types and post formats drive the most conversions, not just impressions
- Output: Dashboard showing cost-per-subscriber equivalent by content type and format
- Technical: Python script pulling Substack stats via unofficial API + manual LinkedIn data entry. Could be a simple Jupyter notebook or a lightweight web dashboard.

---

### COMPONENT 3: 1:1 Outreach (Warmstart)
**Priority: HIGH — untested but highest expected conversion rate**
**Type: Tool-assisted manual outreach**
**Estimated effort: 14-day trial, then ongoing 30 min/week**

1:1 personalized outreach to existing contacts who should be reading your content. Highest conversion rate of any channel because of the personal relationship.

Tasks:
- [ ] Start Warmstart 14-day trial
- [ ] Identify first batch of 20-30 contacts who would genuinely benefit from a specific article
- [ ] Send personalized outreach — not "subscribe to my newsletter" but "I wrote this and thought of you because [specific reason]"
- [ ] Track: messages sent, articles shared, resulting subscribers
- [ ] After trial: evaluate whether Warmstart is worth continuing vs. building your own lightweight outreach tracker

**Buildable tool: Possibly — depends on Warmstart trial results.**
- If Warmstart works well, just use it
- If the manual process reveals automatable patterns, build a lightweight "Article-Contact Matcher" that suggests which contacts to share each new article with based on their professional interests

---

### COMPONENT 4: Substack-Native Growth
**Priority: MEDIUM — worth testing but unproven for your audience**
**Type: Manual engagement + agentic research support**
**Estimated effort: 15-20 min/day engagement + one-time neighborhood mapping**

The hypothesis: product leaders and AI builders exist on Substack and can discover your content through the platform's native mechanisms (Notes, recommendations, restacking). This needs to be tested, not assumed.

**Phase 4a: Neighborhood Mapping (one-time)**
- [ ] Identify 15-20 Substack publications in adjacent spaces (product leadership, AI in media, journalism strategy, leadership/management)
- [ ] Subscribe to each, turn off email delivery
- [ ] Map the recommendation graph — who recommends whom?
- [ ] Identify 5-8 high-priority relationship targets (writers with overlapping audience, active Notes presence, open to cross-recommendations)

**Buildable tool: Neighborhood Mapper (strongest portfolio project candidate)**
- Input: 3-5 seed Substack URLs + your published article topics
- Function: Crawl the Substack recommendation graph using unofficial Python API. For each publication: pull subscriber count (if public), recent post topics, recommendation list, Notes activity level. Score by topic overlap with your editorial thread (product leadership + AI builder).
- Output: Ranked list of publications with: relevance score, subscriber count, recommendation connections, suggested engagement approach
- Technical: Python + `substack_api` library + Claude for topic analysis. Could extend to monitor new publications entering the space over time.
- Portfolio angle: "I built a tool to systematically map niche communities on emerging social platforms" — demonstrates product thinking about platform growth mechanics

**Phase 4b: Daily Engagement Routine (ongoing)**
- [ ] Read 2-3 posts from neighborhood publications
- [ ] Leave 1 substantive comment per day
- [ ] Restack 1-2 relevant Notes/posts
- [ ] Post 1 original Note (standalone thought, not article promotion)
- [ ] Track: which engagement actions correlate with profile views and follows

**Buildable tool: Daily Digest Agent**
- Input: Your 15-20 subscribed publications
- Function: Each morning, pull recent posts using `substack_api`, use Claude to rank by "could Josh add substantive value in comments on this?" based on topic relevance to his editorial thread
- Output: Top 5 posts to engage with today, with suggested comment angles
- Technical: Python + `substack_api` + Claude API for ranking/suggestion

**Phase 4c: Multi-Note Article Distribution (per article)**
- [ ] For each published article, generate 3-4 Substack Notes spread over 4-7 days
- [ ] Note types: standalone insight, personal story/behind-the-scenes, question to community, connection to trending topic
- [ ] Notes should work as standalone content, not just article promotion

**Buildable tool: Notes Generator**
- Input: Published article text + editorial voice guidelines
- Function: Generate 3-4 Note variants, each a different type, calibrated for Substack tone (more personal, more thinking-out-loud than LinkedIn). Include suggested posting schedule.
- Output: Draft Notes ready for human review/editing + posting calendar
- Technical: Claude API with your Editorial Voice skill adapted for Substack tone
- Note: This is the easiest build and could be done as a Claude Skill rather than a standalone tool

**Phase 4d: Cross-Recommendations (after 4-6 weeks of engagement)**
- [ ] After building genuine relationships through commenting and restacking, propose mutual recommendations to 3-5 aligned writers
- [ ] Monitor which recommendations drive subscriber growth

---

### COMPONENT 5: Community Seeding
**Priority: MEDIUM — high potential but requires research**
**Type: Manual with research support**
**Estimated effort: 30 min per article published**

Share specific articles in communities where they're genuinely relevant — not spam, but value-add.

Tasks:
- [ ] Identify 5-10 professional communities (Slack groups, Discord servers, forums) where your target audience gathers
- [ ] For each article, identify which 2-3 communities would find it most relevant
- [ ] Share with tailored context explaining why it's relevant to that community
- [ ] Track: which communities drive clicks and subscribers

Known targets:
- News Product Alliance (journalism + product)
- Lenny's Newsletter Slack (product leadership)
- Reforge alumni community (product strategy)
- NICAR / journalism-tech communities (for civic data pieces)
- Generative AI communities (for AI builder pieces)

**Buildable tool: Community-Article Matcher**
- Input: Article topic + your community list with topic tags
- Function: Suggest which communities to share each article in, with draft context messages tailored to each community's norms
- Output: Distribution checklist per article
- Technical: Simple matching logic, could be a Claude Skill or even a structured prompt

---

### COMPONENT 6: Measurement & Learning Loop
**Priority: HIGH — without this, you're guessing**
**Type: Agentic tracking + weekly human review**
**Estimated effort: 5 min/day logging, 15 min/week review**

Tasks:
- [ ] Establish baseline metrics: current subscribers, visit-to-subscribe conversion rate, subscriber sources
- [ ] Track per-article: visits, new subscribers, source channel
- [ ] Track engagement experiments: which Notes formats, comment approaches, community shares drive results
- [ ] Weekly 15-min review: what worked, what didn't, what to adjust

**Buildable tool: Growth Analytics Dashboard**
- Input: Substack stats (via API) + manual channel tracking
- Function: Correlate actions with outcomes. "This week you commented on 5 posts, restacked 3, posted 4 Notes, shared in 2 communities → gained X subscribers. Previous week with different activity mix → gained Y."
- Output: Weekly summary with patterns and recommendations
- Technical: Python + `substack_api` for Substack data + simple tracking spreadsheet for manual inputs + Claude for pattern analysis

---

## Buildable Tools Summary

| Tool | Effort | Portfolio Value | Practical Value | Build When |
|------|--------|----------------|-----------------|------------|
| Neighborhood Mapper | Medium (1-2 days) | HIGH | HIGH | April — after Warmstart trial starts |
| Notes Generator | Low (half day) | LOW | MEDIUM | April — could be a Claude Skill |
| Daily Digest Agent | Medium (1-2 days) | MEDIUM | MEDIUM | May — after neighborhood established |
| Conversion Tracker | Low-Medium (1 day) | MEDIUM | HIGH | April — alongside manual tracking |
| Growth Analytics | Medium (1-2 days) | MEDIUM | HIGH | May — after 4-6 weeks of data |
| Community-Article Matcher | Low (half day) | LOW | LOW | Optional — may not need a tool |

**Strongest single build for dual purpose (portfolio + practical):** Neighborhood Mapper. It demonstrates product thinking about platform growth, uses real APIs, and produces genuinely useful output. It's also the most novel — there's nothing like it publicly available.

**Strongest Substack article from this work:** "How I Built a Systematic Audience Development Engine — And What I Learned About Platform-Native vs. Cross-Platform Growth." Write this after 60-90 days of running the system with real data.

---

## Recommended Sequencing

### Week 1-2 (Early April)
**Theme: Fix the foundation**
- [ ] Rewrite Substack About page as conversion page
- [ ] Add stronger CTAs to existing articles
- [ ] Draft welcome email sequence
- [ ] Start Warmstart 14-day trial — send first 10 personalized outreach messages
- [ ] Establish baseline metrics (current conversion rate, subscriber sources)
- [ ] Subscribe to 10 neighborhood Substack publications (emails off)
- [ ] Begin daily 15-min engagement: read, comment, restack

### Week 3-4 (Mid-April)
**Theme: Test and build**
- [ ] Continue Warmstart outreach — aim for 30+ messages sent
- [ ] Build Neighborhood Mapper with Claude Code (strongest build candidate)
- [ ] Run Neighborhood Mapper on seed publications — expand map
- [ ] Build Notes Generator as Claude Skill (low effort, immediate use)
- [ ] Generate multi-Note sequences for next 2 articles
- [ ] Continue daily Substack engagement routine

### Week 5-8 (May)
**Theme: Measure and optimize**
- [ ] Evaluate Warmstart results — worth continuing?
- [ ] Build Conversion Tracker (correlate channels with subscriber growth)
- [ ] First data review: which channel is producing subscribers?
- [ ] If Substack engagement is showing results: build Daily Digest Agent
- [ ] If not: reallocate time to higher-performing channels
- [ ] Begin proposing cross-recommendations to warm relationships

### Week 9-12 (June — aligns with mid-year checkpoint)
**Theme: Assess and publish**
- [ ] Full system assessment with 60-90 days of data
- [ ] Which funnel is working? Where should you invest more?
- [ ] Write the Substack article about the system and what you learned
- [ ] Share Neighborhood Mapper as a portfolio project on LinkedIn
- [ ] Decision: continue investing in Substack-native growth or double down on LinkedIn + outreach?

---

## Decision Points

**After Warmstart trial (Week 2-3):**
Does personalized 1:1 outreach convert at a meaningfully higher rate than passive LinkedIn posting? If yes, invest more time here. If no, the bottleneck is elsewhere.

**After 30 days of Substack engagement (Week 4-5):**
Are you seeing any signal — profile views, follows, subscriber growth — from Substack-native activity? If yes, continue and build supporting tools. If no, the audience may not be there and you should redirect that 15 min/day.

**After 60-90 days (June mid-year checkpoint):**
Full assessment. Which channels produce subscribers? What's the conversion rate? Is the system worth maintaining, or should you simplify?

---

## What Success Looks Like

**Minimum viable outcome (90 days):**
- 100+ subscribers (from ~26 today)
- Clear data on which channels convert
- One portfolio-quality build (Neighborhood Mapper)
- One publishable article about the system

**Strong outcome (90 days):**
- 200+ subscribers
- 2-3 cross-recommendations active with aligned writers
- Conversion rate improved to 5%+ from current ~2.6%
- Repeatable per-article distribution checklist that takes <30 min
- Clear understanding of whether Substack-native growth works for your audience

**The real success metric:** A system that makes audience development feel like a structured, completable process rather than an open-ended daily grind — because that's how you sustain it.
