"""Optional Gemini polish — no-ops cleanly when GEMINI_API_KEY is unset."""

from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


async def polish_feedback(tips: list[str]) -> list[str]:
    """Rephrase templated feedback more naturally via Gemini (optional)."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return tips

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)

        polished: list[str] = []
        for tip in tips:
            prompt = (
                "You are an encouraging English pronunciation coach. "
                "Rephrase the following feedback in one or two friendly, specific sentences. "
                "Keep all technical phonetic advice. Do not add disclaimers.\n\n"
                f"Feedback: {tip}"
            )
            response = model.generate_content(prompt)
            text = response.text.strip() if response.text else tip
            polished.append(text)
        return polished
    except Exception:
        logger.exception("Gemini polish failed; using templates")
        return tips
