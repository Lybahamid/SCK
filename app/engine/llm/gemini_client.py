from google import genai

from app.config import settings


_client = None


def _get_client():
    global _client

    if _client is not None:
        return _client

    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set in environment."
        )

    _client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    return _client


def generate_with_gemini(
    prompt: str,
    model_name: str = "gemini-2.5-flash-lite"
) -> str:
    """
    Sends a prompt to Gemini using the new
    google-genai SDK and returns the response text.
    """

    client = _get_client()

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    text = getattr(response, "text", None)

    if not text:
        return ""

    return text.strip()