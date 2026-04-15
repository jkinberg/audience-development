"""Pydantic models for data flowing between pipeline stages."""

from datetime import datetime
from pydantic import BaseModel, Field


class Post(BaseModel):
    """A post fetched from the Substack archive API (metadata only)."""

    post_id: int
    title: str
    subtitle: str | None = None
    description: str | None = None
    truncated_body_text: str | None = None
    post_date: datetime
    wordcount: int | None = None
    slug: str
    canonical_url: str
    substack_url: str = ""  # Always *.substack.com — for app deep linking
    audience: str = "everyone"

    # Engagement
    reaction_count: int = 0
    reactions: dict[str, int] = Field(default_factory=dict)
    restacks: int = 0
    comment_count: int = 0

    # Author
    author_name: str = ""
    author_handle: str = ""
    author_bio: str = ""

    # Publication
    publication_name: str = ""
    publication_url: str = ""


class Stage1Score(BaseModel):
    """Output from Gemini Flash classification (Stage 1)."""

    theme_fit: int = Field(ge=0, le=5)
    theme_clusters: list[str] = Field(default_factory=list)
    reshare_potential: int = Field(ge=0, le=3)
    creator_value: int = Field(ge=0, le=2)
    total_score: int = Field(ge=0, le=10)
    noise_flag: str | None = None
    one_line_reason: str = ""


class ScoredPost(BaseModel):
    """A post with Stage 1 scoring attached."""

    post: Post
    score: Stage1Score


class EnrichmentResult(BaseModel):
    """Output from Stage 2 enrichment (Sonnet/Pro)."""

    summary: str = ""  # 2-3 sentence summary of the article
    pull_quotes: list[str] = Field(default_factory=list)  # 1-3 quotable passages


class EnrichedPost(BaseModel):
    """A scored post that has been enriched with quotes and angles."""

    post: Post
    score: Stage1Score
    enrichment: EnrichmentResult
    full_text: str = ""  # Stripped HTML content used for enrichment


class DigestEntry(BaseModel):
    """A single entry in the output digest."""

    post: Post
    score: Stage1Score
    enrichment: EnrichmentResult | None = None
    tier: str  # "high_signal" or "worth_a_look"


class DigestRun(BaseModel):
    """Metadata for a single pipeline run."""

    date: str
    post_ids: list[int] = Field(default_factory=list)
    posts_scanned: int = 0
    posts_in_digest: int = 0


class DiscoveredPublication(BaseModel):
    """A publication found via recommendation graph crawling."""

    url: str
    name: str = ""
    author: str = ""
    score: float = 0.0
    recommended_by: list[str] = Field(default_factory=list)
    recent_posts: list[str] = Field(default_factory=list)
    reason: str = ""
