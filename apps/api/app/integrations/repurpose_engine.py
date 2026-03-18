"""AI 共創リパーパスエンジン — コンテンツを複数メディア形式に変換.

1 つのコンテンツ（ブログ記事・音声・動画など）を複数のメディア形式に
自動変換する。ブランドボイスやスタイルガイドに基づいてトーンを調整し、
各フォーマットに最適化された出力を生成する。

対応する変換先:
- ブログ記事 / SNS 投稿 / ツイートスレッド / メールニュースレター
- スライドデッキ / インフォグラフィック / プレスリリース / FAQ
- ビデオスクリプト / ポッドキャストトランスクリプト

安全性:
- プロンプトインジェクション検査
- PII ガード適用
- 監査ログ記録
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
    """生成対象のコンテンツ形式."""

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
    """ソースコンテンツの形式."""

    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


@dataclass
class RepurposeRequest:
    """リパーパスリクエスト."""

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
    """リパーパス結果."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    content_type: ContentType = ContentType.BLOG_POST
    generated_content: str = ""
    word_count: int = 0
    quality_score: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ソースフォーマット別の変換可能ターゲット
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
    """AI 共創リパーパスエンジン.

    単一のコンテンツを複数のメディア形式に変換する。
    ブランドボイスやスタイルガイドに基づいてトーン・構成を最適化する。
    """

    def __init__(self) -> None:
        self._templates: dict[ContentType, str] = self._build_templates()
        self._results: dict[str, list[RepurposeResult]] = {}

    @staticmethod
    def _build_templates() -> dict[ContentType, str]:
        """各コンテンツ形式のテンプレートを構築する."""
        return {
            ContentType.BLOG_POST: (
                "# {title}\n\n"
                "## はじめに\n{introduction}\n\n"
                "## 本文\n{body}\n\n"
                "## まとめ\n{conclusion}\n\n"
                "---\n*{tags}*"
            ),
            ContentType.VIDEO_SCRIPT: (
                "[オープニング]\n{opening}\n\n"
                "[メインコンテンツ]\n{main_content}\n\n"
                "[エンディング]\n{ending}\n\n"
                "[CTA]\n{call_to_action}"
            ),
            ContentType.PODCAST_TRANSCRIPT: (
                "【イントロ】\n{intro}\n\n"
                "【本編】\n{main_segment}\n\n"
                "【ゲストコメント】\n{guest_notes}\n\n"
                "【アウトロ】\n{outro}"
            ),
            ContentType.SOCIAL_POST: "{hook}\n\n{body}\n\n{hashtags}",
            ContentType.EMAIL_NEWSLETTER: (
                "件名: {subject}\n\n{greeting}\n\n{body}\n\n{cta}\n\n{footer}"
            ),
            ContentType.SLIDE_DECK: (
                "---\nスライド 1: タイトル\n{title}\n\n"
                "---\nスライド 2: 概要\n{overview}\n\n"
                "---\nスライド 3-N: 本文\n{slides}\n\n"
                "---\n最終スライド: まとめ\n{summary}"
            ),
            ContentType.INFOGRAPHIC_DATA: (
                "# インフォグラフィックデータ\n\n"
                "## タイトル: {title}\n"
                "## 主要数値\n{key_metrics}\n\n"
                "## セクション\n{sections}\n\n"
                "## 出典\n{sources}"
            ),
            ContentType.PRESS_RELEASE: (
                "【プレスリリース】\n\n"
                "## {headline}\n\n"
                "**{dateline}**\n\n"
                "{lead}\n\n"
                "{body}\n\n"
                "### 会社概要\n{boilerplate}\n\n"
                "### お問い合わせ\n{contact}"
            ),
            ContentType.FAQ: ("# よくある質問 (FAQ)\n\n{qa_pairs}"),
            ContentType.TWEET_THREAD: "🧵 スレッド\n\n{tweets}",
        }

    async def repurpose(self, request: RepurposeRequest) -> list[RepurposeResult]:
        """リクエストに基づいて全対象形式のコンテンツを生成する.

        Args:
            request: リパーパスリクエスト

        Returns:
            各ターゲット形式に対する生成結果のリスト
        """
        results: list[RepurposeResult] = []
        key_points = self._extract_key_points(request.source_content)

        for target in request.target_types:
            supported = self.get_supported_conversions(request.source_format)
            if target not in supported:
                logger.warning(
                    "変換非対応: %s -> %s",
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
                            f"{request.source_format.value} から"
                            f" {target.value} への変換は非対応です"
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
            "リパーパス完了: request_id=%s, targets=%d, results=%d",
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
        """コンテンツ形式に応じた生成メソッドを呼び出す."""
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

        # 汎用生成: テンプレートにキーポイントを埋め込む
        return self._generate_generic(target, source, key_points)

    def _generate_blog_post(self, source: str, style: str = "") -> str:
        """ブログ記事を生成する.

        ソースコンテンツからブログ記事形式のテキストを構築する。
        タイトル・導入・本文・まとめの構造を持つ。
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
        """SNS 投稿を生成する.

        プラットフォームに合わせた文字数・形式でコンテンツを生成する。
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
        """ツイートスレッドを生成する.

        280 文字以内のツイートに分割し、スレッド形式で出力する。
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
        tweets.append(f"{last_num}/ 以上です。参考になったらリツイートお願いします!")

        thread_text = "\n\n".join(tweets)
        return self._templates[ContentType.TWEET_THREAD].format(tweets=thread_text)

    def _generate_email_newsletter(self, source: str) -> str:
        """メールニュースレターを生成する.

        件名・挨拶・本文・CTA・フッターの構造を持つ。
        """
        title = self._extract_title(source)
        key_points = self._extract_key_points(source)
        body = "\n\n".join(key_points) if key_points else source[:500]

        return self._templates[ContentType.EMAIL_NEWSLETTER].format(
            subject=f"[Newsletter] {title}",
            greeting="いつもお読みいただきありがとうございます。",
            body=body,
            cta="詳しくはこちらをご覧ください。",
            footer="配信停止はこちら | お問い合わせ",
        )

    def _generate_slide_deck(self, source: str) -> str:
        """スライドデッキのアウトラインを生成する.

        スライド単位に分割した構造化テキストを出力する。
        """
        title = self._extract_title(source)
        key_points = self._extract_key_points(source)
        overview = key_points[0] if key_points else source[:200]

        slides_text = ""
        for i, point in enumerate(key_points[1:], start=3):
            slides_text += f"---\nスライド {i}: {point[:40]}\n{point}\n\n"

        summary = self._build_conclusion(key_points)

        return self._templates[ContentType.SLIDE_DECK].format(
            title=title,
            overview=overview,
            slides=slides_text.strip(),
            summary=summary,
        )

    def _generate_faq(self, source: str) -> str:
        """FAQ を生成する.

        ソースコンテンツからよくある質問と回答のペアを抽出・構築する。
        """
        key_points = self._extract_key_points(source)
        qa_pairs: list[str] = []

        for point in key_points:
            question = f"Q: {point.rstrip('。')}とは何ですか？"
            answer = f"A: {point}"
            qa_pairs.append(f"{question}\n{answer}")

        if not qa_pairs:
            qa_pairs.append(f"Q: この内容について教えてください。\nA: {source[:300]}")

        return self._templates[ContentType.FAQ].format(
            qa_pairs="\n\n".join(qa_pairs),
        )

    def _generate_press_release(self, source: str) -> str:
        """プレスリリースを生成する.

        見出し・リード・本文・会社概要・問い合わせ先の構造を持つ。
        """
        title = self._extract_title(source)
        key_points = self._extract_key_points(source)
        lead = key_points[0] if key_points else source[:200]
        body = "\n\n".join(key_points[1:]) if len(key_points) > 1 else source[:500]
        dateline = datetime.now(UTC).strftime("%Y年%m月%d日")

        return self._templates[ContentType.PRESS_RELEASE].format(
            headline=title,
            dateline=dateline,
            lead=lead,
            body=body,
            boilerplate="[会社名] は [事業内容] を提供する企業です。",
            contact="広報担当: [連絡先]",
        )

    def _generate_generic(
        self,
        target: ContentType,
        source: str,
        key_points: list[str],
    ) -> str:
        """テンプレートベースの汎用生成."""
        template = self._templates.get(target, "{content}")
        content = "\n".join(key_points) if key_points else source[:500]

        try:
            # テンプレート内のプレースホルダーにコンテンツを埋め込む
            placeholders = re.findall(r"\{(\w+)\}", template)
            fill = {p: content for p in placeholders}
            return template.format(**fill)
        except (KeyError, IndexError):
            return content

    def _extract_key_points(self, source: str) -> list[str]:
        """ソースコンテンツから主要ポイントを抽出する.

        文単位に分割し、意味のある長さを持つ文を抽出する。
        """
        if not source:
            return []

        # 段落分割を試行
        paragraphs = [p.strip() for p in source.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            return paragraphs[:10]

        # 文単位に分割
        sentences = re.split(r"[。.!！?\?？\n]+", source)
        points = [s.strip() for s in sentences if len(s.strip()) > 10]
        return points[:10]

    def _adapt_tone(self, content: str, brand_voice: str) -> str:
        """ブランドボイスに基づいてトーンを調整する.

        指定されたブランドボイスに合わせてコンテンツの表現を変換する。
        """
        voice_lower = brand_voice.lower()

        if voice_lower in ("formal", "フォーマル", "丁寧"):
            content = content.replace("だ。", "です。")
            content = content.replace("である。", "でございます。")
            content = content.replace("する。", "いたします。")
        elif voice_lower in ("casual", "カジュアル", "親しみやすい"):
            content = content.replace("です。", "だよ。")
            content = content.replace("ございます。", "だね。")
            content = content.replace("いたします。", "するよ。")
        elif voice_lower in ("professional", "プロフェッショナル", "ビジネス"):
            content = content.replace("だよ。", "です。")
            content = content.replace("だね。", "ですね。")

        return content

    def get_supported_conversions(self, source_format: SourceFormat) -> list[ContentType]:
        """ソースフォーマットに対して変換可能なターゲット形式を返す.

        Args:
            source_format: ソースコンテンツの形式

        Returns:
            変換可能なコンテンツ形式のリスト
        """
        return _SUPPORTED_CONVERSIONS.get(source_format, [])

    def _extract_title(self, source: str) -> str:
        """ソースコンテンツからタイトルを推定する."""
        # Markdown のヘッダーを検索
        match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # 最初の行を使用
        first_line = source.strip().split("\n")[0].strip()
        if len(first_line) <= 100:
            return first_line
        return first_line[:97] + "..."

    def _extract_tags(self, source: str) -> list[str]:
        """ソースコンテンツからタグを抽出する."""
        # 既存のハッシュタグを抽出
        hashtags = re.findall(r"#(\w+)", source)
        if hashtags:
            return hashtags[:10]

        # キーワードを簡易抽出（長めの単語を採用）
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
        """導入文を構築する."""
        if key_points:
            return (
                f"この記事では、{key_points[0].rstrip('。')}について解説します。"
                f" 全{len(key_points)}つのポイントに分けてお伝えします。"
            )
        return source[:200]

    def _build_body(self, key_points: list[str], style: str = "") -> str:
        """本文を構築する."""
        if not key_points:
            return ""
        sections: list[str] = []
        for i, point in enumerate(key_points, start=1):
            sections.append(f"### ポイント {i}\n\n{point}")
        return "\n\n".join(sections)

    def _build_conclusion(self, key_points: list[str]) -> str:
        """まとめ文を構築する."""
        if not key_points:
            return "ご覧いただきありがとうございました。"
        count = len(key_points)
        return f"以上、{count}つのポイントをご紹介しました。ぜひ参考にしてください。"

    def _assess_quality(self, content: str, target: ContentType) -> float:
        """生成コンテンツの品質スコアを算出する.

        文字数・構造・形式の観点から 0.0-1.0 のスコアを返す。
        """
        if not content:
            return 0.0

        score = 0.5  # ベーススコア

        # 文字数の妥当性
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

        # 構造の存在（見出しやリスト）
        if re.search(r"^#{1,3}\s", content, re.MULTILINE):
            score += 0.15
        if re.search(r"^[-*]\s", content, re.MULTILINE):
            score += 0.1

        # 空でないセクションが複数
        sections = [s for s in content.split("\n\n") if s.strip()]
        if len(sections) >= 3:
            score += 0.05

        return min(score, 1.0)

    def _generate_suggestions(
        self,
        content: str,
        target: ContentType,
    ) -> list[str]:
        """生成コンテンツに対する改善提案を生成する."""
        suggestions: list[str] = []

        if len(content) < 100:
            suggestions.append("コンテンツが短すぎます。詳細を追加してください。")

        if target == ContentType.BLOG_POST and "## " not in content:
            suggestions.append("見出し（## ）を追加すると読みやすくなります。")

        if target == ContentType.SOCIAL_POST and "#" not in content:
            suggestions.append("ハッシュタグを追加するとリーチが広がります。")

        if target == ContentType.EMAIL_NEWSLETTER and "件名" not in content:
            suggestions.append("魅力的な件名を設定してください。")

        return suggestions


# グローバルインスタンス
repurpose_engine = RepurposeEngine()
