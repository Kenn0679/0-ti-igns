import logging

from google.genai import types

from src.store_manager import ARTICLE_URL_METADATA_KEY

logger = logging.getLogger(__name__)

MAX_CITATIONS = 3


def _find_article_url(retrieved_context: types.GroundingChunkRetrievedContext) -> str | None:
    for entry in retrieved_context.custom_metadata or []:
        if entry.key == ARTICLE_URL_METADATA_KEY:
            return entry.string_value

    logger.warning("No Article URL metadata on cited source: %s", retrieved_context.title)
    return None


def format_response_with_citations(response: types.GenerateContentResponse) -> str:
    body = (response.text or "").strip()

    candidates = response.candidates or []
    if not candidates:
        return body

    grounding_metadata = candidates[0].grounding_metadata
    if grounding_metadata is None or not grounding_metadata.grounding_chunks:
        return body

    article_urls: list[str] = []

    for chunk in grounding_metadata.grounding_chunks:
        retrieved_context = chunk.retrieved_context
        if retrieved_context is None or not retrieved_context.title:
            continue

        article_url = _find_article_url(retrieved_context)
        if article_url and article_url not in article_urls:
            article_urls.append(article_url)

        if len(article_urls) >= MAX_CITATIONS:
            break

    if article_urls:
        citation_lines = "\n".join(f"Article URL: {url}" for url in article_urls[:MAX_CITATIONS])
        body = f"{body}\n\n{citation_lines}"

    return body
