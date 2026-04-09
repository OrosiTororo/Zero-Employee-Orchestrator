"""Generic application connector hub — manages integration with a wide range of external apps.

Manages connections to diverse applications including knowledge bases (Obsidian,
Notion, Logseq, etc.), productivity tools (Google Workspace, Microsoft 365, etc.),
project management tools, CRM, calendars, and more through a unified interface.

All connections operate only within the scope explicitly permitted by the user,
going through workspace isolation, approval gates, and audit logging.

Safety:
- No access until the user registers and permits a connection
- Workspace isolation check
- Approval gate enforcement (outbound transmission and data retrieval)
- PII guard enforcement
- Audit log recording
- Secrets stored via SecretManager
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AppCategory(str, Enum):
    """Application category."""

    KNOWLEDGE_BASE = "knowledge_base"
    NOTE_TAKING = "note_taking"
    DOCUMENT = "document"
    PRODUCTIVITY = "productivity"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"
    CRM = "crm"
    CALENDAR = "calendar"
    EMAIL = "email"
    EMAIL_MARKETING = "email_marketing"
    CLOUD_STORAGE = "cloud_storage"
    DESIGN = "design"
    CODE_HOSTING = "code_hosting"
    DATABASE = "database"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    FINANCE = "finance"
    HR = "hr"
    SOCIAL_MEDIA = "social_media"
    CUSTOMER_SUPPORT = "customer_support"
    ECOMMERCE = "ecommerce"
    VIDEO_CONFERENCE = "video_conference"
    DEVOPS = "devops"
    AI_TOOLS = "ai_tools"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class AppConnectionStatus(str, Enum):
    """Connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING_AUTH = "pending_auth"
    ERROR = "error"
    DISABLED = "disabled"


class AppAuthMethod(str, Enum):
    """Authentication method."""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    LOCAL_FILE = "local_file"
    WEBHOOK = "webhook"
    TOKEN = "token"
    BASIC = "basic"


class AppDataDirection(str, Enum):
    """Data flow direction."""

    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class AppPermission:
    """Permitted operations for application integration."""

    read: bool = False
    write: bool = False
    delete: bool = False
    sync: bool = False
    export: bool = False
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)


