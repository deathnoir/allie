# JARVIS — Technical Specification

## What It Is
A voice-first AI assistant with a browser-based UI. Users speak naturally, JARVIS responds with voice (British butler persona). It can read calendars/email, browse the web, manage tasks, see the user's screen, and spawn Claude Code sessions to build software projects.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (Chrome)                                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Web Speech   │  │ Three.js Orb │  │ AudioContext   │ │
│  │ API (STT)    │  │ (WebGL)      │  │ (TTS playback) │ │
│  └──────┬───────┘  └──────────────┘  └───────▲────────┘ │
│         │ transcript                         │ audio     │
│         ▼                                    │           │
│  ┌──────────────────────────────────────────────────┐   │
│  │              WebSocket (JSON + binary)            │   │
│  └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Server (Python, single process)                 │
│                                                          │
│  ┌──────────┐  ┌───────────┐  ┌───────────────────────┐│
│  │ Voice    │  │ Action    │  │ Platform Abstraction   ││
│  │ Handler  │  │ Dispatcher│  │ (jarvis_platform/)     ││
│  │          │  │           │  │                        ││
│  │ Receives │  │ Parses    │  │ macOS: AppleScript     ││
│  │ text,    │  │ [ACTION:] │  │ Windows: pywinauto,    ││
│  │ calls    │  │ tags from │  │   Google APIs, mss     ││
│  │ Claude,  │  │ LLM       │  │                        ││
│  │ returns  │  │ response  │  │ Terminal, Browser,     ││
│  │ audio    │  │           │  │ Screen, Calendar,      ││
│  └────┬─────┘  └─────┬─────┘  │ Mail, Notes           ││
│       │               │        └───────────────────────┘│
│       ▼               ▼                                  │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────────┐│
│  │ Anthropic│  │ Claude Code│  │ SQLite (jarvis.db)    ││
│  │ API      │  │ CLI (-p)   │  │ Memory, Tasks, Notes, ││
│  │ (Haiku)  │  │ subprocess │  │ Dispatches, Tracking  ││
│  └──────────┘  └────────────┘  └──────────────────────┘│
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │ Fish     │                                           │
│  │ Audio    │                                           │
│  │ TTS API  │                                           │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | TypeScript + Vite | Build tooling |
| | Three.js | Audio-reactive 3D particle orb |
| | Web Speech API | Browser-native speech-to-text |
| | AudioContext (Web Audio) | TTS audio playback |
| | WebSocket | Real-time bidirectional comms |
| **Backend** | Python 3.11+ | Runtime |
| | FastAPI + Uvicorn | HTTP/WebSocket server |
| | Anthropic SDK | Claude API calls |
| | httpx | HTTP client (TTS calls) |
| | Playwright | Web automation (research) |
| | SQLite (WAL mode) | All local persistence |
| **AI** | Claude Haiku | Low-latency voice responses |
| | Claude Opus | Deep research tasks |
| | Claude Code CLI | Software build tasks (subprocess) |
| **TTS** | Fish Audio API | Text-to-speech with custom voice |
| **Platform (macOS)** | AppleScript | Calendar, Mail, Notes, Terminal |
| **Platform (Windows)** | pywinauto + pywin32 | Terminal/window automation |
| | mss + Pillow | Screenshot capture |
| | Google Calendar API | Calendar (OAuth) |
| | Gmail API | Email read-only (OAuth) |

## External API Dependencies

| Service | Purpose | Auth | Required |
|---------|---------|------|----------|
| Anthropic API | LLM (voice conversation) | API key | Yes |
| Fish Audio | Text-to-speech | API key | Yes (for voice) |
| Google Calendar API | Calendar on Windows | OAuth 2.0 | No (Windows only) |
| Gmail API | Email on Windows | OAuth 2.0 | No (Windows only) |

## Communication Protocol

**WebSocket** at `/ws/voice` — JSON messages + binary audio frames:

```
Client -> Server:
  { type: "transcript", text: "...", isFinal: true }
  { type: "fix_self" }

Server -> Client:
  { type: "audio", data: "<base64 MP3>", text: "..." }
  { type: "status", state: "thinking"|"speaking"|"idle"|"working" }
  { type: "text", text: "..." }
  { type: "task_spawned", task_id: "...", prompt: "..." }
  { type: "task_complete", task_id: "...", status: "...", summary: "..." }
```

## REST API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/projects` | List scanned projects |
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create a task |
| PATCH | `/api/tasks/{id}` | Update/complete a task |
| GET | `/api/settings` | Get current settings |
| POST | `/api/settings` | Save settings to .env |
| GET | `/api/settings/status` | Service connectivity check |
| POST | `/api/restart` | Restart the server |
| POST | `/api/fix-self` | Open Claude Code in JARVIS repo |

