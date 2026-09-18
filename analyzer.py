"""
analyzer.py — "Is This Safe?" message analysis module.

How it works:
  1. Validate the input (not empty, not too long).
  2. Run a fast local heuristic scan using the patterns in warning_signs.py.
  3. Send a structured prompt to the Gemini AI, including what the heuristics found.
  4. Parse the AI response and return a beginner-friendly result.

The AI is used for the nuanced, natural-language part of the analysis.
The heuristic scan is instant, costs nothing, and catches obvious patterns
even if the AI is unavailable.
"""

import json
import re
from dataclasses import dataclass, field

from ai_client import AIClient, AIServiceError, InvalidInputError
from warning_signs import WARNING_SIGNS

# Maximum characters accepted in a single message submission
MAX_INPUT_LENGTH: int = 2000

# The three possible risk verdicts shown to the user
VERDICT_SAFE = "Likely Safe"
VERDICT_CAUTION = "Needs Caution"
VERDICT_SUSPICIOUS = "Suspicious"

# Always shown below the verdict to remind users that AI can be wrong
CONFIDENCE_NOTE = (
    "⚠️ This analysis is a guide only — not a guarantee. "
    "When in doubt, do not click links or share personal information. "
    "Contact the organisation directly using contact details from their official website."
)


@dataclass
class MessageAnalysisResult:
    """
    The result of analysing a suspicious message.

    Attributes:
        verdict:            One of 'Likely Safe', 'Needs Caution', or 'Suspicious'.
        warning_signs_found: Categories of indicators detected in the message.
        explanation:        Plain-English explanation of the findings.
        safe_next_steps:    List of specific actions the user should take.
        confidence_note:    Reminder that AI analysis is not definitive.
    """
    verdict: str
    warning_signs_found: list[str] = field(default_factory=list)
    explanation: str = ""
    safe_next_steps: list[str] = field(default_factory=list)
    confidence_note: str = CONFIDENCE_NOTE


class MessageAnalyzer:
    """
    Analyses a pasted message for phishing and scam indicators.

    Usage:
        client = AIClient()
        analyzer = MessageAnalyzer(client)
        result = analyzer.analyze("Your account has been suspended. Click here.")
    """

    def __init__(self, ai_client: AIClient) -> None:
        self._ai = ai_client

    def analyze(self, text: str) -> MessageAnalysisResult:
        """
        Analyse a message and return a risk assessment.

        Args:
            text: The message the user wants to check.

        Returns:
            A MessageAnalysisResult with verdict, explanation, and next steps.

        Raises:
            InvalidInputError: If the input is empty or too long.
            AIServiceError:    If the AI API call fails.
        """
        self._validate(text)

        # Step 1: Fast local heuristic scan (no API cost)
        heuristic_hits = self._run_heuristic_scan(text)

        # Step 2: Ask the AI for a deeper analysis
        prompt = self._build_prompt(text, heuristic_hits)
        raw_response = self._ai.send_prompt(prompt)

        # Step 3: Parse the AI's structured response
        verdict, explanation, next_steps = self._parse_ai_response(
            raw_response, heuristic_hits
        )

        return MessageAnalysisResult(
            verdict=verdict,
            warning_signs_found=heuristic_hits,
            explanation=explanation,
            safe_next_steps=next_steps,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(text: str) -> None:
        """Raise InvalidInputError for empty or oversized input."""
        if not text or not text.strip():
            raise InvalidInputError("Please paste a message before clicking Analyze.")
        if len(text) > MAX_INPUT_LENGTH:
            raise InvalidInputError(
                f"Message is too long ({len(text)} characters). "
                f"Please limit it to {MAX_INPUT_LENGTH} characters."
            )

    @staticmethod
    def _run_heuristic_scan(text: str) -> list[str]:
        """
        Check the message against known phishing/scam patterns.

        Returns a list of matched category names (e.g. ['Urgency or Pressure']).
        Fast and free — runs locally before any AI call is made.
        """
        text_lower = text.lower()
        hits: list[str] = []
        for sign in WARNING_SIGNS:
            if any(pattern in text_lower for pattern in sign.patterns):
                hits.append(sign.category)
        return hits

    @staticmethod
    def _build_prompt(text: str, heuristic_hits: list[str]) -> str:
        """
        Build the structured prompt sent to Gemini.

        The prompt tells the AI what heuristics already found and asks for
        a JSON response so parsing is reliable.
        """
        hits_summary = (
            ", ".join(heuristic_hits)
            if heuristic_hits
            else "none detected by local scan"
        )

        return f"""You are a cybersecurity awareness assistant helping a beginner check whether a message might be a scam or phishing attempt.

A local scan of the message already detected these warning sign categories: {hits_summary}.

Analyse the message below and respond with ONLY a valid JSON object — no markdown, no code fences, just raw JSON.

The JSON must have exactly these three keys:
- "verdict": one of exactly these three strings: "Likely Safe", "Needs Caution", or "Suspicious"
- "explanation": a 2–4 sentence plain-English explanation of your findings, written for someone with no technical background. Do NOT claim certainty — use phrases like "this message appears to" or "this could be".
- "safe_next_steps": a list of 2–4 short, specific action items the user should take

Message to analyse:
\"\"\"
{text}
\"\"\"

Remember: respond with raw JSON only."""

    @staticmethod
    def _parse_ai_response(
        raw: str, heuristic_hits: list[str]
    ) -> tuple[str, str, list[str]]:
        """
        Parse the AI's JSON response into (verdict, explanation, next_steps).

        Falls back to a safe default if the JSON is malformed, so the app
        never crashes due to an unexpected AI response format.
        """
        # Strip markdown code fences the model sometimes adds despite instructions
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

        try:
            data = json.loads(cleaned)
            verdict = data.get("verdict", VERDICT_CAUTION)
            # Normalise: only accept the three defined verdicts
            if verdict not in (VERDICT_SAFE, VERDICT_CAUTION, VERDICT_SUSPICIOUS):
                verdict = VERDICT_CAUTION
            explanation = str(data.get("explanation", "No explanation provided."))
            next_steps = data.get("safe_next_steps", [])
            if not isinstance(next_steps, list):
                next_steps = [str(next_steps)]
            return verdict, explanation, next_steps

        except (json.JSONDecodeError, AttributeError):
            # Fallback: use heuristic evidence to choose a safe default verdict
            fallback_verdict = VERDICT_CAUTION if heuristic_hits else VERDICT_CAUTION
            fallback_explanation = (
                "The AI was unable to produce a structured analysis. "
                "Based on local scanning, please review the message carefully "
                "before taking any action."
            )
            fallback_steps = [
                "Do not click any links in the message.",
                "Do not share personal information.",
                "Contact the supposed sender via their official website or phone number.",
            ]
            return fallback_verdict, fallback_explanation, fallback_steps