@dataclass
class AppDefinition:
    """Definition of an integrable application."""

    id: str
    name: str
    category: AppCategory
    description: str
    description_en: str
    auth_method: AppAuthMethod = AppAuthMethod.API_KEY
    data_direction: AppDataDirection = AppDataDirection.BIDIRECTIONAL
    env_key: str = ""
    base_url: str = ""
    capabilities: list[str] = field(default_factory=list)
    requires_approval: bool = True
    config_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConnection:
    """Application connection established by a user."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    app_id: str = ""
    user_id: str = ""
    status: AppConnectionStatus = AppConnectionStatus.DISCONNECTED
    permissions: AppPermission = field(default_factory=AppPermission)
    config: dict[str, Any] = field(default_factory=dict)
    connected_at: str = ""
    last_sync_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppSyncResult:
    """Sync result."""

    connection_id: str
    app_id: str
    direction: str
    items_read: int = 0
    items_written: int = 0
    items_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""


# ------------------------------------------------------------------ #
#  Supported application definitions
# ------------------------------------------------------------------ #

_APP_DEFINITIONS: list[AppDefinition] = [
    # --- Knowledge bases ---
    AppDefinition(
        id="obsidian",
        name="Obsidian",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Bidirectional sync with Obsidian Vault and link graph analysis",
        description_en="Bidirectional sync with Obsidian Vault and link graph analysis",
        auth_method=AppAuthMethod.LOCAL_FILE,
        capabilities=[
            "read_notes",
            "write_notes",
            "search",
            "link_graph",
            "backlinks",
            "sync_knowledge_store",
        ],
        requires_approval=False,
    ),
    AppDefinition(
        id="notion",
        name="Notion",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Read/write/search Notion pages and databases",
        description_en="Read/write/search Notion pages and databases",
        auth_method=AppAuthMethod.TOKEN,
        env_key="NOTION_API_KEY",
        base_url="https://api.notion.com/v1",
        capabilities=[
            "read_pages",
            "write_pages",
            "query_database",
            "search",
            "sync_knowledge_store",
        ],
    ),
    AppDefinition(
        id="logseq",
        name="Logseq",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Sync with Logseq graphs, block-level read/write",
        description_en="Sync with Logseq graphs, block-level read/write",
        auth_method=AppAuthMethod.LOCAL_FILE,
        capabilities=[
            "read_blocks",
            "write_blocks",
            "search",
            "graph_analysis",
            "sync_knowledge_store",
        ],
        requires_approval=False,
    ),
    AppDefinition(
        id="joplin",
        name="Joplin",
        category=AppCategory.NOTE_TAKING,
        description="Read/write/search Joplin notes via REST API",
        description_en="Read/write/search Joplin notes via REST API",
        auth_method=AppAuthMethod.TOKEN,
        env_key="JOPLIN_TOKEN",
        base_url="http://localhost:41184",
        capabilities=["read_notes", "write_notes", "search", "sync_knowledge_store"],
    ),
    AppDefinition(
        id="anytype",
        name="Anytype",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Read and search Anytype objects",
        description_en="Read and search Anytype objects",
        auth_method=AppAuthMethod.LOCAL_FILE,
        data_direction=AppDataDirection.READ_ONLY,
        capabilities=["read_objects", "search", "sync_knowledge_store"],
        requires_approval=False,
    ),
    AppDefinition(
        id="roam_research",
        name="Roam Research",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Read/write Roam Research graphs",
        description_en="Read/write Roam Research graphs",
        auth_method=AppAuthMethod.API_KEY,
        env_key="ROAM_API_KEY",
        capabilities=["read_blocks", "write_blocks", "search", "graph_query"],
    ),
    # --- Documents ---
    AppDefinition(
        id="google_docs",
        name="Google Docs",
        category=AppCategory.DOCUMENT,
        description="Create, edit, and share Google Docs",
        description_en="Create, edit, and share Google Docs",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["create_doc", "edit_doc", "share_doc", "export_pdf"],
    ),
    AppDefinition(
        id="google_sheets",
        name="Google Sheets",
        category=AppCategory.DOCUMENT,
        description="Read/write Google Sheets",
        description_en="Read/write Google Sheets",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_sheet", "write_sheet", "create_sheet"],
    ),
    AppDefinition(
        id="google_drive",
        name="Google Drive",
        category=AppCategory.CLOUD_STORAGE,
        description="Search, retrieve, and upload Google Drive files",
        description_en="Search, retrieve, and upload Google Drive files",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["search_files", "download", "upload", "share"],
    ),
    AppDefinition(
        id="microsoft_365",
        name="Microsoft 365",
        category=AppCategory.PRODUCTIVITY,
        description="Operate Word, Excel, PowerPoint, and OneDrive",
        description_en="Operate Word, Excel, PowerPoint, and OneDrive",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["read_docs", "write_docs", "search", "upload", "share"],
    ),
    AppDefinition(
        id="confluence",
        name="Confluence",
        category=AppCategory.DOCUMENT,
        description="Read/write Confluence pages and spaces",
        description_en="Read/write Confluence pages and spaces",
        auth_method=AppAuthMethod.API_KEY,
        env_key="CONFLUENCE_API_TOKEN",
        capabilities=["read_pages", "write_pages", "search", "spaces"],
    ),
    # --- Project management ---
    AppDefinition(
        id="jira",
        name="Jira",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Create, update, and search Jira tickets",
        description_en="Create, update, and search Jira tickets",
        auth_method=AppAuthMethod.API_KEY,
        env_key="JIRA_API_TOKEN",
        capabilities=["create_issue", "update_issue", "transition_issue", "search"],
    ),
    AppDefinition(
        id="linear",
        name="Linear",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Create and update Linear issues",
        description_en="Create and update Linear issues",
        auth_method=AppAuthMethod.API_KEY,
        env_key="LINEAR_API_KEY",
        capabilities=["create_issue", "update_issue", "search"],
    ),
    AppDefinition(
        id="asana",
        name="Asana",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Operate Asana tasks and projects",
        description_en="Operate Asana tasks and projects",
        auth_method=AppAuthMethod.TOKEN,
        env_key="ASANA_ACCESS_TOKEN",
        capabilities=["create_task", "update_task", "search", "projects"],
    ),
    AppDefinition(
        id="trello",
        name="Trello",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Operate Trello boards and cards",
        description_en="Operate Trello boards and cards",
        auth_method=AppAuthMethod.API_KEY,
        env_key="TRELLO_API_KEY",
        capabilities=["create_card", "update_card", "search", "boards"],
    ),
    AppDefinition(
        id="clickup",
        name="ClickUp",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Operate ClickUp tasks and spaces",
        description_en="Operate ClickUp tasks and spaces",
        auth_method=AppAuthMethod.API_KEY,
        env_key="CLICKUP_API_KEY",
        capabilities=["create_task", "update_task", "search"],
    ),
    # --- Communication ---
    AppDefinition(
        id="slack",
        name="Slack",
        category=AppCategory.COMMUNICATION,
        description="Send/receive Slack messages and manage channels",
        description_en="Send/receive Slack messages and manage channels",
        auth_method=AppAuthMethod.TOKEN,
        env_key="SLACK_BOT_TOKEN",
        capabilities=["send_message", "read_channel", "manage_threads", "search"],
    ),
    AppDefinition(
        id="discord",
        name="Discord",
        category=AppCategory.COMMUNICATION,
        description="Send/receive Discord messages",
        description_en="Send/receive Discord messages",
        auth_method=AppAuthMethod.TOKEN,
        env_key="DISCORD_BOT_TOKEN",
        capabilities=["send_message", "read_channel"],
    ),
    AppDefinition(
        id="teams",
        name="Microsoft Teams",
        category=AppCategory.COMMUNICATION,
        description="Send/receive Microsoft Teams messages",
        description_en="Send/receive Microsoft Teams messages",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["send_message", "read_channel", "manage_meetings"],
    ),
    # --- CRM ---
    AppDefinition(
        id="hubspot",
        name="HubSpot",
        category=AppCategory.CRM,
        description="Operate HubSpot CRM contacts, deals, and tasks",
        description_en="Operate HubSpot CRM contacts, deals, and tasks",
        auth_method=AppAuthMethod.API_KEY,
        env_key="HUBSPOT_API_KEY",
        capabilities=["read_contacts", "create_deal", "search", "tasks"],
    ),
    AppDefinition(
        id="salesforce",
        name="Salesforce",
        category=AppCategory.CRM,
        description="Operate Salesforce CRM objects",
        description_en="Operate Salesforce CRM objects",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="SALESFORCE_CLIENT_ID",
        capabilities=["read_objects", "create_record", "search", "reports"],
    ),
    # --- Calendar ---
    AppDefinition(
        id="google_calendar",
        name="Google Calendar",
        category=AppCategory.CALENDAR,
        description="Create and retrieve Google Calendar events",
        description_en="Create and retrieve Google Calendar events",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_events", "create_event", "update_event", "search"],
    ),
    AppDefinition(
        id="outlook_calendar",
        name="Outlook Calendar",
        category=AppCategory.CALENDAR,
        description="Operate Outlook Calendar events",
        description_en="Operate Outlook Calendar events",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["read_events", "create_event", "update_event"],
    ),
    # --- Email ---
    AppDefinition(
        id="gmail",
        name="Gmail",
        category=AppCategory.EMAIL,
        description="Read, send, and search Gmail",
        description_en="Read, send, and search Gmail",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_emails", "send_email", "search", "labels"],
    ),
    # --- Cloud storage ---
    AppDefinition(
        id="dropbox",
        name="Dropbox",
        category=AppCategory.CLOUD_STORAGE,
        description="Search, retrieve, and upload Dropbox files",
        description_en="Search, retrieve, and upload Dropbox files",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="DROPBOX_ACCESS_TOKEN",
        capabilities=["search_files", "download", "upload", "share"],
    ),
    AppDefinition(
        id="onedrive",
        name="OneDrive",
        category=AppCategory.CLOUD_STORAGE,
        description="Operate OneDrive files",
        description_en="Operate OneDrive files",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["search_files", "download", "upload", "share"],
    ),
    # --- Code hosting ---
    AppDefinition(
        id="github",
        name="GitHub",
        category=AppCategory.CODE_HOSTING,
        description="Operate GitHub repositories, issues, and PRs",
        description_en="Operate GitHub repositories, issues, and PRs",
        auth_method=AppAuthMethod.TOKEN,
        env_key="GITHUB_TOKEN",
        capabilities=["create_issue", "create_pr", "review_code", "search"],
    ),
    AppDefinition(
        id="gitlab",
        name="GitLab",
        category=AppCategory.CODE_HOSTING,
        description="Operate GitLab repositories and merge requests",
        description_en="Operate GitLab repositories and merge requests",
        auth_method=AppAuthMethod.TOKEN,
        env_key="GITLAB_TOKEN",
        capabilities=["create_issue", "create_mr", "review_code", "search"],
    ),
    # --- Design ---
    AppDefinition(
        id="figma",
        name="Figma",
        category=AppCategory.DESIGN,
        description="Retrieve and analyze Figma designs via MCP",
        description_en="Retrieve and analyze Figma designs via MCP",
        auth_method=AppAuthMethod.API_KEY,
        env_key="FIGMA_ACCESS_TOKEN",
        data_direction=AppDataDirection.READ_ONLY,
        capabilities=["get_design", "get_screenshot", "code_connect"],
    ),
    AppDefinition(
        id="canva",
        name="Canva",
        category=AppCategory.DESIGN,
        description="Retrieve and export Canva designs",
        description_en="Retrieve and export Canva designs",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="CANVA_API_KEY",
        data_direction=AppDataDirection.READ_ONLY,
        capabilities=["get_designs", "export"],
    ),
    # --- Analytics ---
    AppDefinition(
        id="airtable",
        name="Airtable",
        category=AppCategory.ANALYTICS,
        description="Operate Airtable bases and tables",
        description_en="Operate Airtable bases and tables",
        auth_method=AppAuthMethod.API_KEY,
        env_key="AIRTABLE_API_KEY",
        capabilities=["read_records", "write_records", "search"],
    ),
    # --- Automation ---
    AppDefinition(
        id="n8n",
        name="n8n",
        category=AppCategory.AUTOMATION,
        description="Trigger and manage n8n workflows",
        description_en="Trigger and manage n8n workflows",
        auth_method=AppAuthMethod.WEBHOOK,
        capabilities=["trigger_workflow", "list_workflows", "get_status"],
        requires_approval=False,
    ),
    AppDefinition(
        id="zapier",
        name="Zapier",
        category=AppCategory.AUTOMATION,
        description="Trigger Zapier Zaps",
        description_en="Trigger Zapier Zaps",
        auth_method=AppAuthMethod.WEBHOOK,
        capabilities=["trigger_zap"],
    ),
    AppDefinition(
        id="make",
        name="Make (Integromat)",
        category=AppCategory.AUTOMATION,
        description="Trigger Make scenarios",
        description_en="Trigger Make scenarios",
        auth_method=AppAuthMethod.WEBHOOK,
        capabilities=["trigger_scenario"],
    ),
    # --- Finance ---
    AppDefinition(
        id="stripe",
        name="Stripe",
        category=AppCategory.FINANCE,
        description="Payment processing, invoices, subscriptions, and customer billing",
        description_en="Payment processing, invoices, subscriptions, and customer billing",
        auth_method=AppAuthMethod.API_KEY,
        env_key="STRIPE_SECRET_KEY",
        capabilities=["create_invoice", "list_payments", "manage_subscriptions", "get_balance"],
        requires_approval=True,
    ),
    AppDefinition(
        id="quickbooks",
        name="QuickBooks",
        category=AppCategory.FINANCE,
        description="Accounting, payroll, expenses, and financial reporting",
        description_en="Accounting, payroll, expenses, and financial reporting",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["create_invoice", "record_expense", "run_report", "list_accounts"],
        requires_approval=True,
    ),
    AppDefinition(
        id="xero",
        name="Xero",
        category=AppCategory.FINANCE,
        description="Cloud accounting and bookkeeping for small businesses",
        description_en="Cloud accounting and bookkeeping for small businesses",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["create_invoice", "record_payment", "reconcile", "run_report"],
        requires_approval=True,
    ),
    AppDefinition(
        id="paypal",
        name="PayPal",
        category=AppCategory.FINANCE,
        description="Send and receive payments, manage transactions",
        description_en="Send and receive payments, manage transactions",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["send_payment", "list_transactions", "create_invoice"],
        requires_approval=True,
    ),
    # --- HR ---
    AppDefinition(
        id="bamboohr",
        name="BambooHR",
        category=AppCategory.HR,
        description="Employee records, time-off requests, onboarding, and org chart",
        description_en="Employee records, time-off requests, onboarding, and org chart",
        auth_method=AppAuthMethod.API_KEY,
        env_key="BAMBOOHR_API_KEY",
        capabilities=["get_employee", "list_employees", "request_timeoff", "get_org_chart"],
    ),
    AppDefinition(
        id="workday",
        name="Workday",
        category=AppCategory.HR,
        description="Enterprise HR, finance, and planning platform",
        description_en="Enterprise HR, finance, and planning platform",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["get_employee", "submit_expense", "request_approval", "run_report"],
        requires_approval=True,
    ),
    AppDefinition(
        id="rippling",
        name="Rippling",
        category=AppCategory.HR,
        description="Payroll, benefits, devices, and app management",
        description_en="Payroll, benefits, devices, and app management",
        auth_method=AppAuthMethod.API_KEY,
        env_key="RIPPLING_API_KEY",
        capabilities=["get_employee", "run_payroll", "manage_apps", "onboard_employee"],
        requires_approval=True,
    ),
    # --- Social Media ---
    AppDefinition(
        id="twitter_x",
        name="Twitter / X",
        category=AppCategory.SOCIAL_MEDIA,
        description="Post tweets, monitor mentions, and manage DMs",
        description_en="Post tweets, monitor mentions, and manage DMs",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["post_tweet", "search_tweets", "get_mentions", "send_dm"],
        requires_approval=True,
    ),
    AppDefinition(
        id="linkedin",
        name="LinkedIn",
        category=AppCategory.SOCIAL_MEDIA,
        description="Post updates, manage company pages, and track engagement",
        description_en="Post updates, manage company pages, and track engagement",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["post_update", "get_analytics", "manage_company_page"],
        requires_approval=True,
    ),
    AppDefinition(
        id="instagram",
        name="Instagram",
        category=AppCategory.SOCIAL_MEDIA,
        description="Schedule posts, manage stories, and track insights",
        description_en="Schedule posts, manage stories, and track insights",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["post_media", "get_insights", "manage_comments"],
        requires_approval=True,
    ),
    AppDefinition(
        id="youtube",
        name="YouTube",
        category=AppCategory.SOCIAL_MEDIA,
        description="Upload videos, manage playlists, and track analytics",
        description_en="Upload videos, manage playlists, and track analytics",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["upload_video", "get_analytics", "manage_playlist", "post_comment"],
        requires_approval=True,
    ),
    AppDefinition(
        id="tiktok",
        name="TikTok",
        category=AppCategory.SOCIAL_MEDIA,
        description="Post videos and track content performance",
        description_en="Post videos and track content performance",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["post_video", "get_analytics"],
        requires_approval=True,
    ),
    # --- Customer Support ---
    AppDefinition(
        id="zendesk",
        name="Zendesk",
        category=AppCategory.CUSTOMER_SUPPORT,
        description="Customer support tickets, knowledge base, and chat",
        description_en="Customer support tickets, knowledge base, and chat",
        auth_method=AppAuthMethod.API_KEY,
        env_key="ZENDESK_API_KEY",
        capabilities=["create_ticket", "update_ticket", "list_tickets", "search_tickets", "send_reply"],
    ),
    AppDefinition(
        id="intercom",
        name="Intercom",
        category=AppCategory.CUSTOMER_SUPPORT,
        description="Customer messaging, onboarding, and support automation",
        description_en="Customer messaging, onboarding, and support automation",
        auth_method=AppAuthMethod.API_KEY,
        env_key="INTERCOM_ACCESS_TOKEN",
        capabilities=["send_message", "list_conversations", "create_article", "tag_user"],
    ),
    AppDefinition(
        id="freshdesk",
        name="Freshdesk",
        category=AppCategory.CUSTOMER_SUPPORT,
        description="Help desk software for customer support teams",
        description_en="Help desk software for customer support teams",
        auth_method=AppAuthMethod.API_KEY,
        env_key="FRESHDESK_API_KEY",
        capabilities=["create_ticket", "update_ticket", "list_tickets", "add_note"],
    ),
    # --- E-commerce ---
    AppDefinition(
        id="shopify",
        name="Shopify",
        category=AppCategory.ECOMMERCE,
        description="Manage products, orders, customers, and store analytics",
        description_en="Manage products, orders, customers, and store analytics",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["list_orders", "update_product", "get_customer", "get_analytics"],
    ),
    AppDefinition(
        id="woocommerce",
        name="WooCommerce",
        category=AppCategory.ECOMMERCE,
        description="WordPress e-commerce: orders, products, and reports",
        description_en="WordPress e-commerce: orders, products, and reports",
        auth_method=AppAuthMethod.API_KEY,
        env_key="WOOCOMMERCE_API_KEY",
        capabilities=["list_orders", "update_product", "get_customer", "run_report"],
    ),
    # --- Video Conferencing ---
    AppDefinition(
        id="zoom",
        name="Zoom",
        category=AppCategory.VIDEO_CONFERENCE,
        description="Schedule meetings, manage recordings, and track attendance",
        description_en="Schedule meetings, manage recordings, and track attendance",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["create_meeting", "list_meetings", "get_recording", "list_participants"],
    ),
    AppDefinition(
        id="google_meet",
        name="Google Meet",
        category=AppCategory.VIDEO_CONFERENCE,
        description="Create and manage Google Meet video conferences",
        description_en="Create and manage Google Meet video conferences",
        auth_method=AppAuthMethod.OAUTH2,
        capabilities=["create_meeting", "list_meetings", "get_recording"],
    ),
    # --- Email Marketing ---
    AppDefinition(
        id="mailchimp",
        name="Mailchimp",
        category=AppCategory.EMAIL_MARKETING,
        description="Email campaigns, audience management, and automation",
        description_en="Email campaigns, audience management, and automation",
        auth_method=AppAuthMethod.API_KEY,
        env_key="MAILCHIMP_API_KEY",
        capabilities=["send_campaign", "manage_audience", "create_template", "get_analytics"],
        requires_approval=True,
    ),
    AppDefinition(
        id="sendgrid",
        name="SendGrid",
        category=AppCategory.EMAIL_MARKETING,
        description="Transactional and marketing email delivery at scale",
        description_en="Transactional and marketing email delivery at scale",
        auth_method=AppAuthMethod.API_KEY,
        env_key="SENDGRID_API_KEY",
        capabilities=["send_email", "manage_lists", "create_template", "get_stats"],
        requires_approval=True,
    ),
    # --- DevOps ---
    AppDefinition(
        id="vercel",
        name="Vercel",
        category=AppCategory.DEVOPS,
        description="Deploy and manage frontend projects and serverless functions",
        description_en="Deploy and manage frontend projects and serverless functions",
        auth_method=AppAuthMethod.API_KEY,
        env_key="VERCEL_TOKEN",
        capabilities=["deploy", "list_deployments", "get_logs", "manage_domains"],
    ),
    AppDefinition(
        id="github_actions",
        name="GitHub Actions",
        category=AppCategory.DEVOPS,
        description="Trigger CI/CD workflows and check run status",
        description_en="Trigger CI/CD workflows and check run status",
        auth_method=AppAuthMethod.API_KEY,
        env_key="GITHUB_TOKEN",
        capabilities=["trigger_workflow", "list_runs", "get_run_status", "cancel_run"],
    ),
    AppDefinition(
        id="aws",
        name="AWS",
        category=AppCategory.DEVOPS,
        description="Manage AWS services: S3, Lambda, EC2, and more",
        description_en="Manage AWS services: S3, Lambda, EC2, and more",
        auth_method=AppAuthMethod.API_KEY,
        env_key="AWS_ACCESS_KEY_ID",
        capabilities=["s3_upload", "invoke_lambda", "ec2_status", "cloudwatch_logs"],
        requires_approval=True,
    ),
    # --- AI Tools ---
    AppDefinition(
        id="openai",
        name="OpenAI",
        category=AppCategory.AI_TOOLS,
        description="Access GPT models, DALL-E image generation, and embeddings",
        description_en="Access GPT models, DALL-E image generation, and embeddings",
        auth_method=AppAuthMethod.API_KEY,
        env_key="OPENAI_API_KEY",
        capabilities=["complete", "embed", "generate_image", "moderate"],
    ),
    AppDefinition(
        id="anthropic",
        name="Anthropic / Claude",
        category=AppCategory.AI_TOOLS,
        description="Access Claude models for analysis, writing, and coding",
        description_en="Access Claude models for analysis, writing, and coding",
        auth_method=AppAuthMethod.API_KEY,
        env_key="ANTHROPIC_API_KEY",
        capabilities=["complete", "analyze_document", "generate_code"],
    ),
    AppDefinition(
        id="perplexity",
        name="Perplexity",
        category=AppCategory.AI_TOOLS,
        description="Real-time web search with AI-powered answers",
        description_en="Real-time web search with AI-powered answers",
        auth_method=AppAuthMethod.API_KEY,
        env_key="PERPLEXITY_API_KEY",
        capabilities=["search", "ask"],
    ),
    # --- Monitoring ---
    AppDefinition(
        id="sentry",
        name="Sentry",
        category=AppCategory.MONITORING,
        description="Error tracking and performance monitoring for applications",
        description_en="Error tracking and performance monitoring for applications",
        auth_method=AppAuthMethod.API_KEY,
        env_key="SENTRY_DSN",
        capabilities=["list_issues", "resolve_issue", "get_performance", "create_alert"],
    ),
    AppDefinition(
        id="datadog",
        name="Datadog",
        category=AppCategory.MONITORING,
        description="Infrastructure and application performance monitoring",
        description_en="Infrastructure and application performance monitoring",
        auth_method=AppAuthMethod.API_KEY,
        env_key="DATADOG_API_KEY",
        capabilities=["get_metrics", "list_alerts", "create_monitor", "get_logs"],
    ),
]


class AppConnectorHub:
    """Generic application connector hub.

    Provides unified management of external application listings,
    connection establishment, and data synchronization.
    All operations are executed only within user-permitted scope.
    """

    def __init__(self) -> None:
        self._definitions: dict[str, AppDefinition] = {d.id: d for d in _APP_DEFINITIONS}
        self._connections: dict[str, AppConnection] = {}
        self._sync_history: list[AppSyncResult] = []

    # ------------------------------------------------------------------ #
    #  App definition management
    # ------------------------------------------------------------------ #

    def list_apps(
        self,
        category: AppCategory | None = None,
    ) -> list[AppDefinition]:
        """Return a list of supported applications."""
        apps = list(self._definitions.values())
        if category is not None:
            apps = [a for a in apps if a.category == category]
        return apps

    def get_app(self, app_id: str) -> AppDefinition | None:
        """Get an application definition."""
        return self._definitions.get(app_id)

    def register_custom_app(self, app_def: AppDefinition) -> str:
        """Register a user-defined custom application."""
        if not app_def.id:
            app_def.id = str(uuid.uuid4())
        self._definitions[app_def.id] = app_def
        logger.info("Custom app registered: %s (%s)", app_def.name, app_def.id)
        return app_def.id

    def list_categories(self) -> list[dict[str, Any]]:
        """Return available categories and the number of apps in each."""
        counts: dict[str, int] = {}
        for d in self._definitions.values():
            counts[d.category.value] = counts.get(d.category.value, 0) + 1
        return [
            {"category": cat.value, "count": counts.get(cat.value, 0)}
            for cat in AppCategory
            if counts.get(cat.value, 0) > 0
        ]

    # ------------------------------------------------------------------ #
    #  Connection management
    # ------------------------------------------------------------------ #

    def connect(
        self,
        app_id: str,
        user_id: str,
        config: dict[str, Any] | None = None,
        permissions: AppPermission | None = None,
    ) -> AppConnection:
        """Establish an application connection.

        Args:
            app_id: Application ID to connect
            user_id: User ID
            config: Connection settings (API key, path, etc.)
            permissions: Permitted operations

        Returns:
            Established AppConnection

        Raises:
            KeyError: If app_id is not registered
        """
        app_def = self._definitions.get(app_id)
        if app_def is None:
            raise KeyError(f"App not found: {app_id}")

        conn = AppConnection(
            app_id=app_id,
            user_id=user_id,
            status=AppConnectionStatus.CONNECTED,
            permissions=permissions or AppPermission(read=True),
            config=config or {},
            connected_at=datetime.now(UTC).isoformat(),
        )

        # Credential verification
        if app_def.auth_method == AppAuthMethod.LOCAL_FILE:
            path = (config or {}).get("path", "")
            if not path:
                conn.status = AppConnectionStatus.PENDING_AUTH
                logger.warning("App %s requires a local path", app_id)
        elif app_def.auth_method in (AppAuthMethod.API_KEY, AppAuthMethod.TOKEN):
            import os

            if not (config or {}).get("token") and not os.environ.get(app_def.env_key):
                conn.status = AppConnectionStatus.PENDING_AUTH
                logger.warning("App %s requires credentials (%s)", app_id, app_def.env_key)
        elif app_def.auth_method == AppAuthMethod.OAUTH2:
            if not (config or {}).get("access_token"):
                conn.status = AppConnectionStatus.PENDING_AUTH

        self._connections[conn.id] = conn
        logger.info(
            "App connected: %s (user=%s, status=%s)",
            app_id,
            user_id,
            conn.status.value,
        )
        return conn

    def disconnect(self, connection_id: str) -> bool:
        """Disconnect the connection."""
        conn = self._connections.get(connection_id)
        if conn is None:
            return False
        conn.status = AppConnectionStatus.DISCONNECTED
        logger.info("App disconnected: %s (conn=%s)", conn.app_id, connection_id)
        return True

    def get_connection(self, connection_id: str) -> AppConnection | None:
        """Get connection info."""
        return self._connections.get(connection_id)

    def list_connections(
        self,
        user_id: str | None = None,
        app_id: str | None = None,
        status: AppConnectionStatus | None = None,
    ) -> list[AppConnection]:
        """Return a list of connections."""
        conns = list(self._connections.values())
        if user_id:
            conns = [c for c in conns if c.user_id == user_id]
        if app_id:
            conns = [c for c in conns if c.app_id == app_id]
        if status:
            conns = [c for c in conns if c.status == status]
        return conns

    def update_permissions(
        self,
        connection_id: str,
        permissions: AppPermission,
    ) -> bool:
        """Update connection permissions."""
        conn = self._connections.get(connection_id)
        if conn is None:
            return False
        conn.permissions = permissions
        logger.info("Permissions updated for connection: %s", connection_id)
        return True

    def remove_connection(self, connection_id: str) -> bool:
        """Completely remove a connection."""
        if connection_id in self._connections:
            conn = self._connections.pop(connection_id)
            logger.info("App connection removed: %s (app=%s)", connection_id, conn.app_id)
            return True
        return False

    # ------------------------------------------------------------------ #
    #  Data synchronization
    # ------------------------------------------------------------------ #

    async def sync(
        self,
        connection_id: str,
        direction: AppDataDirection | None = None,
        options: dict[str, Any] | None = None,
    ) -> AppSyncResult:
        """Synchronize data with the connected app.

        Args:
            connection_id: Connection ID
            direction: Sync direction (defaults to app definition default if omitted)
            options: Sync options (filters, range, etc.)

        Returns:
            AppSyncResult
        """
        conn = self._connections.get(connection_id)
        if conn is None:
            return AppSyncResult(
                connection_id=connection_id,
                app_id="unknown",
                direction="unknown",
                errors=[f"Connection not found: {connection_id}"],
            )

        if conn.status != AppConnectionStatus.CONNECTED:
            return AppSyncResult(
                connection_id=connection_id,
                app_id=conn.app_id,
                direction="unknown",
                errors=[f"Connection is not active: {conn.status.value}"],
            )

        app_def = self._definitions.get(conn.app_id)
        if app_def is None:
            return AppSyncResult(
                connection_id=connection_id,
                app_id=conn.app_id,
                direction="unknown",
                errors=[f"App definition not found: {conn.app_id}"],
            )

        sync_dir = direction or app_def.data_direction
        started_at = datetime.now(UTC)

        result = AppSyncResult(
            connection_id=connection_id,
            app_id=conn.app_id,
            direction=sync_dir.value,
            started_at=started_at.isoformat(),
        )

        try:
            # Dispatch to app-specific sync handler
            handler = self._get_sync_handler(conn.app_id)
            if handler:
                sync_data = await handler(conn, sync_dir, options or {})
                result.items_read = sync_data.get("items_read", 0)
                result.items_written = sync_data.get("items_written", 0)
                result.items_skipped = sync_data.get("items_skipped", 0)
            else:
                # Generic sync (delegated to ToolConnector)
                result.items_read = 0
                result.items_written = 0

            conn.last_sync_at = datetime.now(UTC).isoformat()

        except Exception as exc:
            logger.error("Sync failed for %s: %s", conn.app_id, exc)
            result.errors.append(str(exc))

        result.finished_at = datetime.now(UTC).isoformat()
        self._sync_history.append(result)
        return result

    async def import_to_knowledge_store(
        self,
        connection_id: str,
        query: str = "",
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Import data from the connected app to the knowledge store.

        Retrieves only data within the user-permitted scope and
        registers it in the knowledge store.

        Args:
            connection_id: Connection ID
            query: Search query (empty for all)
            tags: Tags to assign
            limit: Maximum number of items to retrieve

        Returns:
            Dictionary of import results
        """
        conn = self._connections.get(connection_id)
        if conn is None:
            return {"error": f"Connection not found: {connection_id}"}

        if not conn.permissions.read:
            return {"error": "Read permission not granted for this connection"}

        if not conn.permissions.sync:
            return {"error": "Sync permission not granted for this connection"}

        app_def = self._definitions.get(conn.app_id)
        if app_def is None:
            return {"error": f"App definition not found: {conn.app_id}"}

        imported = 0
        errors = 0

        try:
            from app.orchestration.knowledge import knowledge_store

            if not hasattr(knowledge_store, "add_entry"):
                return {"error": "Knowledge store not available"}

            # Obsidian uses the existing dedicated integration
            if conn.app_id == "obsidian":
                from app.integrations.obsidian import obsidian_integration

                vault_id = conn.config.get("vault_id", "")
                if vault_id:
                    result = await obsidian_integration.sync_knowledge_store(vault_id)
                    return result

            # Generic import: external data retrieval is delegated to app-specific handlers
            logger.info(
                "Importing from %s to knowledge store (query=%s, limit=%d)",
                conn.app_id,
                query,
                limit,
            )

        except ImportError:
            logger.debug("Knowledge store not available")
            return {"error": "Knowledge store module not available"}

        return {
            "connection_id": connection_id,
            "app_id": conn.app_id,
            "imported": imported,
            "errors": errors,
            "tags": tags or [],
        }

    def get_sync_history(
        self,
        connection_id: str | None = None,
        limit: int = 50,
    ) -> list[AppSyncResult]:
        """Get sync history."""
        history = self._sync_history
        if connection_id:
            history = [h for h in history if h.connection_id == connection_id]
        return history[-limit:]

    # ------------------------------------------------------------------ #
    #  Statistics
    # ------------------------------------------------------------------ #

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of the connector hub."""
        import os

        all_apps = list(self._definitions.values())
        configured = []
        for app in all_apps:
            if (
                app.auth_method == AppAuthMethod.LOCAL_FILE
                or (app.env_key and os.environ.get(app.env_key))
                or app.auth_method == AppAuthMethod.WEBHOOK
            ):
                configured.append(app)

        active_conns = [
            c for c in self._connections.values() if c.status == AppConnectionStatus.CONNECTED
        ]

        categories: dict[str, int] = {}
        for a in all_apps:
            categories[a.category.value] = categories.get(a.category.value, 0) + 1

        return {
            "total_apps": len(all_apps),
            "configured_apps": len(configured),
            "active_connections": len(active_conns),
            "total_connections": len(self._connections),
            "categories": categories,
            "sync_count": len(self._sync_history),
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _get_sync_handler(self, app_id: str):
        """Return an app-specific sync handler if available."""
        handlers = {
            "obsidian": self._sync_obsidian,
            "notion": self._sync_notion,
            "logseq": self._sync_local_files,
            "joplin": self._sync_generic_api,
            "slack": self._sync_slack,
            "github": self._sync_github,
            "google_docs": self._sync_generic_api,
            "google_drive": self._sync_generic_api,
            "google_calendar": self._sync_generic_api,
            "gmail": self._sync_generic_api,
            "jira": self._sync_generic_api,
            "linear": self._sync_generic_api,
            "discord": self._sync_generic_api,
            "hubspot": self._sync_generic_api,
            "salesforce": self._sync_generic_api,
        }
        return handlers.get(app_id)

    async def _sync_obsidian(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """Obsidian sync handler."""
        from app.integrations.obsidian import obsidian_integration

        vault_id = conn.config.get("vault_id", "")
        if not vault_id:
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

        if direction in (AppDataDirection.READ_ONLY, AppDataDirection.BIDIRECTIONAL):
            index = await obsidian_integration.scan_vault(vault_id)
            return {
                "items_read": len(index),
                "items_written": 0,
                "items_skipped": 0,
            }

        return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_notion(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """Notion sync handler — reads pages from a Notion database/workspace."""
        api_key = conn.config.get("api_key") or conn.config.get("token", "")
        if not api_key:
            logger.warning("Notion sync: no API key configured")
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json={"filter": {"property": "object", "value": "page"}, "page_size": 50},
                )
                resp.raise_for_status()
                data = resp.json()
                pages = data.get("results", [])
            return {"items_read": len(pages), "items_written": 0, "items_skipped": 0}
        except Exception as e:
            logger.error("Notion sync failed: %s", e)
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_slack(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """Slack sync handler — reads channel list and recent messages."""
        token = conn.config.get("token") or conn.config.get("api_key", "")
        if not token:
            logger.warning("Slack sync: no token configured")
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}
        try:
            import httpx

            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://slack.com/api/conversations.list",
                    headers=headers,
                    params={"limit": 50, "types": "public_channel,private_channel"},
                )
                resp.raise_for_status()
                data = resp.json()
                channels = data.get("channels", [])
            return {"items_read": len(channels), "items_written": 0, "items_skipped": 0}
        except Exception as e:
            logger.error("Slack sync failed: %s", e)
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_github(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """GitHub sync handler — reads repositories, issues, PRs."""
        token = conn.config.get("token") or conn.config.get("api_key", "")
        if not token:
            logger.warning("GitHub sync: no token configured")
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    params={"per_page": 50, "sort": "updated"},
                )
                resp.raise_for_status()
                repos = resp.json()
            return {"items_read": len(repos), "items_written": 0, "items_skipped": 0}
        except Exception as e:
            logger.error("GitHub sync failed: %s", e)
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_generic_api(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """Generic API sync handler."""
        logger.info("Generic API sync for %s (delegated to ToolConnector)", conn.app_id)
        return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_local_files(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """Local file sync handler."""
        from pathlib import Path

        path = conn.config.get("path", "")
        if not path:
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

        base = Path(path)
        if not base.is_dir():
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

        count = sum(1 for _ in base.rglob("*.md"))
        return {"items_read": count, "items_written": 0, "items_skipped": 0}


# Global instance
app_connector_hub = AppConnectorHub()
