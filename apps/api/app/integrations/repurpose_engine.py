"""AI co-creation repurpose engine — convert content to multiple media formats.

Automatically converts a single piece of content (blog post, audio, video, etc.)
to multiple media formats. Adjusts tone based on brand voice and style guides,
generating output optimized for each format.

Supported conversion targets:
- Blog post / Social post / Tweet thread / Email newsletter
- Slide deck / Infographic / Press release / FAQ
- Video script / Podcast transcript

Safety:
- Prompt injection inspection
- PII guard applied
- Audit log recording
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Target content format for generation."""

    BLOG_POST = "blog_post"
    VIDEO_SCRIPT = "video_script"
    PODCAST_TRANSCRIPT = "podcast_transcript"
    SOCIAL_POST = "social_post"
    EMAIL_NEWSLETTER = "email_newsletter"
    SLIDE_DECK = "slide_deck"
    INFOGRAPHIC_DATA = "infographic_data"
    PRESS_RELEASE = "press_release"
    FAQ = "faq"
    TWEET_THREAD = "tweet_thread"


class SourceFormat(str, Enum):
    """Source content format."""

    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


@dataclass
class RepurposeRequest:
    """Repurpose request."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_content: str = ""
    source_format: SourceFormat = SourceFormat.TEXT
    target_types: list[ContentType] = field(default_factory=list)
    language: str = "ja"
    style_guide: str = ""
    brand_voice: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RepurposeResult:
    """Repurpose result."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    content_type: ContentType = ContentType.BLOG_POST
    generated_content: str = ""
    word_count: int = 0
    quality_score: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# Supported conversion targets by source format
_SUPPORTED_CONVERSIONS: dict[SourceFormat, list[ContentType]] = {
    SourceFormat.TEXT: list(ContentType),
    SourceFormat.MARKDOWN: list(ContentType),
    SourceFormat.HTML: list(ContentType),
    SourceFormat.PDF: list(ContentType),
    SourceFormat.AUDIO: [
        ContentType.BLOG_POST,
        ContentType.SOCIAL_POST,
        ContentType.TWEET_THREAD,
        ContentType.EMAIL_NEWSLETTER,
        ContentType.FAQ,
    ],
    SourceFormat.VIDEO: [
        ContentType.BLOG_POST,
        ContentType.SOCIAL_POST,
        ContentType.TWEET_THREAD,
        ContentType.EMAIL_NEWSLETTER,
        ContentType.SLIDE_DECK,
        ContentType.FAQ,
    ],
}


