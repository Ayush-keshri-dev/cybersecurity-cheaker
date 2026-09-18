"""
password_advisor.py — Local password strength checker.

PRIVACY GUARANTEE:
  - Passwords are NEVER stored, logged, or persisted anywhere.
  - Passwords are NEVER sent to the AI API or any external service.
  - The password is used only inside evaluate() and is not kept in any attribute.
  - The result object does NOT contain the password.

This module intentionally does NOT import ai_client.py.
"""

# NOTE: Do NOT import ai_client here. Passwords must never reach the AI API.
import re
from dataclasses import dataclass, field

from ai_client import InvalidInputError
from strength_rules import (
    COMMON_WEAK_PASSWORDS,
    DIGIT_SCORE,
    LENGTH_SCORE,
    LOWERCASE_SCORE,
    MIN_LENGTH,
    RECOMMENDED_LENGTH,
    STRENGTH_COLORS,
    STRENGTH_LEVELS,
    SYMBOL_SCORE,
    UPPERCASE_SCORE,
)

# Shown in the UI to reassure the user their password was not stored
PRIVACY_NOTICE = "🔒 Your password was not stored, sent, or logged anywhere."


@dataclass
class PasswordAnalysisResult:
    """
    The result of a local password strength check.

    Note: This dataclass intentionally has no 'password' field.

    Attributes:
        strength_rating: 'Weak', 'Moderate', or 'Strong'.
        score:           Internal 0–100 score used to determine the rating.
        issues_found:    Human-readable list of weaknesses detected.
        tips:            Specific, actionable improvement suggestions.
        privacy_notice:  Confirmation that the password was not stored or sent.
        color:           Streamlit status type ('error', 'warning', 'success').
    """
    strength_rating: str
    score: int
    issues_found: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    privacy_notice: str = PRIVACY_NOTICE
    color: str = "warning"


