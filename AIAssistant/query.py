import argparse
import logging

from src.assistant import ask
from src.citations import format_response_with_citations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question against an existing File Search Store")
    parser.add_argument("store_name", help="Resource name, e.g. fileSearchStores/optisigns-knowledge-base-xxxx")
    parser.add_argument("question", help="Question to ask the assistant")
    args = parser.parse_args()

    response = ask(args.question, args.store_name)
    formatted_response = format_response_with_citations(response)

    print(formatted_response)


if __name__ == "__main__":
    main()
