import logging

from src.assistant import ask
from src.citations import format_response_with_citations
from src.store_manager import (
    get_file_search_store_metrics,
    get_or_create_file_search_store,
    log_file_search_store_metrics,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SANITY_CHECK_QUESTION = "How do I add a YouTube video?"


def run_sanity_check(store_name: str) -> None:
    response = ask(SANITY_CHECK_QUESTION, store_name)
    formatted_response = format_response_with_citations(response)

    logger.info("Sanity check question: %s", SANITY_CHECK_QUESTION)
    logger.info("Sanity check response:\n%s", formatted_response)


def check_store(store_name: str) -> None:
    metrics = get_file_search_store_metrics(store_name)
    log_file_search_store_metrics(metrics)

    run_sanity_check(store_name)

    logger.info("Execution summary")
    logger.info("  File search store: %s", store_name)
    logger.info("  Total files embedded: %d", metrics.active_documents)


def main() -> None:
    store_name = get_or_create_file_search_store()
    check_store(store_name)


if __name__ == "__main__":
    main()
