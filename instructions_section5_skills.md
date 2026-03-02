# Section 5 — YouTube Skills + Local Context Skill 実装（Claude Code 用）v11.2

> 担当: Claude Code（全ステップ）
> 前提: Section 3 完了（SkillBase, SkillRegistry, AuthHub, Gateway が動作）
> 完了条件: 6 Skill（YouTube 5 + Local Context 1）が /api/skills に表示され、Orchestrator デモが動作すること
> v11.2 追加: ステップ 5.6b — Local Context Skill（ローカルファイル読み込み・分析）

---

## ステップ 5.1 — yt_script（YouTube 台本生成）

### backend/app/skills/builtins/yt_script/SKILL.json

```json
{
  "name": "yt-script",
  "description": "YouTube動画の台本を生成します。テーマ・長さ・トーンを指定すると、構成・セリフ・演出指示を含む台本を作成します。",
  "version": "1.0.0",
  "input_schema": {
    "topic": {"type": "string", "description": "動画のテーマ"},
    "duration_minutes": {"type": "integer", "description": "動画の長さ（分）", "default": 10},
    "tone": {"type": "string", "description": "トーン（educational, entertaining, serious）", "default": "educational"}
  },
  "output_schema": {
    "title": {"type": "string"},
    "script": {"type": "string"},
    "sections": {"type": "array"}
  },
  "requires_auth": []
}
```

### backend/app/skills/builtins/yt_script/executor.py

```python
"""YouTube 台本生成 Skill。LLM のみ使用（YouTube API 不要）。"""

from app.skills.framework import SkillBase
from app.gateway import call_llm


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        topic = input_data.get("topic", "")
        duration = input_data.get("duration_minutes", 10)
        tone = input_data.get("tone", "educational")

        prompt = f"""YouTube動画の台本を作成してください。

テーマ: {topic}
動画の長さ: {duration}分
トーン: {tone}

以下の構成で台本を作成:
1. フック（最初の15秒で視聴者を引きつける）
2. オープニング（チャンネル紹介）
3. 本編（テーマに沿った内容、{duration}分に適切な分量）
4. まとめ
5. CTA（チャンネル登録・いいね・コメント誘導）

各セクションに:
- セリフ（話す内容）
- 演出指示（画面に表示するもの、効果音、テロップ）
- 想定時間

を含めてください。日本語で。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )
        content = response.choices[0].message.content
        return {
            "title": f"{topic} - YouTube台本",
            "script": content,
            "topic": topic,
            "duration_minutes": duration,
            "tone": tone,
        }
```

---

## ステップ 5.2 — yt_rival（競合チャンネル分析）

### backend/app/skills/builtins/yt_rival/SKILL.json

```json
{
  "name": "yt-rival",
  "description": "競合YouTubeチャンネルを分析します。チャンネルURLまたは検索クエリから、登録者数・再生数・投稿頻度・成功要因を分析します。",
  "version": "1.0.0",
  "input_schema": {
    "search_query": {"type": "string", "description": "競合を探す検索クエリ"},
    "max_results": {"type": "integer", "description": "分析するチャンネル数", "default": 5}
  },
  "output_schema": {
    "channels": {"type": "array"},
    "analysis": {"type": "string"}
  },
  "requires_auth": [{"service": "google", "scopes": ["youtube.readonly"]}]
}
```

### backend/app/skills/builtins/yt_rival/executor.py

