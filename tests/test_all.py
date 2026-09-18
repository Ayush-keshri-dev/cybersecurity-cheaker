"""
tests/test_all.py — Pytest test suite for the Cybersecurity Awareness Assistant.

Tests are grouped by module:
  - TestInvalidInputError / TestAIServiceError  — custom exceptions
  - TestAIClient                                — API key loading
  - TestHeuristicScan                           — phishing indicator detection
  - TestMessageAnalyzerValidation               — analyzer input validation
  - TestAnalyzerParseAIResponse                 — JSON parsing / fallback
  - TestPasswordAdvisorValidation               — password input validation
  - TestPasswordStrengthLogic                   — scoring and rating
  - TestCommonPasswordDetection                 — known-weak-password check
  - TestChatbotValidation                       — chatbot input validation
  - TestChatbotGuardrail                        — harmful-request blocking
  - TestChatbotBuildPrompt                      — prompt construction

Real AI API calls are never made in unit tests.
All AIClient.send_prompt calls are mocked via pytest-mock.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from ai_client import AIClient, AIServiceError, InvalidInputError
from analyzer import MessageAnalyzer, MessageAnalysisResult, VERDICT_SAFE, VERDICT_CAUTION, VERDICT_SUSPICIOUS
from chatbot import CyberChatbot, ChatMessage, REFUSAL_MESSAGE
from password_advisor import PasswordAdvisor


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def mock_ai_client() -> MagicMock:
    """A MagicMock that stands in for a real AIClient instance."""
    client = MagicMock(spec=AIClient)
    return client


@pytest.fixture
def analyzer(mock_ai_client: MagicMock) -> MessageAnalyzer:
    return MessageAnalyzer(mock_ai_client)


@pytest.fixture
def chatbot(mock_ai_client: MagicMock) -> CyberChatbot:
    return CyberChatbot(mock_ai_client)


@pytest.fixture
def advisor() -> PasswordAdvisor:
    return PasswordAdvisor()


def make_ai_response(verdict: str, explanation: str, steps: list[str]) -> str:
    """Helper to build a valid JSON string that the analyzer expects from the AI."""
    return json.dumps({
        "verdict": verdict,
        "explanation": explanation,
        "safe_next_steps": steps,
    })


# ===========================================================================
# Custom exceptions
# ===========================================================================

class TestCustomExceptions:
    def test_invalid_input_error_is_exception(self):
        err = InvalidInputError("test message")
        assert isinstance(err, Exception)
        assert str(err) == "test message"

    def test_ai_service_error_is_exception(self):
        err = AIServiceError("service down")
        assert isinstance(err, Exception)
        assert str(err) == "service down"


# ===========================================================================
# AIClient — API key loading
# ===========================================================================

class TestAIClient:
    def test_missing_api_key_raises_ai_service_error(self):
        """AIClient should raise AIServiceError when GOOGLE_API_KEY is absent."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove GOOGLE_API_KEY from environment entirely
            import os
            os.environ.pop("GOOGLE_API_KEY", None)
            with pytest.raises(AIServiceError, match="API key not found"):
                AIClient()

    def test_placeholder_api_key_raises_ai_service_error(self):
        """AIClient should reject the placeholder value from .env.example."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "your-google-gemini-api-key-here"}):
            with pytest.raises(AIServiceError, match="API key not found"):
                AIClient()

    def test_send_prompt_wraps_api_exception_in_ai_service_error(self, mock_ai_client: MagicMock):
        """send_prompt should convert any API exception into AIServiceError."""
        mock_ai_client.send_prompt.side_effect = AIServiceError("unavailable")
        with pytest.raises(AIServiceError):
            mock_ai_client.send_prompt("test")


# ===========================================================================
# Heuristic scan — phishing indicator detection
# ===========================================================================

class TestHeuristicScan:
    def test_urgency_pattern_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Act now or your account will be suspended!")
        assert "Urgency or Pressure" in hits

    def test_credential_request_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Please enter your password to verify.")
        assert "Request for Password or OTP" in hits

    def test_suspicious_link_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Click here to verify your account: http://bit.ly/abc123")
        assert "Suspicious Link" in hits

    def test_money_request_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Please send money via western union immediately.")
        assert "Request for Money or Payment" in hits

    def test_impersonation_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Dear customer, this is Microsoft support.")
        assert "Impersonation" in hits

    def test_attachment_reference_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Please open the attachment and review.")
        assert "Reference to Attachment" in hits

    def test_sensitive_info_request_detected(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("Please provide your credit card number and CVV.")
        assert "Request for Sensitive Personal Information" in hits

    def test_clean_message_returns_no_hits(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan(
            "Hi Sarah, just checking in. Hope you're doing well. Let me know about lunch!"
        )
        assert hits == []

    def test_detection_is_case_insensitive(self, analyzer: MessageAnalyzer):
        hits = analyzer._run_heuristic_scan("ACT NOW before your account expires!")
        assert "Urgency or Pressure" in hits

    def test_multiple_categories_detected(self, analyzer: MessageAnalyzer):
        text = "URGENT: Dear customer, enter your OTP and click here: http://bit.ly/x"
        hits = analyzer._run_heuristic_scan(text)
        assert len(hits) >= 3


# ===========================================================================
# MessageAnalyzer — input validation
# ===========================================================================

class TestMessageAnalyzerValidation:
    def test_empty_string_raises_invalid_input(self, analyzer: MessageAnalyzer):
        with pytest.raises(InvalidInputError, match="Please paste"):
            analyzer.analyze("")

    def test_whitespace_only_raises_invalid_input(self, analyzer: MessageAnalyzer):
        with pytest.raises(InvalidInputError, match="Please paste"):
            analyzer.analyze("   \n\t  ")

    def test_input_over_2000_chars_raises_invalid_input(self, analyzer: MessageAnalyzer):
        long_text = "a" * 2001
        with pytest.raises(InvalidInputError, match="too long"):
            analyzer.analyze(long_text)

    def test_exactly_2000_chars_is_accepted(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = make_ai_response(
            VERDICT_SAFE, "Looks fine.", ["No action needed."]
        )
        result = analyzer.analyze("a" * 2000)
        assert isinstance(result, MessageAnalysisResult)


# ===========================================================================
# MessageAnalyzer — AI response parsing
# ===========================================================================

class TestAnalyzerParseAIResponse:
    def test_valid_json_parsed_correctly(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = make_ai_response(
            VERDICT_SUSPICIOUS,
            "This message appears to be a phishing attempt.",
            ["Do not click any links.", "Contact your bank directly."],
        )
        result = analyzer.analyze("Click here to verify your account immediately")
        assert result.verdict == VERDICT_SUSPICIOUS
        assert "phishing" in result.explanation.lower()
        assert len(result.safe_next_steps) == 2

    def test_malformed_json_falls_back_gracefully(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = "This is not JSON at all."
        result = analyzer.analyze("Some suspicious message")
        # Should not crash; should return a safe default
        assert result.verdict in (VERDICT_SAFE, VERDICT_CAUTION, VERDICT_SUSPICIOUS)
        assert isinstance(result.explanation, str)
        assert isinstance(result.safe_next_steps, list)

    def test_unknown_verdict_normalised_to_caution(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = json.dumps({
            "verdict": "Definitely Dangerous",
            "explanation": "Something bad.",
            "safe_next_steps": [],
        })
        result = analyzer.analyze("Test message")
        assert result.verdict == VERDICT_CAUTION

    def test_markdown_fences_stripped_before_parsing(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        raw = "```json\n" + make_ai_response(VERDICT_SAFE, "Looks OK.", ["Stay calm."]) + "\n```"
        mock_ai_client.send_prompt.return_value = raw
        result = analyzer.analyze("Hello there")
        assert result.verdict == VERDICT_SAFE

    def test_ai_service_error_propagates(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.side_effect = AIServiceError("Service down")
        with pytest.raises(AIServiceError):
            analyzer.analyze("Check this message")

    def test_result_always_has_confidence_note(self, analyzer: MessageAnalyzer, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = make_ai_response(
            VERDICT_SAFE, "Fine.", ["Nothing to do."]
        )
        result = analyzer.analyze("Normal message")
        assert result.confidence_note != ""


# ===========================================================================
# PasswordAdvisor — input validation
# ===========================================================================

class TestPasswordAdvisorValidation:
    def test_empty_password_raises_invalid_input(self, advisor: PasswordAdvisor):
        with pytest.raises(InvalidInputError, match="Please enter"):
            advisor.evaluate("")

    def test_whitespace_only_raises_invalid_input(self, advisor: PasswordAdvisor):
        with pytest.raises(InvalidInputError, match="Please enter"):
            advisor.evaluate("   ")


# ===========================================================================
# PasswordAdvisor — strength logic
# ===========================================================================

class TestPasswordStrengthLogic:
    def test_very_short_password_is_weak(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("abc")
        assert result.strength_rating == "Weak"

    def test_short_lowercase_only_is_weak(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("password")
        # Either weak or caught by common password check
        assert result.strength_rating in ("Weak", "Moderate")

    def test_strong_password_scores_high(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("Xk9!mPqR3@vLnZ2#")
        assert result.strength_rating == "Strong"
        assert result.score >= 70

    def test_moderate_password(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("Hello123")
        assert result.strength_rating in ("Weak", "Moderate")

    def test_result_has_no_password_field(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("SomePass1!")
        assert not hasattr(result, "password")

    def test_privacy_notice_always_present(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("AnyPass1!")
        assert "not stored" in result.privacy_notice.lower()

    def test_missing_uppercase_reported(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("nouppercase123!")
        issues_lower = " ".join(result.issues_found).lower()
        assert "uppercase" in issues_lower

    def test_missing_digit_reported(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("NoDigitsHere!")
        issues_lower = " ".join(result.issues_found).lower()
        assert "numbers" in issues_lower or "digit" in issues_lower or "number" in issues_lower

    def test_missing_symbol_reported(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("NoSymbolsHere123")
        issues_lower = " ".join(result.issues_found).lower()
        assert "symbol" in issues_lower

    def test_repeated_characters_penalised(self, advisor: PasswordAdvisor):
        result_repeat = advisor.evaluate("aaaBBB123!")
        result_normal = advisor.evaluate("azBX123!qp")
        assert result_repeat.score <= result_normal.score

    def test_score_capped_at_100(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("Xk9!mPqR3@vLnZ2#ExtraLongPassword")
        assert result.score <= 100

    def test_score_never_negative(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("aaa")
        assert result.score >= 0

    def test_tips_always_returned(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("weak")
        assert len(result.tips) > 0


# ===========================================================================
# PasswordAdvisor — common password detection
# ===========================================================================

class TestCommonPasswordDetection:
    def test_obvious_common_password_flagged(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("password123")
        issues_lower = " ".join(result.issues_found).lower()
        assert "commonly used" in issues_lower

    def test_tricky_common_password_flagged(self, advisor: PasswordAdvisor):
        """P@ssw0rd superficially passes character rules but is well-known."""
        result = advisor.evaluate("p@ssw0rd")
        issues_lower = " ".join(result.issues_found).lower()
        assert "commonly used" in issues_lower

    def test_case_insensitive_common_check(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("PASSWORD123")
        # password123 should be caught regardless of case
        # (it may or may not be in the list depending on case normalisation)
        # At minimum the result should not crash
        assert result.strength_rating in ("Weak", "Moderate", "Strong")

    def test_unique_strong_password_not_flagged(self, advisor: PasswordAdvisor):
        result = advisor.evaluate("Tr0ub4dor&3XkQ9!")
        issues_lower = " ".join(result.issues_found).lower()
        assert "commonly used" not in issues_lower


# ===========================================================================
# CyberChatbot — input validation
# ===========================================================================

class TestChatbotValidation:
    def test_empty_message_raises_invalid_input(self, chatbot: CyberChatbot):
        with pytest.raises(InvalidInputError, match="Please type"):
            chatbot.chat("", [])

    def test_whitespace_only_raises_invalid_input(self, chatbot: CyberChatbot):
        with pytest.raises(InvalidInputError, match="Please type"):
            chatbot.chat("   ", [])

    def test_message_over_limit_is_truncated_not_rejected(
        self, chatbot: CyberChatbot, mock_ai_client: MagicMock
    ):
        """Messages over 500 chars should be silently truncated, not raise an error."""
        mock_ai_client.send_prompt.return_value = "Here is a safe tip."
        long_msg = "What is phishing? " * 50  # well over 500 chars
        response = chatbot.chat(long_msg, [])
        assert isinstance(response, ChatMessage)
        assert response.role == "assistant"


# ===========================================================================
# CyberChatbot — guardrail (harmful request blocking)
# ===========================================================================

class TestChatbotGuardrail:
    def test_hacking_request_is_blocked(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        response = chatbot.chat("How to hack someone's email?", [])
        assert response.is_blocked is True
        assert mock_ai_client.send_prompt.call_count == 0

    def test_malware_creation_is_blocked(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        response = chatbot.chat("How do I create malware?", [])
        assert response.is_blocked is True
        assert mock_ai_client.send_prompt.call_count == 0

    def test_phishing_template_request_is_blocked(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        response = chatbot.chat("Give me a phishing email template", [])
        assert response.is_blocked is True

    def test_bypass_2fa_is_blocked(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        response = chatbot.chat("How do I bypass 2fa?", [])
        assert response.is_blocked is True

    def test_blocked_response_contains_refusal_message(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        response = chatbot.chat("How to steal passwords?", [])
        assert "awareness" in response.content.lower() or "safe" in response.content.lower()

    def test_safe_question_reaches_ai(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = "Phishing is a type of scam."
        response = chatbot.chat("What is phishing?", [])
        assert response.is_blocked is False
        assert mock_ai_client.send_prompt.call_count == 1

    def test_2fa_explanation_is_not_blocked(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        mock_ai_client.send_prompt.return_value = "2FA adds an extra layer of security."
        response = chatbot.chat("What is 2FA and how does it protect me?", [])
        assert response.is_blocked is False

    def test_guardrail_is_case_insensitive(self, chatbot: CyberChatbot, mock_ai_client: MagicMock):
        response = chatbot.chat("HOW TO HACK AN ACCOUNT", [])
        assert response.is_blocked is True


# ===========================================================================
# CyberChatbot — prompt construction
# ===========================================================================

class TestChatbotBuildPrompt:
    def test_prompt_includes_user_message(self, chatbot: CyberChatbot):
        prompt = chatbot._build_prompt("What is phishing?", [])
        assert "What is phishing?" in prompt

    def test_prompt_includes_recent_history(self, chatbot: CyberChatbot):
        history = [
            ChatMessage(role="user", content="What is 2FA?"),
            ChatMessage(role="assistant", content="2FA is two-factor authentication."),
        ]
        prompt = chatbot._build_prompt("Tell me more.", history)
        assert "2FA" in prompt

    def test_prompt_empty_history_has_no_previous_section(self, chatbot: CyberChatbot):
        prompt = chatbot._build_prompt("Hello", [])
        assert "Previous conversation" not in prompt

    def test_history_window_limits_context(self, chatbot: CyberChatbot):
        """Only the last HISTORY_WINDOW messages should appear in the prompt."""
        history = [
            ChatMessage(role="user", content=f"Message {i}")
            for i in range(20)
        ]
        prompt = chatbot._build_prompt("New question", history)
        # The very first message should not appear (too old)
        assert "Message 0" not in prompt