class PasswordAdvisor:
    """
    Evaluates password strength using local rules only.

    No AI, no network calls, no persistence.

    Usage:
        advisor = PasswordAdvisor()
        result = advisor.evaluate("MyP@ssword123")
    """

    def evaluate(self, password: str) -> PasswordAnalysisResult:
        """
        Run all strength checks and return a result.

        Args:
            password: The password string to evaluate.

        Returns:
            A PasswordAnalysisResult. The password itself is NOT in the result.

        Raises:
            InvalidInputError: If the password is empty.
        """
        if not password or not password.strip():
            raise InvalidInputError("Please enter a password to check.")

        issues: list[str] = []
        score: int = 0

        # Run each check; accumulate points and issue messages
        length_points, length_issue = self._check_length(password)
        score += length_points
        if length_issue:
            issues.append(length_issue)

        variety_points, variety_issues = self._check_character_variety(password)
        score += variety_points
        issues.extend(variety_issues)

        common_penalty, common_issue = self._check_common_patterns(password)
        score = max(0, score - common_penalty)
        if common_issue:
            issues.append(common_issue)

        repeat_penalty, repeat_issue = self._check_repeated_patterns(password)
        score = max(0, score - repeat_penalty)
        if repeat_issue:
            issues.append(repeat_issue)

        # Cap score at 100
        score = min(score, 100)

        strength_rating = self._calculate_strength_label(score)
        tips = self._generate_tips(issues)
        color = STRENGTH_COLORS.get(strength_rating, "warning")

        # The password variable goes out of scope here — it is not stored anywhere
        return PasswordAnalysisResult(
            strength_rating=strength_rating,
            score=score,
            issues_found=issues,
            tips=tips,
            color=color,
        )

    # ------------------------------------------------------------------
    # Private helpers — each returns (score_contribution, issue_or_None)
    # ------------------------------------------------------------------

    @staticmethod
    def _check_length(password: str) -> tuple[int, str | None]:
        """
        Award LENGTH_SCORE for meeting the recommended length.
        Award partial credit for meeting the minimum length.
        """
        length = len(password)
        if length >= RECOMMENDED_LENGTH:
            return LENGTH_SCORE, None
        if length >= MIN_LENGTH:
            # Partial credit: scales between 0 and LENGTH_SCORE
            partial = int(
                LENGTH_SCORE * (length - MIN_LENGTH) / (RECOMMENDED_LENGTH - MIN_LENGTH)
            )
            return partial, f"Password is {length} characters — aim for at least {RECOMMENDED_LENGTH}."
        # Below minimum
        return 0, (
            f"Password is too short ({length} characters). "
            f"Use at least {MIN_LENGTH}, ideally {RECOMMENDED_LENGTH} or more."
        )

    @staticmethod
    def _check_character_variety(password: str) -> tuple[int, list[str]]:
        """Check for uppercase, lowercase, digits, and symbols."""
        points = 0
        issues: list[str] = []

        if re.search(r"[A-Z]", password):
            points += UPPERCASE_SCORE
        else:
            issues.append("No uppercase letters (A–Z).")

        if re.search(r"[a-z]", password):
            points += LOWERCASE_SCORE
        else:
            issues.append("No lowercase letters (a–z).")

        if re.search(r"\d", password):
            points += DIGIT_SCORE
        else:
            issues.append("No numbers (0–9).")

        if re.search(r"[!@#$%^&*()\-_=+\[\]{}|;:',.<>?/`~\"\\]", password):
            points += SYMBOL_SCORE
        else:
            issues.append("No symbols (e.g. !, @, #, $).")

        return points, issues

    @staticmethod
    def _check_common_patterns(password: str) -> tuple[int, str | None]:
        """
        Deduct 40 points if the password matches a well-known weak password,
        even if it superficially passes other checks (e.g. 'P@ssw0rd').
        """
        if password.lower() in COMMON_WEAK_PASSWORDS:
            return 40, (
                "This password is on the list of commonly used passwords and "
                "is likely to be guessed quickly by attackers."
            )
        return 0, None

    @staticmethod
    def _check_repeated_patterns(password: str) -> tuple[int, str | None]:
        """
        Deduct 20 points if the password contains obvious repeated characters
        or sequences (e.g. 'aaa', '111', 'abcabc').
        """
        # Three or more identical consecutive characters
        if re.search(r"(.)\1{2,}", password):
            return 20, "Contains repeated characters in a row (e.g. 'aaa' or '111')."
        # Simple repeated two-character block: e.g. 'abababab'
        if re.search(r"(.{2,})\1{2,}", password):
            return 20, "Contains a repeated pattern (e.g. 'abab' or '1212')."
        return 0, None

    @staticmethod
    def _calculate_strength_label(score: int) -> str:
        """Map a numeric score to a strength label."""
        for label, (low, high) in STRENGTH_LEVELS.items():
            if low <= score <= high:
                return label
        return "Weak"

    @staticmethod
    def _generate_tips(issues: list[str]) -> list[str]:
        """
        Convert detected issues into specific, actionable improvement tips.
        Also always adds the universal passphrase tip.
        """
        tips: list[str] = []

        issue_to_tip: dict[str, str] = {
            "uppercase": "Add at least one uppercase letter (e.g. A, B, C).",
            "lowercase": "Add at least one lowercase letter (e.g. a, b, c).",
            "numbers": "Include at least one number (0–9).",
            "symbols": "Add a symbol such as !, @, #, $, or %.",
            "too short": (
                f"Make your password at least {RECOMMENDED_LENGTH} characters long."
            ),
            "commonly used": (
                "Choose a password that is unique and not based on common words."
            ),
            "repeated": "Avoid repeating the same character or sequence.",
        }

        for issue in issues:
            issue_lower = issue.lower()
            for keyword, tip in issue_to_tip.items():
                if keyword in issue_lower and tip not in tips:
                    tips.append(tip)

        # Universal tips added for everyone
        if "Consider using a passphrase" not in " ".join(tips):
            tips.append(
                "Consider using a passphrase — three or four random unrelated words "
                "joined together, like 'PurpleCloudBicycle7!'."
            )
        tips.append("Use a different password for every account.")
        tips.append("Consider using a reputable password manager to store passwords safely.")

        return tips
