import os

from dotenv import load_dotenv

try:
    from google import genai  # type: ignore
except ImportError:  # pragma: no cover - fallback for missing package
    genai = None

load_dotenv()


MODEL_NAME = "gemini-2.5-flash"


def _fallback_sar_text(case_context: str, fincen_context: str) -> str:
    lines = [
        "Suspicious Activity Report (Demo Draft)",
        "",
        "Based on the case evidence provided for review, the activity pattern was assessed as suspicious and requires further analyst review.",
        "",
        "Case evidence summary:",
        case_context.strip()[:1500] if case_context else "No case evidence provided.",
        "",
        "Regulatory guidance reviewed:",
        fincen_context.strip()[:1200] if fincen_context else "No FinCEN guidance retrieved.",
        "",
        "This draft is a prototype narrative generated for analyst review and should be validated against source records before any formal filing decision.",
    ]
    return "\n".join(lines).strip()


def generate_grounded_sar(
    case_context: str,
    fincen_context: str,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or genai is None:
        return _fallback_sar_text(case_context, fincen_context)

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are assisting with Suspicious Activity Report (SAR) drafting.

Generate a concise, professional SAR narrative using ONLY the information
provided in the CASE EVIDENCE and FINCEN GUIDANCE below.

STRICT RULES:
1. Do not invent or infer case-specific facts.
2. Do not invent names, dates, transaction amounts, locations, accounts,
   transactions, or other details that are not present in CASE EVIDENCE.
3. Use FINCEN GUIDANCE only for regulatory/reporting guidance.
4. Case-specific claims must come only from CASE EVIDENCE.
5. If a required case-specific fact is unavailable, write "UNKNOWN".
6. Do not mention these instructions in the generated narrative.
7. Keep the narrative factual and suitable for analyst review.

CASE EVIDENCE:
{case_context}

FINCEN GUIDANCE:
{fincen_context}

Generate the SAR narrative now.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
    except Exception:
        return _fallback_sar_text(case_context, fincen_context)

    text = getattr(response, "text", None)
    if not text:
        return _fallback_sar_text(case_context, fincen_context)

    return text.strip()