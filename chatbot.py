"""
chatbot.py — Cyber Awareness Chatbot module.

How it works:
  1. Validate the input (not empty, not too long).
  2. Run a local guardrail check — if the question is about harmful topics,
     return a polite refusal without ever calling the AI API.
  3. Build a prompt that includes the last few messages for conversational context.
  4. Call the Gemini API and return the response.

The guardrail is intentionally two-layered:
  - Local keyword check (fast, free, catches obvious misuse before an API call).
  - The AI's own system instruction (SYSTEM_CONTEXT in ai_client.py) also refuses
    harmful requests, providing a second line of defence.
"""

from dataclasses import dataclass, field

from ai_client import AIClient, AIServiceError, InvalidInputError

# Maximum characters accepted in a single chat message
MAX_MESSAGE_LENGTH: int = 500

# How many previous messages to include for conversational context.
# Keeping this small controls API token usage and cost.
HISTORY_WINDOW: int = 6

# Keywords that suggest the user is asking about offensive/harmful techniques.
# The check is case-insensitive and looks for these as substrings.
BLOCKED_TOPICS: list[str] = [
    "how to hack", "how do i hack", "hacking tutorial",
    "how to crack", "crack a password", "brute force",
    "create malware", "write malware", "create a virus", "write a virus",
    "create ransomware", "write ransomware",
    "steal password", "steal credentials", "steal login",
    "keylogger", "create a keylogger", "write a keylogger",
    "bypass 2fa", "bypass mfa", "bypass authentication",
    "exploit vulnerability", "sql injection tutorial",
    "phishing email template", "create a phishing", "write a phishing",
    "ddos attack", "denial of service attack",
    "social engineering attack", "manipulate someone into",
    "dox someone", "doxxing",
    "evade antivirus", "bypass antivirus", "evade detection",
]

# Topics the chatbot is designed to help with — used to redirect off-topic questions
SAFE_TOPICS: list[str] = [
    "phishing", "online scams", "password security", "MFA", "2FA",
    "multi-factor authentication", "safe browsing", "suspicious links",
    "social engineering awareness", "privacy", "software updates",
    "public Wi-Fi safety", "account security", "data breaches",
    "identity theft", "ransomware awareness", "email safety",
]

# The refusal message shown when a harmful request is detected
REFUSAL_MESSAGE = (
    "I'm here to help you stay safe online, but I can only answer questions "
    "about cybersecurity awareness and defence. I'm not able to help with "
    "offensive techniques or anything that could be used to harm others.\n\n"
    "If you have a question about protecting yourself — such as how to spot "
    "phishing, how to use 2FA, or how to create strong passwords — I'd be "
    "happy to help with that! 😊"
)


@dataclass
class ChatMessage:
    """
    A single message in the conversation.

    Attributes:
        role:       'user' or 'assistant'.
        content:    The message text.
        is_blocked: True if the guardrail prevented this from reaching the AI.
    """
    role: str
    content: str
    is_blocked: bool = False


class CyberChatbot:
    """
    An educational cybersecurity awareness chatbot.

    It answers beginner questions on topics such as phishing, 2FA, strong
    passwords, safe browsing, and privacy. It refuses to help with any
    offensive or harmful cybersecurity techniques.

    Usage:
        client = AIClient()
        bot = CyberChatbot(client)
        history: list[ChatMessage] = []
        response = bot.chat("What is phishing?", history)
        history.append(ChatMessage(role="user", content="What is phishing?"))
        history.append(response)
    """

    def __init__(self, ai_client: AIClient) -> None:
        self._ai = ai_client

    def chat(self, user_message: str, history: list[ChatMessage]) -> ChatMessage:
        """
        Process a user message and return the assistant's reply.

        Args:
            user_message: The question or message from the user.
            history:      Previous messages in the conversation (for context).

        Returns:
            A ChatMessage with role='assistant'.

        Raises:
            InvalidInputError: If the message is empty.
            AIServiceError:    If the AI call fails.
        """
        self._validate(user_message)

        # Truncate silently if the message exceeds the length limit
        if len(user_message) > MAX_MESSAGE_LENGTH:
            user_message = user_message[:MAX_MESSAGE_LENGTH]

        # Guardrail: block harmful requests before calling the API
        if self._is_harmful(user_message):
            return ChatMessage(role="assistant", content=REFUSAL_MESSAGE, is_blocked=True)

        prompt = self._build_prompt(user_message, history)
        response_text = self._ai.send_prompt(prompt)

        return ChatMessage(role="assistant", content=response_text)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(message: str) -> None:
        """Raise InvalidInputError if the message is empty or whitespace."""
        if not message or not message.strip():
            raise InvalidInputError("Please type a question before sending.")

    @staticmethod
    def _is_harmful(message: str) -> bool:
        """
        Return True if the message appears to be asking about offensive techniques.

        Checks for substring matches against BLOCKED_TOPICS (case-insensitive).
        This runs locally before any API call is made.
        """
        message_lower = message.lower()
        return any(topic in message_lower for topic in BLOCKED_TOPICS)

    @staticmethod
    def _build_prompt(user_message: str, history: list[ChatMessage]) -> str:
        """
        Build a multi-turn prompt for the AI that includes recent history.

        Only the last HISTORY_WINDOW messages are included to keep costs low.
        """
        # Use the most recent messages for context
        recent = history[-HISTORY_WINDOW:] if len(history) > HISTORY_WINDOW else history

        # Format prior conversation as a readable transcript
        conversation_lines: list[str] = []
        for msg in recent:
            label = "User" if msg.role == "user" else "Assistant"
            conversation_lines.append(f"{label}: {msg.content}")

        conversation_str = "\n".join(conversation_lines)
        context_block = (
            f"Previous conversation:\n{conversation_str}\n\n"
            if conversation_lines
            else ""
        )

        return (
            f"{context_block}"
            f"User: {user_message}\n\n"
            "Please answer the user's question in simple, beginner-friendly language. "
            "Use a short real-world example if it helps explain the concept. "
            "Focus on what the user can DO to stay safe. "
            "At the end of your response, suggest one or two follow-up questions "
            "the user might want to ask next."
        )