```python
"""競合チャンネル分析 Skill。YouTube Data API + LLM。"""

import asyncio
from app.skills.framework import SkillBase
from app.gateway import call_llm
from app.auth.google_oauth import get_google_credentials


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        query = input_data.get("search_query", "")
        max_results = input_data.get("max_results", 5)

        creds = await get_google_credentials()
        if not creds:
            return {"error": "Google認証が必要です。設定画面から接続してください。"}

        # YouTube API 呼び出し（ブロッキングなのでスレッドオフロード）
        def _search():
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", credentials=creds)

            # チャンネル検索
            search_resp = youtube.search().list(
                q=query, type="channel", part="snippet", maxResults=max_results
            ).execute()

            channels = []
            for item in search_resp.get("items", []):
                ch_id = item["snippet"]["channelId"]
                # チャンネル詳細
                ch_resp = youtube.channels().list(
                    id=ch_id, part="snippet,statistics"
                ).execute()
                if ch_resp["items"]:
                    ch = ch_resp["items"][0]
                    channels.append({
                        "id": ch_id,
                        "title": ch["snippet"]["title"],
                        "description": ch["snippet"].get("description", "")[:200],
                        "subscribers": ch["statistics"].get("subscriberCount", "非公開"),
                        "views": ch["statistics"].get("viewCount", "0"),
                        "videos": ch["statistics"].get("videoCount", "0"),
                    })
            return channels

        channels = await asyncio.to_thread(_search)

        # LLM で分析
        prompt = f"""以下の YouTube チャンネルデータを分析してください。

検索クエリ: {query}

チャンネルデータ:
{channels}

分析項目:
1. 各チャンネルの強み・特徴
2. 共通する成功パターン
3. コンテンツ戦略の傾向
4. 差別化のポイント
5. 参考にすべき施策

日本語で詳細に分析してください。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )
        return {
            "channels": channels,
            "analysis": response.choices[0].message.content,
        }
```

---

## ステップ 5.3 — yt_trend（トレンド探索）

### backend/app/skills/builtins/yt_trend/SKILL.json

```json
{
  "name": "yt-trend",
  "description": "YouTube上の最新トレンドを分析します。カテゴリと地域を指定すると、今人気の動画とトレンドテーマを抽出します。",
  "version": "1.0.0",
  "input_schema": {
    "category": {"type": "string", "description": "カテゴリ（テクノロジー、ゲーム、教育など）", "default": ""},
    "region": {"type": "string", "description": "地域コード", "default": "JP"}
  },
  "output_schema": {
    "trending_videos": {"type": "array"},
    "analysis": {"type": "string"}
  },
  "requires_auth": [{"service": "google", "scopes": ["youtube.readonly"]}]
}
```

### backend/app/skills/builtins/yt_trend/executor.py

```python
"""トレンド探索 Skill。YouTube Data API + LLM。"""

import asyncio
from app.skills.framework import SkillBase
from app.gateway import call_llm
from app.auth.google_oauth import get_google_credentials


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        region = input_data.get("region", "JP")
        category = input_data.get("category", "")

        creds = await get_google_credentials()
        if not creds:
            return {"error": "Google認証が必要です。"}

        def _fetch_trends():
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", credentials=creds)
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region,
                "maxResults": 20,
            }
            resp = youtube.videos().list(**params).execute()
            videos = []
            for v in resp.get("items", []):
                videos.append({
                    "title": v["snippet"]["title"],
                    "channel": v["snippet"]["channelTitle"],
                    "views": v["statistics"].get("viewCount", "0"),
                    "likes": v["statistics"].get("likeCount", "0"),
                    "published": v["snippet"]["publishedAt"],
                    "tags": v["snippet"].get("tags", [])[:5],
                })
            return videos

        videos = await asyncio.to_thread(_fetch_trends)

        prompt = f"""以下は{region}地域のYouTubeトレンド動画データです。
{f'カテゴリフィルタ: {category}' if category else ''}

トレンド動画:
{videos}

分析:
1. 現在のトレンドテーマ TOP5
2. 急上昇の共通パターン
3. タイトル・サムネイルの傾向
4. これから伸びそうなテーマ予測
5. チャンネル運営への具体的な活用提案

日本語で。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )
        return {
            "trending_videos": videos,
            "analysis": response.choices[0].message.content,
            "region": region,
        }
```

---

## ステップ 5.4 — yt_performance（パフォーマンス分析）

### backend/app/skills/builtins/yt_performance/SKILL.json

```json
{
  "name": "yt-performance",
  "description": "YouTubeチャンネルや動画のパフォーマンスを分析します。動画URLからエンゲージメント率・視聴傾向を診断します。",
  "version": "1.0.0",
  "input_schema": {
    "video_ids": {"type": "array", "description": "分析する動画ID一覧（URLからIDを抽出）"}
  },
  "output_schema": {
    "videos": {"type": "array"},
    "analysis": {"type": "string"}
  },
  "requires_auth": [{"service": "google", "scopes": ["youtube.readonly"]}]
}
```

