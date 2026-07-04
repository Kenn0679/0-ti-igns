import logging

from google.genai import types
from google.genai.errors import APIError

from src.client import client
from src.config import GEMINI_MODEL, SYSTEM_PROMPT_PATH

logger = logging.getLogger(__name__)


def read_system_prompt() -> str:
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError(f"Failed to read system prompt file {SYSTEM_PROMPT_PATH}: {error}") from error


def build_generation_config(store_name: str) -> types.GenerateContentConfig:
    instructions = read_system_prompt()

    return types.GenerateContentConfig(
        system_instruction=instructions,
        tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[store_name]))],
    )


def ask(question: str, store_name: str) -> types.GenerateContentResponse:
    config = build_generation_config(store_name)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=question,
            config=config,
        )
    except APIError as error:
        raise RuntimeError(f"Failed to generate a response for question '{question}': {error}") from error

    logger.info("Generated response using model=%s store=%s", GEMINI_MODEL, store_name)
    return response
