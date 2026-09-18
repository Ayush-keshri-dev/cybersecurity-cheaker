"""
warning_signs.py — Phishing and scam indicator patterns.

This file contains only data — no logic.
The MessageAnalyzer in analyzer.py uses these patterns for a fast local
pre-scan before calling the AI API.

Adding new patterns here improves detection without touching any logic.
"""

from dataclasses import dataclass, field


@dataclass
class WarningSign:
    """
    A single category of phishing/scam indicators.

    Attributes:
        category:    Short name shown to the user, e.g. "Urgency or Pressure".
        patterns:    List of lowercase keywords or phrases to look for.
        explanation: Plain-English description of why this pattern is dangerous.
    """
    category: str
    patterns: list[str] = field(default_factory=list)
    explanation: str = ""


# ---------------------------------------------------------------------------
# The master list of warning signs.
# All pattern strings are lowercase — matching is done case-insensitively.
# ---------------------------------------------------------------------------
WARNING_SIGNS: list[WarningSign] = [
    WarningSign(
        category="Urgency or Pressure",
        patterns=[
            "act now", "act immediately", "urgent", "urgently", "immediately",
            "right away", "limited time", "expires today", "last chance",
            "your account will be suspended", "your account has been suspended",
            "within 24 hours", "within 48 hours", "respond immediately",
            "failure to respond", "account locked", "verify immediately",
        ],
        explanation=(
            "Scammers create a false sense of urgency to stop you from "
            "thinking carefully. Legitimate organisations rarely demand "
            "instant action by threatening account suspension."
        ),
    ),
    WarningSign(
        category="Request for Password or OTP",
        patterns=[
            "enter your password", "confirm your password", "provide your password",
            "enter your otp", "enter your one-time", "confirm your otp",
            "share your otp", "share your verification code",
            "enter your pin", "confirm your pin", "provide your pin",
            "your verification code", "your security code",
            "we need your login", "login credentials",
        ],
        explanation=(
            "Legitimate companies and banks will never ask you to share your "
            "password or OTP by email, SMS, or chat. Anyone asking for these "
            "is almost certainly trying to steal access to your account."
        ),
    ),
    WarningSign(
        category="Suspicious Link",
        patterns=[
            "bit.ly", "tinyurl", "t.co", "goo.gl", "ow.ly", "short.link",
            "click here", "click this link", "follow this link",
            "verify your account", "confirm your account",
            "log in here", "login here", "sign in here",
            "update your details", "update your information",
            "http://", "secure-login", "account-verify", "webscr",
        ],
        explanation=(
            "Shortened or unusual-looking links can hide the real destination. "
            "Always hover over a link before clicking and check the actual web "
            "address. Legitimate services use their own official domain names."
        ),
    ),
    WarningSign(
        category="Request for Money or Payment",
        patterns=[
            "send money", "transfer money", "wire transfer", "gift card",
            "buy gift cards", "pay with gift card", "itunes card",
            "google play card", "amazon gift card", "bitcoin", "crypto",
            "western union", "moneygram", "pay immediately", "payment required",
            "fee required", "processing fee", "release fee", "tax payment",
            "inheritance", "lottery winner", "prize money", "you have won",
        ],
        explanation=(
            "Requests for money via unusual methods like gift cards, wire "
            "transfers, or cryptocurrency are a major red flag. Scammers choose "
            "these methods because the payments are almost impossible to reverse."
        ),
    ),
    WarningSign(
        category="Impersonation",
        patterns=[
            "dear customer", "dear user", "dear account holder",
            "your bank", "your financial institution",
            "microsoft support", "apple support", "google support",
            "amazon support", "paypal team", "netflix team",
            "irs", "hmrc", "tax authority", "government notice",
            "fbi", "police department", "interpol",
            "from the desk of", "official notice",
        ],
        explanation=(
            "Scammers impersonate trusted brands and authorities to make their "
            "messages seem legitimate. Notice that they often use generic greetings "
            "like 'Dear Customer' instead of your real name."
        ),
    ),
    WarningSign(
        category="Unusual Spelling or Wording",
        patterns=[
            "kindly do the needful", "do the needful", "revert back",
            "irregardless", "your's sincerely", "plese", "immidiately",
            "recieve", "priviledge", "guaruntee", "occured", "untill",
            "benifit", "sucessful", "definitly", "seperately",
        ],
        explanation=(
            "Poor grammar, unusual phrasing, or misspelled words can indicate "
            "that the message was written in a hurry or by someone unfamiliar "
            "with the language. Professional organisations proofread their messages."
        ),
    ),
    WarningSign(
        category="Reference to Attachment",
        patterns=[
            "open the attachment", "see attached", "open attached",
            "download the file", "download attachment", "view the document",
            "open document", "attached invoice", "attached receipt",
            "attached file", "open the pdf", "open the word document",
            "scan the qr code", "scan this code",
        ],
        explanation=(
            "Unexpected attachments are one of the most common ways malware is "
            "delivered. Never open attachments from senders you don't recognise, "
            "even if the email looks official."
        ),
    ),
    WarningSign(
        category="Request for Sensitive Personal Information",
        patterns=[
            "social security number", "social security", "ssn",
            "national insurance number", "national id",
            "date of birth", "mother's maiden name",
            "credit card number", "card number", "cvv", "card verification",
            "bank account number", "sort code", "routing number",
            "passport number", "driver's license", "driving licence",
            "confirm your identity", "verify your identity",
        ],
        explanation=(
            "Legitimate organisations already have the information they need "
            "and will not ask you to confirm sensitive personal details by email "
            "or text message. Providing this information can lead to identity theft."
        ),
    ),
]
