import logging
import os
import shutil
import subprocess
from pathlib import Path

from src.config import SCRAPE_DIR, SCRAPER_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

SCRAPER_COMMAND = ["pnpm", "run", "migrate"]


def clean_markdown_output(output_dir: Path) -> None:
    """Wipes the scraper's output directory so a stale run never lingers.

    migrate.ts only ever writes/overwrites files for articles it sees in the
    current API response; it never deletes markdown for articles removed
    from the source. Without this, a deleted article's file would stay in
    dist_markdown forever and never surface as "deleted" for cleanup.
    """
    if not output_dir.exists():
        logger.info("No existing markdown output directory to clean at %s", output_dir)
        return

    stale_count = sum(1 for _ in output_dir.glob("*.md"))
    shutil.rmtree(output_dir)
    logger.info("Removed %d stale markdown file(s) from %s before rescraping", stale_count, output_dir)


def run_scraper() -> None:
    pnpm_executable = shutil.which("pnpm") or "pnpm"
    command = [pnpm_executable, *SCRAPER_COMMAND[1:]]

    logger.info("Starting scraper: %s (cwd=%s)", " ".join(command), SCRAPE_DIR)

    try:
        result = subprocess.run(
            command,
            cwd=SCRAPE_DIR,
            shell=(os.name == "nt"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=SCRAPER_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "pnpm executable not found; ensure Node.js and pnpm are installed and on PATH"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"Scraper timed out after {SCRAPER_TIMEOUT_SECONDS} seconds"
        ) from error

    if result.stdout:
        logger.info("Scraper stdout:\n%s", result.stdout.strip())
    if result.stderr:
        logger.warning("Scraper stderr:\n%s", result.stderr.strip())

    if result.returncode != 0:
        raise RuntimeError(f"Scraper process exited with code {result.returncode}")

    logger.info("Scraper completed successfully")
