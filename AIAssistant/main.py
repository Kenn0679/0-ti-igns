import logging
import sys

from check_store import check_store
from src.config import MANIFEST_PATH, MARKDOWN_SOURCE_DIR, RUN_SCRAPER
from src.delta import ManifestEntry, compute_delta, load_manifest, save_manifest, utc_now_iso
from src.scraper_runner import clean_markdown_output, run_scraper
from src.store_manager import (
    delete_documents,
    find_markdown_files,
    get_or_create_file_search_store,
    upload_document,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline() -> bool:
    """Runs the full scrape -> delta detection -> sync pipeline. Returns True on full success."""

    # Step 1: wipe any stale scrape output, then re-scrape the latest articles into Markdown.
    # Wiping first ensures articles deleted from the source disappear from dist_markdown
    # too, so delta detection can correctly flag them for cleanup in the vector store.
    if RUN_SCRAPER:
        clean_markdown_output(MARKDOWN_SOURCE_DIR)
        run_scraper()
    else:
        logger.info("RUN_SCRAPER is disabled; reusing the existing dist_markdown contents")

    if not MARKDOWN_SOURCE_DIR.exists():
        raise FileNotFoundError(f"Markdown source directory not found after scrape: {MARKDOWN_SOURCE_DIR}")

    current_files = find_markdown_files(MARKDOWN_SOURCE_DIR)
    if not current_files:
        raise FileNotFoundError(f"No markdown files found in {MARKDOWN_SOURCE_DIR}")

    total_scraped = len(current_files)

    store_name = get_or_create_file_search_store()

    # Step 2: detect which files are new, changed, unchanged, or removed since the last run.
    manifest = load_manifest(MANIFEST_PATH)
    delta = compute_delta(current_files, manifest)

    # Step 3: remove stale documents (updated or deleted source files) from the store.
    stale_names = [f.name for f in delta.updated] + delta.deleted
    stale_document_names = [manifest[name].document_name for name in stale_names if name in manifest]

    deleted_ok, deleted_failed = (0, 0)
    if stale_document_names:
        deleted_ok, deleted_failed = delete_documents(stale_document_names)

    # Step 4: upload only the added/updated delta.
    to_upload = delta.added + delta.updated
    failed_uploads: list[str] = []

    for file_path in to_upload:
        try:
            document_name = upload_document(store_name, file_path)
        except RuntimeError as error:
            logger.error("Giving up on %s, continuing with remaining files: %s", file_path.name, error)
            failed_uploads.append(file_path.name)
            continue

        manifest[file_path.name] = ManifestEntry(
            hash=delta.hashes[file_path.name],
            document_name=document_name,
            updated_at=utc_now_iso(),
        )

    for name in delta.deleted:
        manifest.pop(name, None)

    # Step 5: persist the updated manifest state for the next run.
    save_manifest(MANIFEST_PATH, manifest, store_name)

    added_count = len(delta.added) - sum(1 for f in delta.added if f.name in failed_uploads)
    updated_count = len(delta.updated) - sum(1 for f in delta.updated if f.name in failed_uploads)
    skipped_count = len(delta.unchanged)

    logger.info("Job Execution Summary:")
    logger.info("- Total scraped articles: %d", total_scraped)
    logger.info("- Added: %d", added_count)
    logger.info("- Updated: %d", updated_count)
    logger.info("- Skipped: %d", skipped_count)
    logger.info("- Deleted: %d", len(delta.deleted))

    if failed_uploads:
        logger.warning("- Failed to upload: %d (%s)", len(failed_uploads), ", ".join(failed_uploads))
    if deleted_failed:
        logger.warning("- Failed to delete stale documents: %d", deleted_failed)

    check_store(store_name)

    return not failed_uploads and not deleted_failed


def main() -> None:
    try:
        success = run_pipeline()
    except Exception:
        logger.exception("Pipeline execution failed")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
