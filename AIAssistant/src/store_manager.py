import logging
import time
from dataclasses import dataclass
from pathlib import Path

from google.genai import types
from google.genai.errors import APIError

from src.client import client
from src.config import FILE_SEARCH_STORE_NAME, MARKDOWN_SOURCE_DIR

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3
MAX_UPLOAD_ATTEMPTS = 3
UPLOAD_RETRY_DELAY_SECONDS = 5

# Left as None so the File Search Store's built-in default chunking is used.
# Pass a types.ChunkingConfig here to override chunk size / overlap explicitly.
CHUNKING_CONFIG = None


@dataclass
class FileSearchStoreMetrics:
    store_name: str
    display_name: str
    active_documents: int
    pending_documents: int
    failed_documents: int
    size_bytes: int


def create_file_search_store(display_name: str = FILE_SEARCH_STORE_NAME) -> str:
    try:
        store = client.file_search_stores.create(
            config=types.CreateFileSearchStoreConfig(display_name=display_name)
        )
    except APIError as error:
        raise RuntimeError(f"Failed to create file search store '{display_name}': {error}") from error

    logger.info("File search store created: name=%s display_name=%s", store.name, display_name)
    return store.name


def get_or_create_file_search_store(display_name: str = FILE_SEARCH_STORE_NAME) -> str:
    try:
        for store in client.file_search_stores.list():
            if store.display_name == display_name:
                logger.info("Reusing existing file search store: name=%s display_name=%s", store.name, display_name)
                return store.name
    except APIError as error:
        raise RuntimeError(f"Failed to list file search stores: {error}") from error

    return create_file_search_store(display_name)


def find_markdown_files(source_dir: Path = MARKDOWN_SOURCE_DIR) -> list[Path]:
    return sorted(source_dir.glob("*.md"))


def upload_document(store_name: str, file_path: Path) -> str:
    """Uploads a single file and returns the resource name of the created Document."""
    last_error: Exception | None = None

    for attempt in range(1, MAX_UPLOAD_ATTEMPTS + 1):
        try:
            operation = client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=store_name,
                file=file_path,
                config=types.UploadToFileSearchStoreConfig(
                    display_name=file_path.name,
                    mime_type="text/markdown",
                    chunking_config=CHUNKING_CONFIG,
                ),
            )

            while not operation.done:
                time.sleep(POLL_INTERVAL_SECONDS)
                operation = client.operations.get(operation)

            if operation.error:
                raise RuntimeError(f"Upload operation failed for {file_path.name}: {operation.error}")

            document_name = operation.response.document_name if operation.response else None
            if not document_name:
                raise RuntimeError(f"Upload operation for {file_path.name} completed without a document name")

            logger.info("Uploaded and indexed: %s (document=%s)", file_path.name, document_name)
            return document_name

        except APIError as error:
            last_error = error
            logger.warning(
                "Upload attempt %d/%d failed for %s: %s",
                attempt,
                MAX_UPLOAD_ATTEMPTS,
                file_path.name,
                error,
            )
            if attempt < MAX_UPLOAD_ATTEMPTS:
                time.sleep(UPLOAD_RETRY_DELAY_SECONDS)

    raise RuntimeError(
        f"Failed to upload {file_path.name} to store {store_name} after {MAX_UPLOAD_ATTEMPTS} attempts: {last_error}"
    ) from last_error


def delete_documents(document_names: list[str]) -> tuple[int, int]:
    """Deletes stale Documents from the store. Returns (succeeded, failed) counts."""
    succeeded = 0
    failed = 0

    for document_name in document_names:
        try:
            client.file_search_stores.documents.delete(name=document_name)
            logger.info("Deleted stale document: %s", document_name)
            succeeded += 1
        except APIError as error:
            logger.error("Failed to delete document %s: %s", document_name, error)
            failed += 1

    return succeeded, failed


def get_file_search_store_metrics(store_name: str) -> FileSearchStoreMetrics:
    try:
        store = client.file_search_stores.get(name=store_name)
    except APIError as error:
        raise RuntimeError(f"Failed to retrieve file search store {store_name}: {error}") from error

    return FileSearchStoreMetrics(
        store_name=store.name,
        display_name=store.display_name,
        active_documents=store.active_documents_count or 0,
        pending_documents=store.pending_documents_count or 0,
        failed_documents=store.failed_documents_count or 0,
        size_bytes=store.size_bytes or 0,
    )


def log_file_search_store_metrics(metrics: FileSearchStoreMetrics) -> None:
    logger.info("File search store metrics for '%s' (%s)", metrics.display_name, metrics.store_name)
    logger.info("  Active documents: %d", metrics.active_documents)
    logger.info("  Pending documents: %d", metrics.pending_documents)
    logger.info("  Failed documents: %d", metrics.failed_documents)
    logger.info("  Storage usage (bytes): %d", metrics.size_bytes)
