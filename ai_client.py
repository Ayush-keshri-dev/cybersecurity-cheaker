"""
ai_client.py — Shared Google Gemini API wrapper.

All modules that need AI (analyzer, chatbot) use this single class.
If the AI provider ever changes, only this file needs updating.

Passwords are NEVER passed to this module. See password_advisor.py.

Uses the current google-genai SDK (google.genai), not the deprecated
google.generativeai package.
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# The system instruction tells Gemini who it is and what it must never do.
# This is the first line of defense against misuse.
SYSTEM_CONTEXT = (
    "You are a cybersecurity awareness assistant for beginners. "
    "Your only job is to help people stay safe online through education. "
    "Always explain things in simple, plain English. "
    "Never provide instructions for hacking, creating malware, stealing credentials, "
    "bypassing authentication, exploiting systems, or any other harmful activity. "
    "If asked about offensive or harmful topics, politely refuse and redirect "
    "to a relevant safety tip instead. "
    "Always encourage users to verify suspicious messages through official channels."
)


class AIServiceError(Exception):
    """Raised when the AI API call fails for any reason."""
    pass


class InvalidInputError(Exception):
    """Raised when user input is empty, too long, or otherwise unusable."""
    pass


class AIClient:
    """
    A simple wrapper around the Google Gemini API (google-genai SDK).

    Usage:
        client = AIClient()
        response = client.send_prompt("What is phishing?")
    """

    def __init__(self) -> None:
        api_key = self._load_api_key()
        # Create the genai client with the API key
        self._client = genai.Client(api_key=api_key)

    def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the response text.

        Args:
            prompt: The text prompt to send.

        Returns:
            The model's response as a plain string.

        Raises:
            AIServiceError: If the API call fails for any reason.
        """
        try:
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_CONTEXT,
                ),
            )
            return response.text.strip()
        except Exception as exc:
            raise AIServiceError(
                "The AI service is temporarily unavailable. Please try again shortly."
            ) from exc

    @staticmethod
    def _load_api_key() -> str:
        """
        Read the API key from the environment.

        Raises:
            AIServiceError: If the key is missing or looks like the placeholder.
        """
        key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not key or key == "your-google-gemini-api-key-here":
            raise AIServiceError(
                "Google API key not found. "
                "Please create a .env file with GOOGLE_API_KEY=your-key. "
                "See README.md for instructions."
            )
        return key
