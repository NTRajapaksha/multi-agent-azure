from google import genai
from app.config import settings

gemini_client = genai.Client(api_key=settings.gemini_api_key)

GEMINI_MODEL = "models/gemini-flash-latest"
EMBEDDING_MODEL = "gemini-embedding-2"
