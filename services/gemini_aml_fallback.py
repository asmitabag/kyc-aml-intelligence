import os
from typing import Any

from google import genai

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class GeminiAMLExplanationFallback:
    """Generate evidence-grounded AML explanations; never calculate risk scores."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def explain(self, evidence: dict[str, Any]) -> str | None:
        if self.client is None:
            return None

        prompt = f"""
Explain the following AML model output for a human reviewer.
Use only the supplied evidence. Do not invent facts, infer unsupported
criminal activity, or calculate, modify, or recommend a different risk score.
Clearly distinguish observed evidence from uncertainty.
Keep the explanation concise.

Evidence:
{evidence}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            return text.strip() if text and text.strip() else None
        except Exception:
            return None