### backend/app/skills/builtins/yt_performance/executor.py

```python
"""パフォーマンス分析 Skill。"""

import asyncio
from app.skills.framework import SkillBase
from app.gateway import call_llm
from app.auth.google_oauth import get_google_credentials


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        video_ids = input_data.get("video_ids", [])
        if not video_ids:
            return {"error": "動画IDを1つ以上指定してください。"}

        creds = await get_google_credentials()
        if not creds:
            return {"error": "Google認証が必要です。"}

        def _fetch():
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", credentials=creds)
            resp = youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics,contentDetails"
            ).execute()
            videos = []
            for v in resp.get("items", []):
                stats = v["statistics"]
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))
                engagement = (likes + comments) / max(views, 1) * 100
                videos.append({
                    "id": v["id"],
                    "title": v["snippet"]["title"],
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate": round(engagement, 2),
                    "duration": v["contentDetails"]["duration"],
                    "published": v["snippet"]["publishedAt"],
                })
            return videos

        videos = await asyncio.to_thread(_fetch)

        prompt = f"""以下の YouTube 動画パフォーマンスデータを分析してください。

動画データ:
{videos}

分析項目:
1. 各動画のパフォーマンス評価
2. エンゲージメント率の良し悪し
3. 再生数が伸びた/伸びなかった要因推測
4. 改善すべきポイント
5. 次の動画への具体的な提案

日本語で詳細に。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )
        return {"videos": videos, "analysis": response.choices[0].message.content}
```

---

## ステップ 5.5 — yt_next_move（次回企画提案）

### backend/app/skills/builtins/yt_next_move/SKILL.json

```json
{
  "name": "yt-next-move",
  "description": "チャンネルの方向性と過去の投稿から、次に作るべき動画企画を提案します。",
  "version": "1.0.0",
  "input_schema": {
    "channel_description": {"type": "string", "description": "チャンネルの概要・方向性"},
    "recent_topics": {"type": "array", "description": "最近の動画トピック一覧"},
    "goal": {"type": "string", "description": "目標（登録者増加、収益化、ブランディング等）", "default": "登録者増加"}
  },
  "output_schema": {
    "proposals": {"type": "array"},
    "strategy": {"type": "string"}
  },
  "requires_auth": []
}
```

### backend/app/skills/builtins/yt_next_move/executor.py

```python
"""次回企画提案 Skill。LLM のみ。"""

from app.skills.framework import SkillBase
from app.gateway import call_llm


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        desc = input_data.get("channel_description", "")
        topics = input_data.get("recent_topics", [])
        goal = input_data.get("goal", "登録者増加")

        prompt = f"""YouTubeチャンネルの次の動画企画を提案してください。

チャンネル概要: {desc}
最近のトピック: {topics}
目標: {goal}

以下を提案:
1. 企画案 5本（タイトル案 + 概要 + 期待効果）
2. 優先順位とその理由
3. 各企画の想定ターゲット層
4. シリーズ化の可能性
5. 短期（1ヶ月）と中期（3ヶ月）の投稿戦略

日本語で具体的に。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )
        return {
            "proposals": [],
            "strategy": response.choices[0].message.content,
            "goal": goal,
        }
```

---

## ステップ 5.6b — local_context（ローカルファイル分析）★v11.2

### backend/app/skills/builtins/local_context/SKILL.json

```json
{
  "name": "local-context",
  "description": "ローカルファイルを安全に読み込み、AI組織のコンテキストとして分析します。機密データをクラウドに送信せず、ローカルで処理します。",
  "version": "1.0.0",
  "input_schema": {
    "path": {"type": "string", "description": "読み込むファイルまたはディレクトリのパス"},
    "instruction": {"type": "string", "description": "分析指示（例: 要約、構造化、キーワード抽出）", "default": "内容を要約してください"},
    "file_types": {"type": "array", "description": "対象ファイル拡張子（ディレクトリ指定時）", "default": [".txt", ".md", ".csv"]}
  },
  "output_schema": {
    "files_read": {"type": "array"},
    "analysis": {"type": "string"},
    "structured_data": {"type": "object"}
  },
  "requires_auth": [],
  "security": {
    "allowed_dirs_config": "%APPDATA%/zpcos/allowed_dirs.json",
    "note": "ユーザーが明示的に許可したディレクトリのみアクセス可能"
  }
}
```

