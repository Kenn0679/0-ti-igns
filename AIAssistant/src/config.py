import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MARKDOWN_SOURCE_DIR = (PROJECT_ROOT.parent / "Scrape" / "src" / "dist_markdown").resolve()
SYSTEM_PROMPT_PATH = (PROJECT_ROOT / "system_prompt.md").resolve()

FILE_SEARCH_STORE_NAME = "OptiSigns Knowledge Base"
ASSISTANT_NAME = "OptiBot"
GEMINI_MODEL = "gemini-2.5-flash"


def validate_config() -> None:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the .env file")

    if not MARKDOWN_SOURCE_DIR.exists():
        raise FileNotFoundError(f"Markdown source directory not found: {MARKDOWN_SOURCE_DIR}")

    if not SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}")
