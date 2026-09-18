# AI-Powered Cybersecurity Awareness Assistant — Implementation Plan

## Top-Level Overview

**Goal:** Build a beginner-friendly, educational cybersecurity awareness web application using Python, Streamlit, and an LLM API.

**Scope:** Three self-contained modules presented as tabs in a single Streamlit app:
1. "Is This Safe?" Message Analyzer
2. Password Safety Advisor (fully local — no AI API)
3. Cyber Awareness Chatbot

**Approach:** Simple modular architecture — one Python file per module plus a shared AI client wrapper. All analysis logic lives in plain Python classes with type hints. The Streamlit app file imports and orchestrates the modules. No database, no persistent storage, no user accounts.

**Guiding Constraints:**
- Passwords never leave local memory and never reach the AI API
- The chatbot includes a guardrail that blocks harmful or offensive-security requests
- All results use beginner-friendly plain English
- Every verdict includes a recommended safe action
- The app displays a visible disclaimer that it is for educational purposes only

---

## Folder Structure

```
p1/
├── app.py                   # Streamlit entry point — UI only
├── analyzer.py              # "Is This Safe?" module
├── password_advisor.py      # Password Safety module (local only)
├── chatbot.py               # Cyber Awareness Chatbot module
├── ai_client.py             # Shared AI API wrapper
├── warning_signs.py         # Phishing heuristic rules data
├── strength_rules.py        # Password strength rules data
├── requirements.txt         # Project dependencies
├── .env                     # API key (not committed to version control)
├── .env.example             # Template showing required env vars
└── README.md                # Setup instructions for beginners
```

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding and Dependencies

**Status:** [ ] pending

**Intent:**
Create the full folder/file structure, install dependencies, and configure the environment so that every subsequent sub-task has a working foundation to build on.

**Expected Outcomes:**
- All files listed in the folder structure exist (empty stubs are acceptable)
- `requirements.txt` lists all needed packages
- `.env.example` shows the required environment variable names without real values
- `README.md` explains how a beginner sets up and runs the app

