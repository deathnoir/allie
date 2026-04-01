# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
JARVIS (Just A Rather Very Intelligent System) is a voice-first AI assistant supporting macOS and Windows. On macOS it connects to Apple Calendar, Mail, Notes via AppleScript. On Windows it uses Google Calendar/Gmail APIs and local SQLite for notes. It can spawn Claude Code sessions for development tasks. The user interacts through a browser showing an audio-reactive Three.js particle orb.

## Commands

### Backend
```bash
python server.py                      # Start FastAPI server on https://localhost:8340
```

### Frontend
```bash
cd frontend && npm install            # Install dependencies
cd frontend && npm run dev            # Vite dev server on http://localhost:5173
cd frontend && npm run build          # TypeScript check + production build
```

### Testing
```bash
python -m pytest tests/               # Run all tests
python -m pytest tests/test_classifier.py  # Run a single test file
```

### Setup (first time)
```bash
cp .env.example .env                  # Then add ANTHROPIC_API_KEY and FISH_API_KEY
pip install -r requirements.txt
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
```

### Windows-only: Google API setup
```bash
# Place google_credentials.json in data/ (from Google Cloud Console)
python -m jarvis_platform.google_auth  # One-time OAuth flow for Calendar + Gmail
```

## Architecture

### Voice Loop
```
Microphone → Web Speech API → WebSocket → FastAPI (server.py) → Claude Haiku → Fish Audio TTS → WebSocket → Speaker
```

The frontend sends speech transcripts over WebSocket. The server processes them through Claude, detects action tags in responses, executes system actions, and streams TTS audio back as binary WebSocket frames.

### Platform Abstraction (`jarvis_platform/`)
All platform-specific code is behind a unified interface:
- `jarvis_platform/__init__.py` — Detects `sys.platform`, re-exports from `darwin` or `win32`
- `jarvis_platform/darwin.py` — macOS: thin wrapper importing from existing `actions.py`, `screen.py`, `calendar_access.py`, `mail_access.py`, `notes_access.py`
- `jarvis_platform/win32/` — Windows: terminal (Windows Terminal/PowerShell + pywinauto), browser (subprocess/webbrowser), screen (mss + pywin32), calendar/mail (Google API), notes (local SQLite)
- `jarvis_platform/google_auth.py` — OAuth 2.0 flow for Google Calendar + Gmail
- `jarvis_platform/google_services.py` — Google Calendar and Gmail API clients

### Backend (Python)
- `server.py` — Monolithic main server (~2400 lines): WebSocket handler, LLM integration, action dispatch, TTS streaming, system prompt construction, conversation memory management
- `memory.py` — SQLite + FTS5 persistent memory: facts, preferences, tasks, notes. Relevant memories are injected into every LLM call
- `dispatch_registry.py` — SQLite-backed registry tracking active/recent Claude Code build dispatches
- `conversation.py` — Multi-turn planning session state: decisions, plan summaries, context windowing (20 messages, 5-min timeout)
- `planner.py` — Pre-build planning: detects planning intent, generates clarifying questions, builds structured prompts from templates
- `actions.py` — macOS system action execution (AppleScript): Terminal, Chrome, Claude Code subprocess spawning
- `work_mode.py` — Persistent Claude Code session management
- `screen.py` — macOS screen awareness via AppleScript + screencapture
- `calendar_access.py`, `mail_access.py`, `notes_access.py` — macOS AppleScript bridges
- `browser.py` — Playwright web automation for research tasks
- `templates.py` — Build prompt templates by project type

### Frontend (TypeScript + Vite)
- `main.ts` — State machine: idle → listening → processing → speaking
- `orb.ts` — Three.js particle orb that deforms/pulses in response to audio
- `voice.ts` — Web Speech API transcription + audio playback queue
- `ws.ts` — WebSocket connection management
- `settings.ts` — Settings panel UI (API keys, preferences)

### Data
- All local data in `data/jarvis.db` (SQLite with WAL mode)
- Google OAuth token at `data/google_token.json` (Windows only)
- Frontend proxies `/ws` and `/api` to backend via Vite config (port 5173 → 8340)

## Action System
JARVIS responses contain action tags that the server parses and executes:
- `[ACTION:BUILD]` — Spawns Claude Code subprocess to build a project on Desktop
- `[ACTION:BROWSE]` — Opens browser (Chrome via AppleScript on macOS, subprocess on Windows)
- `[ACTION:RESEARCH]` — Deep research using Claude Opus, produces HTML report
- `[ACTION:PROMPT_PROJECT]` — Connects to existing project via Claude Code
- `[ACTION:SCREEN]` — Captures screen state (AppleScript on macOS, pywinauto/mss on Windows)
- `[ACTION:ADD_TASK]`, `[ACTION:ADD_NOTE]`, `[ACTION:REMEMBER]` — Memory/task/note creation

## Conventions
- JARVIS personality: British butler, dry wit, economy of language. Max 1-2 sentences per voice response
- macOS integrations use AppleScript; Windows uses Google APIs + native Windows automation
- Mail is intentionally read-only (safety by design)
- Notes can be created but not edited/deleted
- Don't add external data services beyond Anthropic, Fish Audio, and Google APIs
- Claude Haiku for fast voice responses; Claude Opus for research/complex tasks
- Default build stack when user says "just build it": React + Tailwind

## Environment Variables
- `ANTHROPIC_API_KEY` (required) — Claude API access
- `FISH_API_KEY` (required) — Fish Audio TTS
- `FISH_VOICE_ID` (optional) — Voice model ID (defaults to MCU JARVIS voice)
- `USER_NAME` (optional) — How JARVIS addresses the user (defaults to "sir")
- `CALENDAR_ACCOUNTS` (optional, macOS) — Comma-separated calendar account emails
