"""
Application Configuration & Environment Settings for Meridian Enterprise Application
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Directory Paths
BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent  # Meridian Enterprise Application root

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Server Config
PORT = int(os.getenv("PORT", "8001"))
HOST = os.getenv("HOST", "0.0.0.0")
PUBLIC_APP_URL = (os.getenv("PUBLIC_APP_URL") or os.getenv("ENTERPRISE_APP_URL") or f"http://localhost:{PORT}").strip().rstrip("/")

# Security & JWT
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Data & Storage Directories
DATA_DIR = BASE_DIR / "data"
SQLITE_DIR = DATA_DIR / "sqlite"
SQLITE_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = SQLITE_DIR / "shopmart.db"

# Database URL with primary data/sqlite location and fallback
if SQLITE_DB_PATH.exists():
    DEFAULT_DB_URL = f"sqlite:///{SQLITE_DB_PATH}"
else:
    DEFAULT_DB_URL = f"sqlite:///{BACKEND_DIR / 'database' / 'shopmart.db'}"

DATABASE_DIR = SQLITE_DIR if SQLITE_DB_PATH.exists() else (BACKEND_DIR / "database")
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Uploads Directory
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Templates Directory
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"
STATIC_DIR.mkdir(exist_ok=True)

# Knowledge Corpus & RAG Paths
KNOWLEDGE_CORPUS_DIR = DATA_DIR / "knowledge_corpus"
VECTOR_INDICES_DIR = DATA_DIR / "vector_indices"
RAG_DIR = BACKEND_DIR / "rag"

# MeshCentral
MESHCENTRAL_URL = os.getenv("MESHCENTRAL_URL", "wss://localhost:443")
MESHCENTRAL_USER = os.getenv("MESHCENTRAL_USER", "admin-sd")
MESHCENTRAL_PASS = os.getenv("MESHCENTRAL_PASS", "admin@SD1")
MESHCTRL_PATH = os.getenv("MESHCTRL_PATH", r"C:\Users\SANDEEPDUBEY\meshcentral\node_modules\meshcentral\meshctrl.js")

# Atlassian Jira
_raw_jira_url = (os.getenv("JIRA_INSTANCE_URL") or os.getenv("JIRA_HOST") or "https://iamsandeep630.atlassian.net").strip().strip('"').strip("'").rstrip("/")
if _raw_jira_url and not _raw_jira_url.startswith("http"):
    _raw_jira_url = f"https://{_raw_jira_url}"
JIRA_INSTANCE_URL = _raw_jira_url
JIRA_EMAIL = (os.getenv("JIRA_EMAIL") or os.getenv("JIRA_USERNAME") or "iamsandeep630@gmail.com").strip().strip('"').strip("'")
JIRA_API_TOKEN = (os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_API_KEY") or "").strip().strip('"').strip("'")
JIRA_PROJECT_KEY = (os.getenv("JIRA_PROJECT_KEY") or "SCRUM").strip().strip('"').strip("'")

# Atlassian Confluence
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL", "https://agnishpaul2002.atlassian.net/wiki")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "agnishpaul2002@gmail.com")
CONFLUENCE_API_KEY = os.getenv("CONFLUENCE_API_KEY", "")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "SELFHELP")

# AWS Bedrock
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_BEDROCK_KB_ID = os.getenv("AWS_BEDROCK_KB_ID", "BAB6KXZLG6")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "meridia-buck")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")

# Confidence Thresholds
CONFIDENCE_THRESHOLD = 0.45

# Admin Catalog Sync Secret
ADMIN_SYNC_KEY = os.getenv("ADMIN_SYNC_KEY", "meridian-admin-sync-secret-2026")

