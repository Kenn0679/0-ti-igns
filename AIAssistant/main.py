import logging

from check_store import check_store
from src.store_manager import get_or_create_file_search_store, upload_markdown_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    store_name = get_or_create_file_search_store()
    upload_markdown_files(store_name)

    check_store(store_name)


if __name__ == "__main__":
    main()