## Data Storage

Single SQLite database at `data/jarvis.db`:

| Table | Purpose |
|-------|---------|
| `memories` | Facts, preferences, decisions (FTS5 searchable) |
| `tasks` | To-do items with priority, due date, project |
| `notes` | Freeform notes tied to topics |
| `dispatches` | Claude Code build tracking |
| `task_log` | Success/failure tracking |
| `usage_patterns` | Action type frequency |
| `suggestions` | Follow-up suggestions |

## Action System

The LLM embeds action tags in responses. The server parses and executes them:

| Tag | What It Does |
|-----|-------------|
| `[ACTION:BUILD] description` | Create project dir, spawn Claude Code |
| `[ACTION:BROWSE] url` | Open browser |
| `[ACTION:RESEARCH] brief` | Deep research with Opus, HTML report |
| `[ACTION:PROMPT_PROJECT] name \|\|\| prompt` | Send prompt to existing project via Claude Code |
| `[ACTION:SCREEN]` | Capture/describe screen |
| `[ACTION:OPEN_TERMINAL]` | Open fresh terminal |
| `[ACTION:ADD_TASK] priority \|\|\| title \|\|\| desc \|\|\| due` | Create task |
| `[ACTION:ADD_NOTE] topic \|\|\| content` | Create note |
| `[ACTION:REMEMBER] fact` | Store a memory |

## Key Design Constraints

- Voice responses: 1-2 sentences max, no markdown
- Mail: **read-only** by design (safety)
- Notes: create only, no edit/delete
- All data local (SQLite), no external DB
- Single-user, single-process, runs locally
- JARVIS personality must be maintained (British butler, dry wit)

## File Structure

```
server.py              # Main server (~2400 lines): WebSocket, LLM, actions, TTS
jarvis_platform/       # Platform abstraction layer
  __init__.py          # Platform detection (darwin/win32)
  base.py              # Abstract interfaces
  darwin.py            # macOS wrapper (AppleScript)
  google_auth.py       # Google OAuth flow
  google_services.py   # Google Calendar + Gmail clients
  win32/               # Windows implementations
    terminal.py        # Windows Terminal + pywinauto
    browser.py         # Browser + Explorer
    screen.py          # mss screenshots + window enum
    calendar.py        # Google Calendar async wrappers
    mail.py            # Gmail async wrappers
    notes.py           # Local SQLite notes
memory.py              # SQLite memory/tasks/notes
actions.py             # macOS action execution
screen.py              # macOS screen capture
calendar_access.py     # macOS Apple Calendar
mail_access.py         # macOS Apple Mail
notes_access.py        # macOS Apple Notes
planner.py             # Build planning + clarifying questions
conversation.py        # Multi-turn session state
dispatch_registry.py   # Build dispatch tracking
work_mode.py           # Persistent Claude Code sessions
browser.py             # Playwright web automation
templates.py           # Build prompt templates
tracking.py            # Success/usage analytics
learning.py            # Usage pattern learning
evolution.py           # Template auto-improvement
ab_testing.py          # A/B testing for prompts
qa.py                  # QA verification agent
suggestions.py         # Proactive follow-up suggestions
monitor.py             # Conversation quality monitoring
frontend/src/
  main.ts              # State machine + wiring
  orb.ts               # Three.js particle orb
  voice.ts             # Web Speech API + audio playback
  ws.ts                # WebSocket client
  settings.ts          # Settings panel UI
```

## Cloud Deployment Considerations

### Current blockers for cloud:
1. **Speech-to-text** runs in the browser (Web Speech API) — works anywhere, no change needed
2. **TTS** calls Fish Audio API — works from cloud, no change needed
3. **LLM** calls Anthropic API — works from cloud, no change needed
4. **Screen capture** — only works locally (sees user's desktop)
5. **Terminal automation** — only works locally (opens windows)
6. **Calendar/Mail** — macOS: requires local AppleScript. Windows: Google APIs work from anywhere
7. **Claude Code CLI** — requires local installation
8. **SQLite** — works on cloud but needs persistent volume

### What would work from cloud as-is:
- Voice conversation loop (STT -> LLM -> TTS -> audio)
- Task/memory management
- Calendar/Mail via Google APIs
- Web research via Playwright

### What requires local machine:
- Screen awareness
- Terminal/browser automation
- Claude Code build dispatching

### Possible cloud architecture:
- Deploy the server to a VM/container with persistent storage
- Keep a local agent on the user's machine for screen/terminal actions
- Server <-> Local agent communication via WebSocket or API
