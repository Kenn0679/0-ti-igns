import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SCRAPE_DIR = Path(os.getenv("SCRAPE_DIR", str(PROJECT_ROOT.parent / "Scrape"))).resolve()
MARKDOWN_SOURCE_DIR = (SCRAPE_DIR / "src" / "dist_markdown").resolve()
SYSTEM_PROMPT_PATH = (PROJECT_ROOT / "system_prompt.md").resolve()

# Overridable so a deployment can point this at a mounted volume
# (e.g. /data/manifest.json) that survives across ephemeral job runs.
MANIFEST_PATH = Path(os.getenv("MANIFEST_PATH", str(PROJECT_ROOT / "manifest.json"))).resolve()

# Set RUN_SCRAPER=false to skip the scraping step and only re-sync an
# already-populated dist_markdown directory (useful for local testing).
RUN_SCRAPER = os.getenv("RUN_SCRAPER", "true").strip().lower() not in ("0", "false", "no")
SCRAPER_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "600"))

FILE_SEARCH_STORE_NAME = "OptiSigns Knowledge Base"
ASSISTANT_NAME = "OptiBot"
GEMINI_MODEL = "gemini-2.5-flash"


def validate_config() -> None:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the .env file")

    if not SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}")
