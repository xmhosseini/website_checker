# 🔍 Website Keyword Monitor

Polls a website section every 10 minutes and sends a Gmail alert when keyword found.

## Setup

```bash
python3.8 -m venv myenv
source myenv/bin/activate
python -m pip install requests==2.31.0 beautifulsoup4==4.12.3
```

**Gmail Setup**:
1. Go to https://myaccount.google.com/apppasswords and create an App Password.
2. replace the MAIL args in `monitor.py`.

## Usage

```bash
python monitor.py
```

Runs continuously until stopped (`Ctrl+C`). 
