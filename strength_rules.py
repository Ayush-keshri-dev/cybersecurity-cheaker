"""
strength_rules.py — Password strength rules and thresholds.

This file contains only data — no logic.
The PasswordAdvisor in password_advisor.py uses these values to score passwords.

Passwords are NEVER stored, logged, or passed outside password_advisor.py.
"""

# ---------------------------------------------------------------------------
# Scoring weights — each criterion contributes points toward a 100-point total
# ---------------------------------------------------------------------------

# Points awarded for meeting the recommended length
LENGTH_SCORE: int = 30

# Points for having at least one uppercase letter
UPPERCASE_SCORE: int = 15

# Points for having at least one lowercase letter
LOWERCASE_SCORE: int = 10

# Points for having at least one digit (0–9)
DIGIT_SCORE: int = 20

# Points for having at least one symbol (!@#$... etc.)
SYMBOL_SCORE: int = 25

# ---------------------------------------------------------------------------
# Length thresholds
# ---------------------------------------------------------------------------

MIN_LENGTH: int = 8           # Below this is automatically Weak
RECOMMENDED_LENGTH: int = 14  # At or above this earns full LENGTH_SCORE

# ---------------------------------------------------------------------------
# Strength label bands
# score 0–39  → Weak
# score 40–69 → Moderate
# score 70–100→ Strong
# ---------------------------------------------------------------------------
STRENGTH_LEVELS: dict[str, tuple[int, int]] = {
    "Weak":     (0, 39),
    "Moderate": (40, 69),
    "Strong":   (70, 100),
}

# Streamlit status colours for each band
STRENGTH_COLORS: dict[str, str] = {
    "Weak":     "error",    # red
    "Moderate": "warning",  # orange/yellow
    "Strong":   "success",  # green
}

# ---------------------------------------------------------------------------
# Commonly used passwords that look "strong" but are well-known to attackers.
# All entries are stored lowercase — comparison is case-insensitive.
# ---------------------------------------------------------------------------
COMMON_WEAK_PASSWORDS: list[str] = [
    # Classic keyboard patterns
    "password", "password1", "password123", "password!",
    "123456", "1234567", "12345678", "123456789", "1234567890",
    "qwerty", "qwerty123", "qwerty!", "qwerty1",
    "abc123", "abcdef", "111111", "000000",
    # Deceptively "complex" but well-known
    "p@ssw0rd", "pa$$w0rd", "p@$$word", "p@ssword",
    "passw0rd", "pa55word", "pa55w0rd",
    "welcome1", "welcome1!", "w3lcome1",
    "admin123", "admin123!", "administrator",
    "letmein", "letmein1", "letmein!",
    "iloveyou", "iloveyou1", "iloveyou!",
    "sunshine", "sunshine1",
    "princess", "princess1",
    "dragon", "dragon1",
    "monkey", "monkey1",
    "master", "master1",
    "superman", "batman", "pokemon",
    "login", "login123",
    "pass", "pass123", "pass1234",
    "test", "test123", "test1234",
    "user", "user123",
    "hello", "hello123", "hello1",
    "football", "baseball", "basketball",
    "shadow", "shadow1",
    "trustno1", "trustno1!",
    "changeme", "changeme1", "changeme!",
    "correct horse battery staple",  # famous example — should be a passphrase though
    "Summer2024!", "Winter2024!", "Spring2024!", "Fall2024!",
    "January1!", "February1!", "March1!",
    "companyname1!", "company123!",
]