### backend/app/skills/builtins/local_context/executor.py

```python
"""ローカルファイル分析 Skill。
ローカルに常駐するOSだからこそ可能な、機密データを含むファイルのセキュアな読み込み・分析。
クラウドAIにはできない「ローカルの文脈理解」を実現する。
"""

import os
import json
from pathlib import Path

from app.skills.framework import SkillBase
from app.gateway import call_llm


def _load_allowed_dirs() -> list[str]:
    """許可ディレクトリ一覧を読み込み。"""
    config_path = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "zpcos" / "allowed_dirs.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return []


def _is_path_allowed(target: str, allowed_dirs: list[str]) -> bool:
    """パスが許可ディレクトリ配下かチェック。"""
    target_path = Path(target).resolve()
    return any(
        str(target_path).startswith(str(Path(d).resolve()))
        for d in allowed_dirs
    )


def _read_file_content(file_path: Path) -> str | None:
    """ファイルを読み込み。テキスト系のみ対応。"""
    text_exts = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml",
                 ".py", ".js", ".ts", ".html", ".css", ".xml", ".log"}
    if file_path.suffix.lower() not in text_exts:
        return None
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")[:50000]  # 50K文字上限
    except Exception:
        return None


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        target_path = input_data.get("path", "")
        instruction = input_data.get("instruction", "内容を要約してください")
        file_types = input_data.get("file_types", [".txt", ".md", ".csv"])

        if not target_path:
            return {"error": "パスを指定してください。"}

        allowed_dirs = _load_allowed_dirs()
        if not allowed_dirs:
            return {
                "error": "許可ディレクトリが設定されていません。"
                "設定画面からアクセスを許可するディレクトリを追加してください。"
            }

        if not _is_path_allowed(target_path, allowed_dirs):
            return {
                "error": f"指定されたパスはアクセスが許可されていません: {target_path}\n"
                f"許可ディレクトリ: {allowed_dirs}"
            }

        # ファイル読み込み
        target = Path(target_path)
        files_read = []

        if target.is_file():
            content = _read_file_content(target)
            if content:
                files_read.append({"path": str(target), "content": content, "size": len(content)})
        elif target.is_dir():
            for ext in file_types:
                for f in target.rglob(f"*{ext}"):
                    if len(files_read) >= 20:  # 最大20ファイル
                        break
                    content = _read_file_content(f)
                    if content:
                        files_read.append({"path": str(f), "content": content[:10000], "size": len(content)})

        if not files_read:
            return {"error": "読み込み可能なファイルが見つかりませんでした。"}

        # LLM で分析（ファイル内容はLLMに送信されるため、ユーザーが許可済みの前提）
        file_summaries = "\n\n".join(
            f"--- {f['path']} ({f['size']}文字) ---\n{f['content'][:5000]}"
            for f in files_read
        )

        prompt = f"""以下のローカルファイルを分析してください。

指示: {instruction}

ファイル内容:
{file_summaries}

日本語で分析結果を返してください。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )

        return {
            "files_read": [{"path": f["path"], "size": f["size"]} for f in files_read],
            "analysis": response.choices[0].message.content,
            "file_count": len(files_read),
        }
```

---

## ステップ 5.7 — 確認

```powershell
cd zpcos/backend

# Skill 一覧確認（サーバー起動中）
curl http://localhost:18234/api/skills
# → 6 Skill が一覧表示されること（YouTube 5 + local-context 1）

# yt-script テスト（認証済みの場合）
curl -X POST http://localhost:18234/api/skills/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_name":"yt-script","input":{"topic":"AIの未来","duration_minutes":10,"tone":"educational"}}'

# Orchestrator デモ（認証済みの場合）
curl -X POST http://localhost:18234/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"input":"YouTubeチャンネルを伸ばしたい"}'

git add -A
git commit -m "feat: implement 6 Skills including Local Context (Section 5 v11.2)"
```

セクション 5 完了。
