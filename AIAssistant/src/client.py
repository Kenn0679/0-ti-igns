from google import genai

from src.config import GEMINI_API_KEY, validate_config

validate_config()

client = genai.Client(api_key=GEMINI_API_KEY)