**Todo List:**
1. Create `requirements.txt` with: `streamlit`, `openai` (or `google-generativeai` depending on AI provider choice), `python-dotenv`, `re` (stdlib — no install needed)
2. Create `.env.example` with placeholder: `OPENAI_API_KEY=your-key-here` (or the chosen provider's key name)
3. Create empty stub files: `app.py`, `analyzer.py`, `password_advisor.py`, `chatbot.py`, `ai_client.py`, `warning_signs.py`, `strength_rules.py`
4. Write `README.md` covering: prerequisites, virtual environment setup, how to add the API key, how to run with `streamlit run app.py`
5. Delete or repurpose the existing empty `index.py` (rename to `app.py` or delete)

**Relevant Context:**
- The workspace is currently a clean slate (`index.py` is empty)
- The AI provider must be decided before requirements.txt can be finalized — see open question in Step 3 below
- Python-dotenv is needed so beginners can store API keys in `.env` rather than hardcoding them

**AI Provider: Google Gemini 1.5 Flash** (confirmed)
- Free tier available at Google AI Studio — no credit card required
- Python SDK: `google-generativeai`
- API key environment variable: `GOOGLE_API_KEY`

---

### Sub-Task 2 — AI Client Wrapper (`ai_client.py`)

**Status:** [ ] pending

**Intent:**
Create a single, reusable wrapper around the chosen AI API. All other modules that need AI (Analyzer, Chatbot) call this one class. If the AI provider ever changes, only this file needs updating.

**Expected Outcomes:**
- `AIClient` class with a `send_prompt(prompt: str) -> str` method
- API key loaded from environment variable via `python-dotenv` — never hardcoded
- Graceful error handling: connection failures return a user-friendly fallback string rather than crashing
- A module-level constant `SYSTEM_CONTEXT` defining the assistant's persona and safety boundaries

**Todo List:**
1. Define `AIClient` class with `__init__` that loads the API key using `dotenv` and initializes the API client object
2. Implement `send_prompt(prompt: str) -> str` — sends a prompt, returns the response text
3. Implement `_load_api_key() -> str` — reads from environment, raises `InvalidAPIKeyError` with a beginner-friendly message if missing
4. Define custom exception `InvalidAPIKeyError` and `AIConnectionError`
5. Add `SYSTEM_CONTEXT` constant string: instructs the AI to act as a cybersecurity educator, explain things simply, refuse harmful requests, and never provide offensive-security instructions
6. Wrap the API call in try/except to catch network errors and return a safe fallback message

**Relevant Context:**
- Only `analyzer.py` and `chatbot.py` import from this module
- `password_advisor.py` must NOT import this module (passwords stay local)
- The `SYSTEM_CONTEXT` is the first line of defense for the chatbot's guardrail

---

### Sub-Task 3 — Phishing Warning Signs Data (`warning_signs.py`)

**Status:** [ ] pending

**Intent:**
Define a structured, easy-to-update collection of phishing and fraud indicators. This file is pure data — no logic. Keeping rules separate from logic means the list can grow without touching the analyzer.

**Expected Outcomes:**
- A list of `WarningSign` dataclass instances, each with: `category`, `patterns` (list of keywords/phrases), and `explanation`
- Categories cover all eight indicators from the requirements: urgency/pressure, credential/OTP requests, suspicious links, money requests, impersonation, spelling/wording, attachment references, sensitive information requests
- Each entry's `explanation` is written in plain English suitable for a beginner

**Todo List:**
1. Define a `WarningSign` dataclass with fields: `category: str`, `patterns: list[str]`, `explanation: str`
2. Create `WARNING_SIGNS: list[WarningSign]` — populate with at least 3–5 pattern entries per category
3. For the "suspicious links" category, include patterns like `bit.ly`, `tinyurl`, `click here`, `verify your account`
4. For the "urgency" category, include patterns like `act now`, `urgent`, `immediately`, `your account will be suspended`
5. For the "credential request" category, include patterns like `enter your password`, `confirm your OTP`, `verify your identity`
6. Ensure all pattern strings are lowercase (matching will be done case-insensitively)

**Relevant Context:**
- Imported only by `analyzer.py`
- Pattern matching in `analyzer.py` will lowercase the input before comparing
- These patterns are a first-pass heuristic — the AI then does the deeper analysis

---

### Sub-Task 4 — Password Strength Rules Data (`strength_rules.py`)

**Status:** [ ] pending

**Intent:**
Define the rules used to evaluate password strength as a pure data file. No analysis logic here — just the thresholds and the list of commonly-known weak passwords.

**Expected Outcomes:**
- Constants defining strength thresholds: minimum length, scoring weights per character class
- A `COMMON_WEAK_PASSWORDS` list of the most frequently used, easily guessed passwords (at least 30 entries including passwords that superficially pass character-variety rules, like `P@ssw0rd`)
- A `STRENGTH_LEVELS` mapping from score ranges to labels: `Weak`, `Moderate`, `Strong`

**Todo List:**
1. Define `MIN_LENGTH = 8` and `RECOMMENDED_LENGTH = 14`
2. Define scoring weights: `LENGTH_SCORE`, `UPPERCASE_SCORE`, `LOWERCASE_SCORE`, `DIGIT_SCORE`, `SYMBOL_SCORE` (all integers that sum to 100 when all criteria are met)
3. Create `COMMON_WEAK_PASSWORDS: list[str]` — include entries like `password`, `123456`, `qwerty`, `abc123`, `P@ssw0rd`, `Welcome1!`, `Admin123!`
4. Define `STRENGTH_LEVELS: dict[str, tuple[int, int]]` mapping label to score range, e.g., `{"Weak": (0, 39), "Moderate": (40, 69), "Strong": (70, 100)}`
5. Define `STRENGTH_COLORS: dict[str, str]` mapping label to a Streamlit-compatible color string for UI display

**Relevant Context:**
- Imported only by `password_advisor.py`
- Passwords are NEVER passed outside `password_advisor.py` — this file contains only static constants

---

### Sub-Task 5 — Message Analyzer Module (`analyzer.py`)

**Status:** [ ] pending

**Intent:**
Implement the core logic for the "Is This Safe?" feature. The analyzer first runs fast local heuristics (no API cost), then sends a structured prompt to the AI with the heuristic findings as context. The result is a plain-English verdict with warning signs and safe next steps.

**Expected Outcomes:**
- `MessageAnalysisResult` dataclass with fields: `verdict`, `warning_signs_found`, `explanation`, `safe_next_steps`, `confidence_note`
- `MessageAnalyzer` class with a `analyze(text: str) -> MessageAnalysisResult` method
- Heuristic scan runs first and is always instant
- AI is called only when input is non-empty and within length limits
- Verdict is one of three values: `"Likely Safe"`, `"Needs Caution"`, `"Suspicious"`
- Input validation rejects empty input and input over 2000 characters

**Todo List:**
1. Define `MessageAnalysisResult` dataclass with all five fields
2. Define `MessageAnalyzer` class; inject `AIClient` instance in `__init__`
3. Implement `analyze(text: str) -> MessageAnalysisResult` — the public entry point
4. Implement `_run_heuristic_scan(text: str) -> list[str]` — lowercases input, checks each `WarningSign`'s patterns, returns list of matched category names
5. Implement `_build_prompt(text: str, heuristic_hits: list[str]) -> str` — crafts a safe, structured prompt that tells the AI what heuristics were already found and asks for a verdict + explanation + next steps in JSON format
6. Implement `_parse_ai_response(raw: str) -> tuple[str, str, list[str]]` — parses the AI's JSON response into verdict, explanation, and next steps; falls back gracefully if JSON is malformed
7. Add input validation: raise `EmptyInputError` if blank, raise `InputTooLongError` if over 2000 characters
8. Add `confidence_note` as a static string: "This analysis is a guide only. When in doubt, do not click links or share information."
9. Define `EmptyInputError` and `InputTooLongError` as simple custom exceptions

**Relevant Context:**
- Imports: `AIClient` from `ai_client.py`, `WARNING_SIGNS` from `warning_signs.py`
- The prompt must instruct the AI to respond in structured JSON with keys: `verdict`, `explanation`, `safe_next_steps`
- The AI prompt must include an explicit instruction NOT to claim certainty — use language like "appears to be" and "may be"

---

### Sub-Task 6 — Password Safety Advisor Module (`password_advisor.py`)

**Status:** [ ] pending

**Intent:**
Implement fully local password strength analysis. No AI, no network calls. The password is evaluated, scored, and immediately discarded — it is never stored in any attribute or returned in any result object.

**Expected Outcomes:**
- `PasswordAnalysisResult` dataclass with fields: `strength_rating`, `score`, `issues_found`, `tips`, `privacy_notice` — note: NO `password` field
- `PasswordAdvisor` class with `evaluate(password: str) -> PasswordAnalysisResult` method
- Evaluation runs five checks: length, uppercase, lowercase, digits, symbols, common-password list
- Result always includes `privacy_notice = "Your password was not stored, sent, or logged."`
- Input validation rejects empty password

**Todo List:**
1. Define `PasswordAnalysisResult` dataclass — confirm no `password` field exists
2. Define `PasswordAdvisor` class (no constructor dependencies needed — no AI client)
3. Implement `evaluate(password: str) -> PasswordAnalysisResult` — orchestrates all checks
4. Implement `_check_length(password: str) -> tuple[int, str | None]` — returns partial score and an issue message if too short
5. Implement `_check_character_variety(password: str) -> tuple[int, list[str]]` — checks for uppercase, lowercase, digits, symbols using `re` module; returns score contribution and list of missing character class messages
6. Implement `_check_common_patterns(password: str) -> tuple[int, str | None]` — checks against `COMMON_WEAK_PASSWORDS` (case-insensitive); returns score penalty and an issue message if matched
7. Implement `_calculate_strength_label(score: int) -> str` — maps score to `"Weak"` / `"Moderate"` / `"Strong"` using `STRENGTH_LEVELS`
8. Implement `_generate_tips(issues: list[str]) -> list[str]` — converts each issue into a specific, actionable tip
9. Add validation: raise `EmptyInputError` if password is empty or whitespace

**Relevant Context:**
- Imports only from `strength_rules.py` and Python stdlib (`re`)
- Must NOT import `ai_client.py` — enforce this as a code comment at the top of the file
- The `evaluate` method must not assign `password` to `self` at any point

---

### Sub-Task 7 — Cyber Awareness Chatbot Module (`chatbot.py`)

**Status:** [ ] pending

**Intent:**
Implement the educational chatbot. The chatbot maintains a per-session conversation history (held in memory only), applies a guardrail check before every AI call, and always responds in beginner-friendly language. Session history is passed to the AI for context but is never persisted.

**Expected Outcomes:**
- `ChatMessage` dataclass with fields: `role`, `content`, `is_blocked`
- `CyberChatbot` class with `chat(user_message: str, history: list[ChatMessage]) -> ChatMessage` method
- Guardrail check runs before every AI call
- Blocked requests return a polite, educational refusal without revealing what the blocked topic was
- The chatbot covers all eleven topics from the requirements
- Suggested follow-up questions are included in the response when relevant

**Todo List:**
1. Define `ChatMessage` dataclass with `role: str`, `content: str`, `is_blocked: bool = False`
2. Define `BLOCKED_TOPICS: list[str]` — a module-level list of keywords/phrases that indicate a harmful request (e.g., `"how to hack"`, `"create malware"`, `"bypass 2fa"`, `"steal password"`, `"phishing email template"`)
3. Define `SAFE_TOPICS: list[str]` — the eleven educational topics; used to redirect off-topic questions
4. Define `CyberChatbot` class; inject `AIClient` in `__init__`
5. Implement `chat(user_message: str, history: list[ChatMessage]) -> ChatMessage` — the public entry point
6. Implement `_is_harmful(message: str) -> bool` — checks lowercased message against `BLOCKED_TOPICS`; returns True if any match found
7. Implement `_build_prompt(user_message: str, history: list[ChatMessage]) -> str` — builds a multi-turn prompt including recent history (last 6 messages maximum to control token cost), the user's question, and an instruction to respond simply with a real-world example
8. Implement `_format_refusal() -> str` — returns a consistent, friendly message explaining the chatbot only covers awareness topics
9. Add input validation: raise `EmptyInputError` if message is empty; truncate silently if over 500 characters
10. Add suggested follow-ups as a parenthetical at the end of every AI response, generated by appending a follow-up instruction to the prompt

**Relevant Context:**
- Imports `AIClient` from `ai_client.py`
- Session history is managed in `app.py` using `st.session_state` — `chatbot.py` receives history as a parameter and returns it; it does not own state
- The `SYSTEM_CONTEXT` defined in `ai_client.py` already instructs the AI to refuse harmful requests — the guardrail in this module is an additional local check that runs before the API is even called

---

### Sub-Task 8 — Streamlit UI (`app.py`)

**Status:** [ ] pending

**Intent:**
Build the complete Streamlit front-end that ties all modules together. The UI uses tabs to separate the three features. All session state (chat history, analysis results) is managed here using `st.session_state`. The UI contains no business logic — it only calls module methods and displays results.

**Expected Outcomes:**
- Three-tab layout: "🔍 Is This Safe?", "🔑 Password Advisor", "💬 Cyber Chatbot"
- Each tab is self-contained and visually clear for a beginner
- A visible disclaimer banner appears at the top of every tab
- Verdicts use colored indicators (with text labels — not color alone) for accessibility
- Password input uses `type="password"` so the characters are masked in the UI
- Errors from all modules are caught and displayed as friendly `st.warning` or `st.error` messages — the app never crashes
- Chat history is stored in `st.session_state["chat_history"]` and displayed as a scrollable conversation
- A "Clear Chat" button resets session history

**Todo List:**
1. Set Streamlit page config: title, icon, wide layout
2. Add a top-of-page disclaimer using `st.info`: "This tool is for educational awareness only. It is not a substitute for professional security software."
3. Create three tabs using `st.tabs`
4. **Tab 1 — Analyzer:**
   a. `st.text_area` for message input
   b. "Analyze" button triggers `MessageAnalyzer.analyze()`
   c. Display verdict with color-coded `st.success` / `st.warning` / `st.error` plus bold text label
   d. Display warning signs as a bulleted list
   e. Display explanation paragraph
   f. Display safe next steps as a numbered list
   g. Display confidence note in italics
   h. Wrap in try/except for `EmptyInputError`, `InputTooLongError`, `AIConnectionError`
5. **Tab 2 — Password Advisor:**
   a. `st.text_input` with `type="password"` for password entry
   b. "Check Strength" button triggers `PasswordAdvisor.evaluate()`
   c. Display strength rating with appropriate color (`st.success` / `st.warning` / `st.error`)
   d. Display issues list
   e. Display tips list
   f. Display `privacy_notice` in a small `st.caption`
   g. Wrap in try/except for `EmptyInputError`
6. **Tab 3 — Chatbot:**
   a. Initialize `st.session_state["chat_history"]` as empty list on first load
   b. Display existing chat history using `st.chat_message` components
   c. `st.chat_input` for new messages
   d. On submit: call `CyberChatbot.chat()`, append both user and assistant messages to session state, rerun
   e. "Clear Chat" button resets `st.session_state["chat_history"]`
   f. Wrap in try/except for `EmptyInputError`, `AIConnectionError`
7. Instantiate `AIClient`, `MessageAnalyzer`, `PasswordAdvisor`, `CyberChatbot` at module level (outside any tab block) so they are created once per session

**Relevant Context:**
- `st.session_state` persists across reruns within a session but resets when the browser tab is closed — this is the correct and intended behavior
- Password input must use `type="password"` — Streamlit supports this via the `type` parameter on `st.text_input`
- Do not call `st.rerun()` inside a try/except block — place it after the block

---

### Sub-Task 9 — README and Final Setup

**Status:** [ ] pending

**Intent:**
Write a clear, step-by-step README that a complete beginner can follow to get the app running. This is a first-class deliverable, not an afterthought — without it, a beginner cannot use the app.

**Expected Outcomes:**
- `README.md` explains all setup steps in plain English
- Covers: Python version requirement, creating a virtual environment, installing dependencies, creating the `.env` file, running the app
- Includes a short description of each of the three features
- Includes a "What this app will NOT do" section reinforcing the safety boundary
- Includes a troubleshooting section for the two most common issues: missing API key and Streamlit not found

**Todo List:**
1. Write introduction: what the app is and who it is for
2. Write prerequisites section: Python 3.10+, pip, a terminal
3. Write setup steps: clone/download, create venv, `pip install -r requirements.txt`, create `.env` from `.env.example`
4. Write run instructions: `streamlit run app.py`
5. Write feature descriptions for all three tabs
6. Write "What this app will NOT do" section
7. Write troubleshooting section

**Relevant Context:**
- The `.env.example` file created in Sub-Task 1 must match the variable name used in `ai_client.py`
- The README should mention that the app was built for educational purposes and link to a reputable cybersecurity awareness resource (e.g., NCSC or CISA)

---

## AI Integration Approach

| Module | Uses AI? | Reason |
|---|---|---|
| `analyzer.py` | Yes | Deep semantic analysis of free-form text requires language understanding beyond simple keyword matching |
| `password_advisor.py` | **No** | Passwords must never leave the local session; rule-based scoring is sufficient and more trustworthy |
| `chatbot.py` | Yes | Open-ended Q&A on varied topics requires generative language capability |
| `ai_client.py` | Owns AI | Single point of configuration and error handling for all AI calls |

**Prompt Engineering Approach:**
- All prompts include an explicit system instruction to refuse harmful requests
- Analyzer prompt requests structured JSON output to make parsing reliable
- Chatbot prompt includes a rolling window of the last 6 messages for conversational context
- All prompts are assembled in the module (not in the UI layer) so they can be tested independently

---

## Data Flow

```
User Input (app.py)
       |
       v
[Tab 1] MessageAnalyzer.analyze(text)
    --> _run_heuristic_scan(text)  -->  warning_signs.py patterns
    --> _build_prompt(text, hits)
    --> AIClient.send_prompt(prompt)  -->  AI API
    --> _parse_ai_response(raw)
    --> MessageAnalysisResult  -->  app.py display

[Tab 2] PasswordAdvisor.evaluate(password)
    --> _check_length / _check_character_variety / _check_common_patterns
    --> _calculate_strength_label / _generate_tips          strength_rules.py
    --> PasswordAnalysisResult  -->  app.py display
    [password is NOT passed to AIClient at any step]

[Tab 3] CyberChatbot.chat(message, history)
    --> _is_harmful(message)  -->  BLOCKED_TOPICS list
         if blocked  -->  _format_refusal()
         if safe     -->  _build_prompt(message, history)
                          --> AIClient.send_prompt(prompt)  -->  AI API
    --> ChatMessage  -->  app.py / st.session_state
```

---

## Validation Strategy

| Layer | What is Validated | How |
|---|---|---|
| UI (`app.py`) | Empty fields, display of errors | `st.warning` messages; try/except around module calls |
| Module entry points | Empty input, input too long | Custom exceptions `EmptyInputError`, `InputTooLongError` |
| `ai_client.py` | Missing API key | `InvalidAPIKeyError` raised in `_load_api_key` |
| `chatbot.py` | Harmful request | `_is_harmful()` check; returns refusal without calling AI |
| `analyzer.py` | Malformed AI JSON | `_parse_ai_response` falls back to safe defaults |

---

## Error-Handling Strategy

- **Never crash the app.** All exceptions are caught in `app.py` and displayed as friendly `st.warning` or `st.error` messages.
- **Custom exceptions** (`EmptyInputError`, `InputTooLongError`, `AIConnectionError`, `InvalidAPIKeyError`) carry beginner-friendly messages as their string argument.
- **AI failures** fall back to a static safe response: "The AI service is temporarily unavailable. Please try again shortly."
- **Malformed AI JSON** in the analyzer falls back to a generic `"Needs Caution"` verdict with the raw AI text shown as the explanation.
- **Harmful chatbot requests** are handled silently — no exception, just a polite refusal string returned as the `ChatMessage`.

---

## Testing Strategy

Since this is a beginner project, testing is kept simple and manual:

| Test Type | What to Test |
|---|---|
| **Heuristic scan** | Paste a message containing "act now" — confirm urgency category is detected |
| **Heuristic scan** | Paste a clean message — confirm no warning signs are returned |
| **Password — Weak** | Enter "abc" — confirm `Weak` rating and length issue |
| **Password — Strong** | Enter a 16-char mixed password — confirm `Strong` rating |
| **Password — Common** | Enter "P@ssw0rd" — confirm it is flagged despite passing character rules |
| **Chatbot — Safe** | Ask "What is phishing?" — confirm an educational response |
| **Chatbot — Blocked** | Ask "How do I hack someone's email?" — confirm polite refusal |
| **Chatbot — Off-topic** | Ask "What is the weather?" — confirm redirect to cybersecurity topics |
| **Empty input** | Submit each tab with no input — confirm friendly warning, no crash |
| **Long input** | Paste 3000 characters into the analyzer — confirm truncation/rejection message |

Unit tests using `pytest` can be added later for `PasswordAdvisor` and the heuristic scan — these are pure functions with no external dependencies.

---

## Security and Privacy Considerations

| Consideration | Implementation |
|---|---|
| API key never hardcoded | Loaded from `.env` via `python-dotenv`; `.env` excluded from version control via `.gitignore` |
| Passwords never stored | `password` parameter used only inside `evaluate()`; never assigned to `self` or included in result |
| Passwords never sent to AI | `password_advisor.py` has no import of `ai_client.py` |
| No persistent user data | Streamlit session state is in-memory only; cleared on tab close |
| AI responses displayed as plain text | Streamlit `st.write` / `st.markdown` used carefully; no `unsafe_allow_html=True` |
| Harmful request guardrail | Local keyword check in `chatbot.py` before AI is called; AI system prompt also instructs refusal |
| Disclaimer always visible | Static `st.info` banner at top of every tab |
| Confidence note always shown | Analyzer result always includes a note that the AI analysis is not definitive |