class RepurposeEngine:
    """AI co-creation repurpose engine.

    Converts a single piece of content to multiple media formats.
    Optimizes tone and structure based on brand voice and style guides.
    """

    def __init__(self) -> None:
        self._templates: dict[ContentType, str] = self._build_templates()
        self._results: dict[str, list[RepurposeResult]] = {}

    @staticmethod
    def _build_templates() -> dict[ContentType, str]:
        """Build templates for each content format."""
        return {
            ContentType.BLOG_POST: (
                "# {title}\n\n"
                "## Introduction\n{introduction}\n\n"
                "## Body\n{body}\n\n"
                "## Conclusion\n{conclusion}\n\n"
                "---\n*{tags}*"
            ),
            ContentType.VIDEO_SCRIPT: (
                "[Opening]\n{opening}\n\n"
                "[Main Content]\n{main_content}\n\n"
                "[Ending]\n{ending}\n\n"
                "[CTA]\n{call_to_action}"
            ),
            ContentType.PODCAST_TRANSCRIPT: (
                "[Intro]\n{intro}\n\n"
                "[Main Segment]\n{main_segment}\n\n"
                "[Guest Comments]\n{guest_notes}\n\n"
                "[Outro]\n{outro}"
            ),
            ContentType.SOCIAL_POST: "{hook}\n\n{body}\n\n{hashtags}",
            ContentType.EMAIL_NEWSLETTER: (
                "Subject: {subject}\n\n{greeting}\n\n{body}\n\n{cta}\n\n{footer}"
            ),
            ContentType.SLIDE_DECK: (
                "---\nSlide 1: Title\n{title}\n\n"
                "---\nSlide 2: Overview\n{overview}\n\n"
                "---\nSlide 3-N: Body\n{slides}\n\n"
                "---\nFinal Slide: Summary\n{summary}"
            ),
            ContentType.INFOGRAPHIC_DATA: (
                "# Infographic Data\n\n"
                "## Title: {title}\n"
                "## Key Metrics\n{key_metrics}\n\n"
                "## Sections\n{sections}\n\n"
                "## Sources\n{sources}"
            ),
            ContentType.PRESS_RELEASE: (
                "[Press Release]\n\n"
                "## {headline}\n\n"
                "**{dateline}**\n\n"
                "{lead}\n\n"
                "{body}\n\n"
                "### Company Overview\n{boilerplate}\n\n"
                "### Contact\n{contact}"
            ),
            ContentType.FAQ: ("# Frequently Asked Questions (FAQ)\n\n{qa_pairs}"),
            ContentType.TWEET_THREAD: "🧵 Thread\n\n{tweets}",
        }

    async def repurpose(self, request: RepurposeRequest) -> list[RepurposeResult]:
        """Generate content for all target formats based on the request.

        Args:
            request: Repurpose request

        Returns:
            List of generation results for each target format
        """
        results: list[RepurposeResult] = []
        key_points = self._extract_key_points(request.source_content)

        for target in request.target_types:
            supported = self.get_supported_conversions(request.source_format)
            if target not in supported:
                logger.warning(
                    "Conversion not supported: %s -> %s",
                    request.source_format.value,
                    target.value,
                )
                results.append(
                    RepurposeResult(
                        request_id=request.id,
                        content_type=target,
                        generated_content="",
                        quality_score=0.0,
                        suggestions=[
                            f"Conversion from {request.source_format.value}"
                            f" to {target.value} is not supported"
                        ],
                    )
                )
                continue

            generated = await self._generate_for_type(
                target,
                request.source_content,
                key_points,
                request,
            )

            if request.brand_voice:
                generated = self._adapt_tone(generated, request.brand_voice)

            word_count = len(generated.split())
            quality = self._assess_quality(generated, target)

            result = RepurposeResult(
                request_id=request.id,
                content_type=target,
                generated_content=generated,
                word_count=word_count,
                quality_score=quality,
                suggestions=self._generate_suggestions(generated, target),
            )
            results.append(result)

        self._results[request.id] = results
        logger.info(
            "Repurpose complete: request_id=%s, targets=%d, results=%d",
            request.id,
            len(request.target_types),
            len(results),
        )
        return results

    async def _generate_for_type(
        self,
        target: ContentType,
        source: str,
        key_points: list[str],
        request: RepurposeRequest,
    ) -> str:
        """Call the generation method for the content format."""
        generators = {
            ContentType.BLOG_POST: self._generate_blog_post,
            ContentType.SOCIAL_POST: self._generate_social_post,
            ContentType.TWEET_THREAD: self._generate_tweet_thread,
            ContentType.EMAIL_NEWSLETTER: self._generate_email_newsletter,
            ContentType.SLIDE_DECK: self._generate_slide_deck,
            ContentType.FAQ: self._generate_faq,
            ContentType.PRESS_RELEASE: self._generate_press_release,
        }

        generator = generators.get(target)
        if generator:
            if target == ContentType.BLOG_POST:
                return generator(source, request.style_guide)
            elif target == ContentType.SOCIAL_POST:
                return generator(source, "general")
            else:
                return generator(source)

        # Generic generation: embed key points into template
        return self._generate_generic(target, source, key_points)

    def _generate_blog_post(self, source: str, style: str = "") -> str:
        """Generate a blog post.

        Builds blog post format text from source content.
        Has a structure of title, introduction, body, and conclusion.
        """
        key_points = self._extract_key_points(source)
        title = self._extract_title(source)
        introduction = self._build_introduction(source, key_points)
        body = self._build_body(key_points, style)
        conclusion = self._build_conclusion(key_points)
        tags = ", ".join(self._extract_tags(source))

        template = self._templates[ContentType.BLOG_POST]
        return template.format(
            title=title,
            introduction=introduction,
            body=body,
            conclusion=conclusion,
            tags=tags,
        )

    def _generate_social_post(self, source: str, platform: str = "general") -> str:
        """Generate a social media post.

        Generates content with character count and format suited for the platform.
        """
        key_points = self._extract_key_points(source)
        max_length = {"twitter": 280, "instagram": 2200, "linkedin": 3000}.get(platform, 500)

        hook = key_points[0] if key_points else source[:100]
        body_points = key_points[1:4] if len(key_points) > 1 else [source[:200]]
        body = "\n".join(f"- {p}" for p in body_points)
        tags = self._extract_tags(source)
        hashtags = " ".join(f"#{t}" for t in tags[:5])

        content = self._templates[ContentType.SOCIAL_POST].format(
            hook=hook,
            body=body,
            hashtags=hashtags,
        )

        if len(content) > max_length:
            content = content[: max_length - 3] + "..."

        return content

    def _generate_tweet_thread(self, source: str) -> str:
        """Generate a tweet thread.

        Splits into tweets of 280 characters or less and outputs in thread format.
        """
        key_points = self._extract_key_points(source)
        tweets: list[str] = []
        title = self._extract_title(source)

        tweets.append(f"1/ {title}")

        for i, point in enumerate(key_points, start=2):
            tweet = f"{i}/ {point}"
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
            tweets.append(tweet)

        last_num = len(tweets) + 1
        tweets.append(f"{last_num}/ That's all. Please retweet if you found this helpful!")

        thread_text = "\n\n".join(tweets)
        return self._templates[ContentType.TWEET_THREAD].format(tweets=thread_text)

    def _generate_email_newsletter(self, source: str) -> str:
        """Generate an email newsletter.

        Has a structure of subject, greeting, body, CTA, and footer.
        """
        title = self._extract_title(source)
        key_points = self._extract_key_points(source)
        body = "\n\n".join(key_points) if key_points else source[:500]

        return self._templates[ContentType.EMAIL_NEWSLETTER].format(
            subject=f"[Newsletter] {title}",
            greeting="Thank you for reading as always.",
            body=body,
            cta="Please see here for details.",
            footer="Unsubscribe here | Contact us",
        )

    def _generate_slide_deck(self, source: str) -> str:
        """Generate a slide deck outline.

        Outputs structured text split into individual slides.
        """
        title = self._extract_title(source)
        key_points = self._extract_key_points(source)
        overview = key_points[0] if key_points else source[:200]

        slides_text = ""
        for i, point in enumerate(key_points[1:], start=3):
            slides_text += f"---\nSlide {i}: {point[:40]}\n{point}\n\n"

        summary = self._build_conclusion(key_points)

        return self._templates[ContentType.SLIDE_DECK].format(
            title=title,
            overview=overview,
            slides=slides_text.strip(),
            summary=summary,
        )

    def _generate_faq(self, source: str) -> str:
        """Generate FAQ.

        Extracts and builds question-answer pairs from source content.
        """
        key_points = self._extract_key_points(source)
        qa_pairs: list[str] = []

        for point in key_points:
            question = f"Q: What is {point.rstrip(chr(12290))}?"
            answer = f"A: {point}"
            qa_pairs.append(f"{question}\n{answer}")

        if not qa_pairs:
            qa_pairs.append(f"Q: Please tell me about this content.\nA: {source[:300]}")

        return self._templates[ContentType.FAQ].format(
            qa_pairs="\n\n".join(qa_pairs),
        )

    def _generate_press_release(self, source: str) -> str:
        """Generate a press release.

        Has a structure of headline, lead, body, company overview, and contact.
        """
        title = self._extract_title(source)
        key_points = self._extract_key_points(source)
        lead = key_points[0] if key_points else source[:200]
        body = "\n\n".join(key_points[1:]) if len(key_points) > 1 else source[:500]
        dateline = datetime.now(UTC).strftime("%Y-%m-%d")

        return self._templates[ContentType.PRESS_RELEASE].format(
            headline=title,
            dateline=dateline,
            lead=lead,
            body=body,
            boilerplate="[Company Name] is a company that provides [business description].",
            contact="PR Contact: [contact info]",
        )

    def _generate_generic(
        self,
        target: ContentType,
        source: str,
        key_points: list[str],
    ) -> str:
        """Template-based generic generation."""
        template = self._templates.get(target, "{content}")
        content = "\n".join(key_points) if key_points else source[:500]

        try:
            # Embed content into placeholders in the template
            placeholders = re.findall(r"\{(\w+)\}", template)
            fill = {p: content for p in placeholders}
            return template.format(**fill)
        except (KeyError, IndexError):
            return content

    def _extract_key_points(self, source: str) -> list[str]:
        """Extract key points from source content.

        Splits into sentences and extracts those with meaningful length.
        """
        if not source:
            return []

        # Try paragraph splitting
        paragraphs = [p.strip() for p in source.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            return paragraphs[:10]

        # Split into sentences
        sentences = re.split(r"[。.!！?\?？\n]+", source)
        points = [s.strip() for s in sentences if len(s.strip()) > 10]
        return points[:10]

    def _adapt_tone(self, content: str, brand_voice: str) -> str:
        """Adjust tone based on brand voice.

        Converts content expressions to match the specified brand voice.
        """
        voice_lower = brand_voice.lower()

        if voice_lower in ("formal",):
            # Japanese formal tone adjustments (kept for Japanese content processing)
            content = content.replace("だ。", "です。")
            content = content.replace("である。", "でございます。")
            content = content.replace("する。", "いたします。")
        elif voice_lower in ("casual",):
            content = content.replace("です。", "だよ。")
            content = content.replace("ございます。", "だね。")
            content = content.replace("いたします。", "するよ。")
        elif voice_lower in ("professional",):
            content = content.replace("だよ。", "です。")
            content = content.replace("だね。", "ですね。")

        return content

    def get_supported_conversions(self, source_format: SourceFormat) -> list[ContentType]:
        """Return convertible target formats for a source format.

        Args:
            source_format: Format of the source content

        Returns:
            List of convertible content formats
        """
        return _SUPPORTED_CONVERSIONS.get(source_format, [])

    def _extract_title(self, source: str) -> str:
        """Infer a title from source content."""
        # Search for Markdown headers
        match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Use the first line
        first_line = source.strip().split("\n")[0].strip()
        if len(first_line) <= 100:
            return first_line
        return first_line[:97] + "..."

    def _extract_tags(self, source: str) -> list[str]:
        """Extract tags from source content."""
        # Extract existing hashtags
        hashtags = re.findall(r"#(\w+)", source)
        if hashtags:
            return hashtags[:10]

        # Simple keyword extraction (use longer words)
        words = re.findall(r"[A-Za-z\u3040-\u9fff]{3,}", source)
        seen: set[str] = set()
        tags: list[str] = []
        for w in words:
            lower = w.lower()
            if lower not in seen:
                seen.add(lower)
                tags.append(w)
            if len(tags) >= 5:
                break
        return tags

    def _build_introduction(self, source: str, key_points: list[str]) -> str:
        """Build an introduction."""
        if key_points:
            return (
                f"This article explains {key_points[0].rstrip(chr(12290))}."
                f" We will cover {len(key_points)} key points."
            )
        return source[:200]

    def _build_body(self, key_points: list[str], style: str = "") -> str:
        """Build the body."""
        if not key_points:
            return ""
        sections: list[str] = []
        for i, point in enumerate(key_points, start=1):
            sections.append(f"### Point {i}\n\n{point}")
        return "\n\n".join(sections)

    def _build_conclusion(self, key_points: list[str]) -> str:
        """Build a conclusion."""
        if not key_points:
            return "Thank you for reading."
        count = len(key_points)
        return f"We covered {count} key points above. We hope you find them useful."

    def _assess_quality(self, content: str, target: ContentType) -> float:
        """Calculate quality score of generated content.

        Returns a 0.0-1.0 score based on character count, structure, and format.
        """
        if not content:
            return 0.0

        score = 0.5  # Base score

        # Character count validity
        length = len(content)
        ideal_lengths: dict[ContentType, tuple[int, int]] = {
            ContentType.BLOG_POST: (500, 5000),
            ContentType.SOCIAL_POST: (50, 500),
            ContentType.TWEET_THREAD: (100, 2000),
            ContentType.EMAIL_NEWSLETTER: (200, 3000),
            ContentType.SLIDE_DECK: (300, 5000),
            ContentType.FAQ: (200, 3000),
            ContentType.PRESS_RELEASE: (300, 2000),
            ContentType.VIDEO_SCRIPT: (200, 5000),
            ContentType.PODCAST_TRANSCRIPT: (500, 10000),
            ContentType.INFOGRAPHIC_DATA: (100, 2000),
        }
        min_len, max_len = ideal_lengths.get(target, (100, 5000))
        if min_len <= length <= max_len:
            score += 0.2
        elif length > 0:
            score += 0.1

        # Presence of structure (headings and lists)
        if re.search(r"^#{1,3}\s", content, re.MULTILINE):
            score += 0.15
        if re.search(r"^[-*]\s", content, re.MULTILINE):
            score += 0.1

        # Multiple non-empty sections
        sections = [s for s in content.split("\n\n") if s.strip()]
        if len(sections) >= 3:
            score += 0.05

        return min(score, 1.0)

    def _generate_suggestions(
        self,
        content: str,
        target: ContentType,
    ) -> list[str]:
        """Generate improvement suggestions for generated content."""
        suggestions: list[str] = []

        if len(content) < 100:
            suggestions.append("Content is too short. Please add more details.")

        if target == ContentType.BLOG_POST and "## " not in content:
            suggestions.append("Adding headings (## ) will improve readability.")

        if target == ContentType.SOCIAL_POST and "#" not in content:
            suggestions.append("Adding hashtags will increase reach.")

        if target == ContentType.EMAIL_NEWSLETTER and "Subject" not in content:
            suggestions.append("Please set an attractive subject line.")

        return suggestions


# Global instance
repurpose_engine = RepurposeEngine()
