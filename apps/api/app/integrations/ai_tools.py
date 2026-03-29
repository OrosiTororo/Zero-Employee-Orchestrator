"""AI tool integration — list and manage external tools operable by AI.

In addition to browser assist and media generation, manages various tools
that AI can operate.

Supported tool categories:
1. Code: GitHub, GitLab, Bitbucket, code review
2. Documents: Google Docs, Notion, Confluence, Obsidian
3. Communication: Slack, Discord, LINE, Teams, Email
4. Project management: Jira, Linear, Asana, Trello, ClickUp
5. Design: Figma, Canva (via MCP)
6. Data analysis: Google Sheets, Airtable
7. Cloud: AWS, GCP, Azure (via CLI)
8. Search: Web Search, RAG, Knowledge Base
9. Media generation: image, video, audio (media_generation.py)
10. Browser: Browser Assist, Playwright
11. Knowledge base: Obsidian, Notion, Logseq, Joplin, Roam Research, Anytype
12. CRM: HubSpot, Salesforce
13. Calendar: Google Calendar, Outlook Calendar
14. Cloud storage: Google Drive, Dropbox, OneDrive
15. Automation: n8n, Zapier, Make
16. Social media: Twitter/X, Instagram, TikTok, YouTube, LinkedIn, Threads
17. Video editing: Runway ML, Pika, CapCut, Descript

All tool operations:
- Go through approval gates
- Are recorded in audit logs
- Follow data protection policies
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool category."""

    CODE = "code"
    DOCUMENT = "document"
    COMMUNICATION = "communication"
    PROJECT_MANAGEMENT = "project_management"
    DESIGN = "design"
    DATA = "data"
    CLOUD = "cloud"
    SEARCH = "search"
    MEDIA_GENERATION = "media_generation"
    BROWSER = "browser"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    AI_MODEL = "ai_model"
    KNOWLEDGE_BASE = "knowledge_base"
    CRM = "crm"
    CALENDAR = "calendar"
    CLOUD_STORAGE = "cloud_storage"
    AUTOMATION = "automation"
    PRODUCTIVITY = "productivity"
    SOCIAL_MEDIA = "social_media"
    VIDEO_EDITING = "video_editing"


class ToolStatus(str, Enum):
    """Tool status."""

    AVAILABLE = "available"
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class AIToolDefinition:
    """AI tool definition."""

    id: str
    name: str
    category: ToolCategory
    description: str
    description_en: str
    status: ToolStatus = ToolStatus.NOT_CONFIGURED
    requires_api_key: bool = False
    env_key: str = ""
    requires_approval: bool = True
    capabilities: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


