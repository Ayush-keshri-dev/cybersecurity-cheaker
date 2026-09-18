# AI-Powered Cybersecurity Awareness Assistant

A beginner-friendly educational app built with Python, Streamlit, and Google Gemini AI. It helps you understand common cybersecurity risks and make safer decisions online.

> **Disclaimer:** This tool is for educational awareness only. It is not a substitute for professional security software. AI analysis can make mistakes — always verify suspicious messages through official channels.

---

## Features

| Tab | What it does |
|-----|-------------|
| 🔍 Is This Safe? | Paste a suspicious email, SMS, or social media message and get a risk assessment |
| 🔑 Password Advisor | Check how strong your password is — fully local, never sent anywhere |
| 💬 Cyber Chatbot | Ask beginner cybersecurity questions in plain English |

---

## Prerequisites

- Python 3.10 or newer
- A free Google Gemini API key (see below)
- A terminal / command prompt

---

## Setup

### 1. Download the project

```bash
# If you have git:
git clone <your-repo-url>
cd p1

# Or just download and unzip the folder, then open a terminal in it.
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a free Google Gemini API key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with a Google account
3. Click **Create API key**
4. Copy the key

### 5. Configure your API key

```bash
# Copy the example file
cp .env.example .env   # Mac/Linux
copy .env.example .env  # Windows
```

Open `.env` in any text editor and replace `your-google-gemini-api-key-here` with your real key:

```
GOOGLE_API_KEY=AIza...your-real-key...
```

> **Never share your `.env` file or commit it to version control.**

---

## Run the app

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

---

## Run the tests

```bash
pytest tests/ -v
```

---

## Project structure

```
p1/
├── app.py               # Streamlit UI — the main entry point
├── analyzer.py          # "Is This Safe?" message analysis logic
├── password_advisor.py  # Password strength checker (fully local)
├── chatbot.py           # Cyber awareness chatbot logic
├── ai_client.py         # Shared Google Gemini API wrapper
├── warning_signs.py     # Phishing/scam indicator patterns (data only)
├── strength_rules.py    # Password strength rules and thresholds (data only)
├── tests/
│   ├── __init__.py
│   └── test_all.py      # Pytest test suite
├── requirements.txt     # Python dependencies
├── .env.example         # Template for your API key
└── README.md            # This file
```

---

## What this app will NOT do

- Provide instructions for hacking, phishing, or attacking systems
- Store, log, or transmit your passwords
- Guarantee that a message is safe or dangerous
- Replace professional antivirus or security software

---

## Troubleshooting

**"GOOGLE_API_KEY not found"**
→ Make sure you created a `.env` file (not just `.env.example`) and added your real API key.

**"streamlit: command not found"**
→ Make sure your virtual environment is activated and you ran `pip install -r requirements.txt`.

**AI responses seem slow**
→ The free Gemini tier has rate limits. Wait a moment and try again.

---

## Learn more

- [NCSC Cyber Aware](https://www.ncsc.gov.uk/cyberaware)
- [CISA Cybersecurity Awareness](https://www.cisa.gov/cybersecurity-awareness-month)
- [Have I Been Pwned](https://haveibeenpwned.com/) — check if your email was in a data breach
