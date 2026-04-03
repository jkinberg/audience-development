"""
Day 0 Validation: Test substack_api for Content Pipeline viability.

Questions to answer:
1. Can Newsletter.get_posts() pull recent posts with enough content to score?
2. How much post content is available without auth? (need text for quote extraction)
3. Can we batch-pull from multiple publications without rate limiting?
4. Does get_recommendations() return useful data?
5. Does search_posts() work with our topic keywords?
"""

import json
import time
from substack_api import Newsletter, Post

# --- Test 1: Pull posts from a known Tier 1 publication ---
print("=" * 60)
print("TEST 1: Pull posts from a single publication (Evan Shapiro)")
print("=" * 60)

try:
    newsletter = Newsletter("https://eshap.substack.com")
    posts = newsletter.get_posts(sorting="new", limit=3)
    print(f"Posts returned: {len(posts)}")
    print(f"Post type: {type(posts[0])}")
    print()

    for i, post in enumerate(posts[:3]):
        print(f"--- Post {i+1} ---")
        # Check what attributes are available directly
        print(f"Attributes: {[a for a in dir(post) if not a.startswith('_')]}")

        # Get metadata
        meta = post.get_metadata()
        print(f"\nMetadata keys: {list(meta.keys())}")
        print(f"Title: {meta.get('title', 'N/A')}")
        print(f"Subtitle: {meta.get('subtitle', 'N/A')}")
        print(f"Date: {meta.get('post_date', meta.get('published_at', 'N/A'))}")
        print(f"Slug: {meta.get('slug', 'N/A')}")
        print(f"Word count: {meta.get('word_count', 'N/A')}")
        print(f"Reactions: {meta.get('reactions', meta.get('reaction_count', 'N/A'))}")
        print(f"Comments: {meta.get('comment_count', 'N/A')}")

        # Get content
        content = post.get_content()
        if content:
            print(f"\nContent length: {len(content)} chars")
            print(f"Content type: {type(content)}")
            print(f"First 500 chars:\n{content[:500]}")
        else:
            print("\nContent: None (not available)")

        print()

        # Dump full metadata for first post to see all fields
        if i == 0:
            print("FULL METADATA (first post):")
            print(json.dumps(meta, indent=2, default=str)[:3000])
            print()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# --- Test 2: Test get_recommendations ---
print("\n" + "=" * 60)
print("TEST 2: Get recommendations from Evan Shapiro")
print("=" * 60)

try:
    recs = newsletter.get_recommendations()
    print(f"Recommendations returned: {len(recs)}")
    for i, rec in enumerate(recs[:10]):
        print(f"  {i+1}. {rec}")
        if hasattr(rec, 'get_metadata'):
            try:
                rmeta = rec.get_metadata() if callable(getattr(rec, 'get_metadata', None)) else {}
                print(f"     Type: {type(rec)}")
            except:
                pass
    print()
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# --- Test 3: Test search_posts ---
print("\n" + "=" * 60)
print("TEST 3: Search posts with topic keywords")
print("=" * 60)

test_queries = [
    "newsroom technology AI",
    "media product leadership",
    "AI tools journalism",
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    try:
        # search_posts is a class method on Newsletter, let's test
        results = Newsletter.search_posts(Newsletter("https://substack.com"), query, limit=5)
        print(f"  Results: {len(results)}")
        for j, r in enumerate(results[:3]):
            meta = r.get_metadata()
            print(f"  {j+1}. {meta.get('title', 'N/A')}")
            print(f"     Publication: {meta.get('publishedBylines', meta.get('publication', 'N/A'))}")
        time.sleep(1)  # Be polite
    except Exception as e:
        print(f"  ERROR: {e}")

# --- Test 4: Batch pull from multiple publications ---
print("\n" + "=" * 60)
print("TEST 4: Batch pull from 5 publications (rate limit test)")
print("=" * 60)

test_pubs = [
    ("eshap", "Evan Shapiro"),
    ("joulee", "Julie Zhuo"),
    ("timshey", "Tim Shey"),
    ("clairevo", "Claire Vo"),
    ("brianbalfour", "Brian Balfour"),
]

for slug, name in test_pubs:
    start = time.time()
    try:
        nl = Newsletter(f"https://{slug}.substack.com")
        posts = nl.get_posts(sorting="new", limit=3)
        elapsed = time.time() - start
        titles = []
        for p in posts[:3]:
            m = p.get_metadata()
            titles.append(m.get('title', 'N/A'))
        print(f"  {name} ({slug}): {len(posts)} posts in {elapsed:.1f}s")
        for t in titles:
            print(f"    - {t}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  {name} ({slug}): ERROR in {elapsed:.1f}s - {e}")
    time.sleep(0.5)  # Polite delay

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