# All tool definitions
_AI_TOOLS: list[AIToolDefinition] = [
    # --- Code ---
    AIToolDefinition(
        id="github",
        name="GitHub",
        category=ToolCategory.CODE,
        description="GitHub repository, issue, and PR operations",
        description_en="GitHub repository, issue, and PR operations",
        requires_api_key=True,
        env_key="GITHUB_TOKEN",
        capabilities=["create_issue", "create_pr", "review_code", "manage_releases"],
    ),
    AIToolDefinition(
        id="gitlab",
        name="GitLab",
        category=ToolCategory.CODE,
        description="GitLab repository and merge request operations",
        description_en="GitLab repository and merge request operations",
        requires_api_key=True,
        env_key="GITLAB_TOKEN",
        capabilities=["create_issue", "create_mr", "review_code"],
    ),
    # --- Documents ---
    AIToolDefinition(
        id="google_docs",
        name="Google Docs",
        category=ToolCategory.DOCUMENT,
        description="Create and edit Google Docs",
        description_en="Create and edit Google Docs",
        requires_api_key=True,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["create_doc", "edit_doc", "share_doc"],
    ),
    AIToolDefinition(
        id="notion",
        name="Notion",
        category=ToolCategory.DOCUMENT,
        description="Notion page and database operations",
        description_en="Notion page and database operations",
        requires_api_key=True,
        env_key="NOTION_API_KEY",
        capabilities=["create_page", "update_page", "query_database"],
    ),
    AIToolDefinition(
        id="obsidian",
        name="Obsidian",
        category=ToolCategory.DOCUMENT,
        description="Bidirectional sync with Obsidian Vault",
        description_en="Bidirectional sync with Obsidian Vault",
        requires_api_key=False,
        capabilities=["import_notes", "export_notes", "link_notes"],
    ),
    # --- Communication ---
    AIToolDefinition(
        id="slack",
        name="Slack",
        category=ToolCategory.COMMUNICATION,
        description="Send and receive Slack messages",
        description_en="Send and receive Slack messages",
        requires_api_key=True,
        env_key="SLACK_BOT_TOKEN",
        requires_approval=True,
        capabilities=["send_message", "read_channel", "manage_threads"],
    ),
    AIToolDefinition(
        id="discord",
        name="Discord",
        category=ToolCategory.COMMUNICATION,
        description="Send and receive Discord messages",
        description_en="Send and receive Discord messages",
        requires_api_key=True,
        env_key="DISCORD_BOT_TOKEN",
        requires_approval=True,
        capabilities=["send_message", "read_channel"],
    ),
    AIToolDefinition(
        id="line",
        name="LINE",
        category=ToolCategory.COMMUNICATION,
        description="Send and receive LINE messages",
        description_en="Send and receive LINE messages",
        requires_api_key=True,
        env_key="LINE_CHANNEL_TOKEN",
        requires_approval=True,
        capabilities=["send_message", "rich_menu"],
    ),
    AIToolDefinition(
        id="email",
        name="Email (SMTP)",
        category=ToolCategory.COMMUNICATION,
        description="Send emails",
        description_en="Send emails via SMTP",
        requires_api_key=True,
        env_key="SMTP_PASSWORD",
        requires_approval=True,
        capabilities=["send_email"],
    ),
    # --- Project management ---
    AIToolDefinition(
        id="jira",
        name="Jira",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="Create and update Jira tickets",
        description_en="Create and update Jira tickets",
        requires_api_key=True,
        env_key="JIRA_API_TOKEN",
        capabilities=["create_issue", "update_issue", "transition_issue"],
    ),
    AIToolDefinition(
        id="linear",
        name="Linear",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="Linear issue operations",
        description_en="Linear issue operations",
        requires_api_key=True,
        env_key="LINEAR_API_KEY",
        capabilities=["create_issue", "update_issue"],
    ),
    # --- Design ---
    AIToolDefinition(
        id="figma",
        name="Figma",
        category=ToolCategory.DESIGN,
        description="Retrieve and analyze Figma designs via MCP",
        description_en="Get and analyze Figma designs via MCP",
        requires_api_key=True,
        env_key="FIGMA_ACCESS_TOKEN",
        capabilities=["get_design", "get_screenshot", "code_connect"],
    ),
    # --- Data ---
    AIToolDefinition(
        id="google_sheets",
        name="Google Sheets",
        category=ToolCategory.DATA,
        description="Read and write Google Sheets",
        description_en="Read and write Google Sheets",
        requires_api_key=True,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_sheet", "write_sheet", "create_sheet"],
    ),
    # --- Cloud ---
    AIToolDefinition(
        id="aws_cli",
        name="AWS CLI",
        category=ToolCategory.CLOUD,
        description="AWS service operations",
        description_en="AWS service operations via CLI",
        requires_api_key=True,
        env_key="AWS_ACCESS_KEY_ID",
        requires_approval=True,
        capabilities=["s3", "lambda", "ec2", "iam"],
    ),
    AIToolDefinition(
        id="gcloud",
        name="Google Cloud CLI",
        category=ToolCategory.CLOUD,
        description="GCP service operations",
        description_en="GCP service operations via CLI",
        requires_api_key=True,
        env_key="GOOGLE_APPLICATION_CREDENTIALS",
        requires_approval=True,
        capabilities=["compute", "storage", "functions"],
    ),
    # --- Search ---
    AIToolDefinition(
        id="web_search",
        name="Web Search",
        category=ToolCategory.SEARCH,
        description="Web search via Google, Bing, DuckDuckGo",
        description_en="Web search via Google, Bing, or DuckDuckGo",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["search", "scrape"],
    ),
    AIToolDefinition(
        id="local_rag",
        name="Local RAG",
        category=ToolCategory.SEARCH,
        description="Local file RAG search",
        description_en="Local file RAG search",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["index", "search", "similarity"],
    ),
    # --- Media generation ---
    AIToolDefinition(
        id="image_generation",
        name="Image Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="Image generation via DALL-E, Stable Diffusion, Flux",
        description_en="Image generation via DALL-E, Stable Diffusion, Flux",
        requires_api_key=True,
        env_key="OPENAI_API_KEY",
        requires_approval=True,
        capabilities=["generate_image", "edit_image", "variation"],
    ),
    AIToolDefinition(
        id="video_generation",
        name="Video Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="Video generation via Runway ML, Pika, Replicate",
        description_en="Video generation via Runway ML, Pika, Replicate",
        requires_api_key=True,
        env_key="RUNWAY_API_KEY",
        requires_approval=True,
        capabilities=["generate_video", "img2video"],
    ),
    AIToolDefinition(
        id="audio_generation",
        name="Audio/TTS Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="Audio/TTS generation via OpenAI TTS, ElevenLabs",
        description_en="Audio/TTS generation via OpenAI TTS, ElevenLabs",
        requires_api_key=True,
        env_key="OPENAI_API_KEY",
        requires_approval=True,
        capabilities=["text_to_speech", "voice_clone"],
    ),
    AIToolDefinition(
        id="music_generation",
        name="Music Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="Music generation via Suno, Udio",
        description_en="Music generation via Suno, Udio",
        requires_api_key=True,
        env_key="SUNO_API_KEY",
        requires_approval=True,
        capabilities=["generate_music", "extend_music"],
    ),
    # --- Browser ---
    AIToolDefinition(
        id="browser_assist",
        name="Browser Assist",
        category=ToolCategory.BROWSER,
        description="Browser screen analysis and operation guidance",
        description_en="Browser screen analysis and operation guidance",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["analyze_screen", "guide_navigation", "diagnose_error"],
    ),
    AIToolDefinition(
        id="playwright",
        name="Playwright (Browser Automation)",
        category=ToolCategory.BROWSER,
        description="Browser automation (scraping and testing)",
        description_en="Browser automation via Playwright",
        requires_api_key=False,
        requires_approval=True,
        capabilities=["navigate", "click", "fill_form", "screenshot", "scrape"],
    ),
    # --- File system ---
    AIToolDefinition(
        id="file_system",
        name="File System",
        category=ToolCategory.FILE_SYSTEM,
        description="File read/write within sandbox",
        description_en="File read/write within sandbox",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["read", "write", "list", "search"],
    ),
    # --- Database ---
    AIToolDefinition(
        id="database",
        name="Database (Read-only)",
        category=ToolCategory.DATABASE,
        description="Read-only database access",
        description_en="Read-only database access",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["query", "search"],
    ),
    # --- Knowledge base ---
    AIToolDefinition(
        id="logseq",
        name="Logseq",
        category=ToolCategory.KNOWLEDGE_BASE,
        description="Sync with Logseq graphs, block-level read/write",
        description_en="Sync with Logseq graphs, block-level read/write",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["read_blocks", "write_blocks", "search", "graph_analysis"],
    ),
    AIToolDefinition(
        id="joplin",
        name="Joplin",
        category=ToolCategory.KNOWLEDGE_BASE,
        description="Joplin note read/write/search",
        description_en="Joplin note read/write/search via REST API",
        requires_api_key=True,
        env_key="JOPLIN_TOKEN",
        requires_approval=False,
        capabilities=["read_notes", "write_notes", "search"],
    ),
    AIToolDefinition(
        id="roam_research",
        name="Roam Research",
        category=ToolCategory.KNOWLEDGE_BASE,
        description="Roam Research graph read/write",
        description_en="Roam Research graph read/write",
        requires_api_key=True,
        env_key="ROAM_API_KEY",
        capabilities=["read_blocks", "write_blocks", "search"],
    ),
    AIToolDefinition(
        id="anytype",
        name="Anytype",
        category=ToolCategory.KNOWLEDGE_BASE,
        description="Read and search Anytype objects",
        description_en="Read and search Anytype objects",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["read_objects", "search"],
    ),
    AIToolDefinition(
        id="confluence",
        name="Confluence",
        category=ToolCategory.DOCUMENT,
        description="Read/write Confluence pages and spaces",
        description_en="Read/write Confluence pages and spaces",
        requires_api_key=True,
        env_key="CONFLUENCE_API_TOKEN",
        capabilities=["read_pages", "write_pages", "search"],
    ),
    # --- CRM ---
    AIToolDefinition(
        id="hubspot",
        name="HubSpot",
        category=ToolCategory.CRM,
        description="HubSpot CRM contacts and deals operations",
        description_en="HubSpot CRM contacts and deals operations",
        requires_api_key=True,
        env_key="HUBSPOT_API_KEY",
        requires_approval=True,
        capabilities=["read_contacts", "create_deal", "search"],
    ),
    AIToolDefinition(
        id="salesforce",
        name="Salesforce",
        category=ToolCategory.CRM,
        description="Salesforce CRM object operations",
        description_en="Salesforce CRM object operations",
        requires_api_key=True,
        env_key="SALESFORCE_CLIENT_ID",
        requires_approval=True,
        capabilities=["read_objects", "create_record", "search"],
    ),
    # --- Calendar ---
    AIToolDefinition(
        id="google_calendar",
        name="Google Calendar",
        category=ToolCategory.CALENDAR,
        description="Google Calendar event operations",
        description_en="Google Calendar event operations",
        requires_api_key=True,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        requires_approval=True,
        capabilities=["read_events", "create_event", "update_event"],
    ),
    AIToolDefinition(
        id="outlook_calendar",
        name="Outlook Calendar",
        category=ToolCategory.CALENDAR,
        description="Outlook Calendar event operations",
        description_en="Outlook Calendar event operations",
        requires_api_key=True,
        env_key="MICROSOFT_CLIENT_ID",
        requires_approval=True,
        capabilities=["read_events", "create_event", "update_event"],
    ),
    # --- Cloud storage ---
    AIToolDefinition(
        id="google_drive",
        name="Google Drive",
        category=ToolCategory.CLOUD_STORAGE,
        description="Google Drive file operations",
        description_en="Google Drive file operations",
        requires_api_key=True,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        requires_approval=True,
        capabilities=["search_files", "download", "upload"],
    ),
    AIToolDefinition(
        id="dropbox",
        name="Dropbox",
        category=ToolCategory.CLOUD_STORAGE,
        description="Dropbox file operations",
        description_en="Dropbox file operations",
        requires_api_key=True,
        env_key="DROPBOX_ACCESS_TOKEN",
        requires_approval=True,
        capabilities=["search_files", "download", "upload"],
    ),
    AIToolDefinition(
        id="onedrive",
        name="OneDrive",
        category=ToolCategory.CLOUD_STORAGE,
        description="OneDrive file operations",
        description_en="OneDrive file operations",
        requires_api_key=True,
        env_key="MICROSOFT_CLIENT_ID",
        requires_approval=True,
        capabilities=["search_files", "download", "upload"],
    ),
    # --- Project management (additional) ---
    AIToolDefinition(
        id="asana",
        name="Asana",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="Asana task and project operations",
        description_en="Asana task and project operations",
        requires_api_key=True,
        env_key="ASANA_ACCESS_TOKEN",
        capabilities=["create_task", "update_task", "search"],
    ),
    AIToolDefinition(
        id="trello",
        name="Trello",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="Trello board and card operations",
        description_en="Trello board and card operations",
        requires_api_key=True,
        env_key="TRELLO_API_KEY",
        capabilities=["create_card", "update_card", "search"],
    ),
    AIToolDefinition(
        id="clickup",
        name="ClickUp",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="ClickUp task operations",
        description_en="ClickUp task operations",
        requires_api_key=True,
        env_key="CLICKUP_API_KEY",
        capabilities=["create_task", "update_task", "search"],
    ),
    # --- Communication (additional) ---
    AIToolDefinition(
        id="teams",
        name="Microsoft Teams",
        category=ToolCategory.COMMUNICATION,
        description="Send/receive Microsoft Teams messages",
        description_en="Send/receive Microsoft Teams messages",
        requires_api_key=True,
        env_key="MICROSOFT_CLIENT_ID",
        requires_approval=True,
        capabilities=["send_message", "read_channel"],
    ),
    # --- Automation ---
    AIToolDefinition(
        id="n8n",
        name="n8n",
        category=ToolCategory.AUTOMATION,
        description="Trigger and manage n8n workflows",
        description_en="Trigger and manage n8n workflows",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["trigger_workflow", "list_workflows"],
    ),
    AIToolDefinition(
        id="zapier",
        name="Zapier",
        category=ToolCategory.AUTOMATION,
        description="Trigger Zapier Zaps",
        description_en="Trigger Zapier Zaps via webhook",
        requires_api_key=False,
        requires_approval=True,
        capabilities=["trigger_zap"],
    ),
    # --- Productivity ---
    AIToolDefinition(
        id="microsoft_365",
        name="Microsoft 365",
        category=ToolCategory.PRODUCTIVITY,
        description="Operate Word, Excel, and PowerPoint",
        description_en="Operate Word, Excel, PowerPoint via Microsoft Graph",
        requires_api_key=True,
        env_key="MICROSOFT_CLIENT_ID",
        requires_approval=True,
        capabilities=["read_docs", "write_docs", "search"],
    ),
    # --- Design (additional) ---
    AIToolDefinition(
        id="canva",
        name="Canva",
        category=ToolCategory.DESIGN,
        description="Retrieve and export Canva designs",
        description_en="Retrieve and export Canva designs",
        requires_api_key=True,
        env_key="CANVA_API_KEY",
        capabilities=["get_designs", "export"],
    ),
    # --- Social media ---
    AIToolDefinition(
        id="twitter_x",
        name="Twitter / X",
        category=ToolCategory.SOCIAL_MEDIA,
        description="Post tweets, manage threads, schedule posts",
        description_en="Post tweets, manage threads, schedule posts on X (formerly Twitter)",
        requires_api_key=True,
        env_key="TWITTER_API_KEY",
        requires_approval=True,
        capabilities=["post_tweet", "schedule_tweet", "read_timeline", "manage_threads"],
    ),
    AIToolDefinition(
        id="instagram",
        name="Instagram",
        category=ToolCategory.SOCIAL_MEDIA,
        description="Post images/reels, manage stories",
        description_en="Post images, reels, stories on Instagram via Graph API",
        requires_api_key=True,
        env_key="INSTAGRAM_ACCESS_TOKEN",
        requires_approval=True,
        capabilities=["post_image", "post_reel", "manage_stories", "schedule_post"],
    ),
    AIToolDefinition(
        id="tiktok",
        name="TikTok",
        category=ToolCategory.SOCIAL_MEDIA,
        description="Post videos, manage content",
        description_en="Post and manage video content on TikTok",
        requires_api_key=True,
        env_key="TIKTOK_ACCESS_TOKEN",
        requires_approval=True,
        capabilities=["post_video", "schedule_video", "get_analytics"],
    ),
    AIToolDefinition(
        id="youtube",
        name="YouTube",
        category=ToolCategory.SOCIAL_MEDIA,
        description="Upload videos, manage channel, schedule posts",
        description_en="Upload videos, manage channel, community posts on YouTube",
        requires_api_key=True,
        env_key="YOUTUBE_API_KEY",
        requires_approval=True,
        capabilities=["upload_video", "manage_playlists", "community_post", "schedule_upload"],
    ),
    AIToolDefinition(
        id="linkedin",
        name="LinkedIn",
        category=ToolCategory.SOCIAL_MEDIA,
        description="Post articles, manage professional content",
        description_en="Post articles and manage professional content on LinkedIn",
        requires_api_key=True,
        env_key="LINKEDIN_ACCESS_TOKEN",
        requires_approval=True,
        capabilities=["post_article", "share_update", "schedule_post"],
    ),
    AIToolDefinition(
        id="threads",
        name="Threads",
        category=ToolCategory.SOCIAL_MEDIA,
        description="Post text and media on Threads",
        description_en="Post text and media on Meta Threads",
        requires_api_key=True,
        env_key="THREADS_ACCESS_TOKEN",
        requires_approval=True,
        capabilities=["post_text", "post_media", "reply"],
    ),
    # --- Video editing ---
    AIToolDefinition(
        id="runway_ml",
        name="Runway ML",
        category=ToolCategory.VIDEO_EDITING,
        description="AI video generation and editing",
        description_en="AI-powered video generation and editing with Runway ML Gen-3",
        requires_api_key=True,
        env_key="RUNWAY_API_KEY",
        capabilities=["generate_video", "edit_video", "extend_video", "image_to_video"],
    ),
    AIToolDefinition(
        id="pika",
        name="Pika",
        category=ToolCategory.VIDEO_EDITING,
        description="AI video generation",
        description_en="AI video generation with Pika",
        requires_api_key=True,
        env_key="PIKA_API_KEY",
        capabilities=["generate_video", "image_to_video"],
    ),
    AIToolDefinition(
        id="capcut",
        name="CapCut",
        category=ToolCategory.VIDEO_EDITING,
        description="Video editing and template generation",
        description_en="Video editing, templates, and effects via CapCut API",
        requires_api_key=True,
        env_key="CAPCUT_API_KEY",
        capabilities=["edit_video", "apply_template", "add_effects"],
    ),
    AIToolDefinition(
        id="descript",
        name="Descript",
        category=ToolCategory.VIDEO_EDITING,
        description="AI video/audio editing with transcription",
        description_en="AI-powered video and audio editing with transcription",
        requires_api_key=True,
        env_key="DESCRIPT_API_KEY",
        capabilities=["edit_video", "transcribe", "remove_filler_words"],
    ),
]


class AIToolRegistry:
    """AI tool registry.

    Manages available tools and checks their status.
    """

    def __init__(self) -> None:
        self._tools: dict[str, AIToolDefinition] = {t.id: t for t in _AI_TOOLS}
        self._disabled_tools: set[str] = set()

    def get_all_tools(self) -> list[AIToolDefinition]:
        """Return all tools."""
        return list(self._tools.values())

    def get_tool(self, tool_id: str) -> AIToolDefinition | None:
        """Get a tool."""
        return self._tools.get(tool_id)

    def get_tools_by_category(self, category: ToolCategory) -> list[AIToolDefinition]:
        """Return tools by category."""
        return [t for t in self._tools.values() if t.category == category]

    def get_available_tools(self) -> list[AIToolDefinition]:
        """Return a list of available (configured) tools."""
        import os

        available = []
        for tool in self._tools.values():
            if tool.id in self._disabled_tools:
                continue
            if tool.requires_api_key:
                if os.environ.get(tool.env_key):
                    tool.status = ToolStatus.CONFIGURED
                    available.append(tool)
                else:
                    tool.status = ToolStatus.NOT_CONFIGURED
            else:
                tool.status = ToolStatus.AVAILABLE
                available.append(tool)
        return available

    def disable_tool(self, tool_id: str) -> bool:
        """Disable a tool."""
        if tool_id in self._tools:
            self._disabled_tools.add(tool_id)
            self._tools[tool_id].status = ToolStatus.DISABLED
            logger.info("AI tool disabled: %s", tool_id)
            return True
        return False

    def enable_tool(self, tool_id: str) -> bool:
        """Enable a tool."""
        self._disabled_tools.discard(tool_id)
        if tool_id in self._tools:
            self._tools[tool_id].status = ToolStatus.NOT_CONFIGURED
            logger.info("AI tool enabled: %s", tool_id)
            return True
        return False

    def get_summary(self) -> dict:
        """Return tool summary."""
        all_tools = self.get_all_tools()
        available = self.get_available_tools()
        return {
            "total": len(all_tools),
            "available": len(available),
            "disabled": len(self._disabled_tools),
            "categories": {cat.value: len(self.get_tools_by_category(cat)) for cat in ToolCategory},
        }


# Global instance
ai_tool_registry = AIToolRegistry()
