# AskTo - AI-Powered Voice Sales Agent

## Overview

**AskTo** is an intelligent, voice-enabled AI sales agent platform designed to automate personalized customer conversations. Built on **Pipecat** for real-time voice interaction and **LangGraph** for stateful conversation management, it enables natural sales conversations with memory persistence, user identification, and multi-session continuity.

The platform currently demonstrates a credit card sales use case (HDFC Bank's Swiggy Card) with three distinct conversation modes: **Discovery**, **Pitch**, and **Objection Handling**.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Voice Conversations** | Natural speech-to-text and text-to-speech using Sarvam AI for Indian language support |
| **LangGraph Agent Architecture** | Stateful conversation flow with identity verification, memory retrieval, and profile extraction |
| **Persistent Memory** | Redis for session state + PostgreSQL for long-term user profiles and conversation history |
| **Multi-Session Continuity** | Recognizes returning users and references previous conversations |
| **Token/Coin Quota System** | Built-in usage tracking with configurable limits and real-time frontend updates |
| **Multiple Session Types** | Discovery, Pitch, and Objection Handling modes with specialized prompts |
| **WebRTC Transport** | Low-latency voice communication via Daily.co or SmallWebRTC |
| **Modern UI** | Responsive interface with live transcript, animated orb visualization, and event logs |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  CLIENT                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Next.js   │  │   Pipecat   │  │  Shadcn UI  │  │  Transcript Panel   │ │
│  │  App Router │  │  Client SDK │  │  Components │  │  + Event Logs       │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                                                   │
│         └────────────────┴───────────────┬───────────────────────────────────│
└──────────────────────────────────────────┼───────────────────────────────────┘
                                           │ WebRTC / API
┌──────────────────────────────────────────┼───────────────────────────────────┐
│                                  SERVER  │                                   │
│  ┌───────────────────────────────────────┴───────────────────────────────┐  │
│  │                         Pipecat Pipeline                               │  │
│  │  ┌─────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │ Sarvam  │→ │  LangGraph  │→ │   Sarvam    │→ │ Token Reporter  │   │  │
│  │  │   STT   │  │    Agent    │  │     TTS     │  │                 │   │  │
│  │  └─────────┘  └──────┬──────┘  └─────────────┘  └─────────────────┘   │  │
│  └──────────────────────┼────────────────────────────────────────────────┘  │
│                         │                                                    │
│  ┌──────────────────────┴────────────────────────────────────────────────┐  │
│  │                       LangGraph Workflow                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Identity │→ │ Retrieve │→ │ Generate │→ │ Extract  │→ │  Write   │ │  │
│  │  │   Node   │  │  Memory  │  │ Response │  │ Profile  │  │  Memory  │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                         │                                                    │
│         ┌───────────────┴───────────────┐                                   │
│         ▼                               ▼                                   │
│  ┌─────────────┐                 ┌─────────────┐                            │
│  │    Redis    │                 │  PostgreSQL │                            │
│  │   Session   │                 │   Long-term │                            │
│  │    State    │                 │    Memory   │                            │
│  └─────────────┘                 └─────────────┘                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend (`/client`)

| Technology | Purpose |
|------------|---------|
| Next.js 16 | React framework with App Router |
| Tailwind CSS | Utility-first styling |
| Shadcn UI | Component library |
| Pipecat Client SDK | Voice/WebRTC integration |
| Lucide React | Icon library |

### Backend (`/server`)

| Technology | Purpose |
|------------|---------|
| Pipecat SDK | Voice pipeline framework |
| LangGraph | Stateful AI agent workflow |
| Sarvam AI | Indian language STT/TTS |
| OpenRouter | LLM gateway (GPT-4, Claude, etc.) |
| Daily.co / SmallWebRTC | Real-time voice transport |

### Data Layer

| Technology | Purpose |
|------------|---------|
| PostgreSQL | User profiles, sessions, conversation history |
| Redis | Session state, message cache, real-time data |
| SQLAlchemy | ORM for PostgreSQL |

---

## Session Types

The agent supports three conversation modes, each with specialized prompts and goals:

### 1. Discovery Session
- Build rapport with the customer
- Understand their lifestyle and spending habits
- Identify pain points with current cards
- Determine if they're a good fit for the product

### 2. Pitch Session
- Present personalized value proposition
- Use customer's specific data to show savings
- Guide toward application decision

### 3. Objection Handling
- Address concerns and hesitations
- Provide clarifications on fees, benefits
- Maintain rapport while being persuasive

---

## Setup & Installation

### Prerequisites

- Node.js v18+
- Python 3.10+
- PostgreSQL instance
- Redis instance
- Daily.co account (for WebRTC)
- Sarvam AI API key
- OpenRouter API key

### 1. Client Setup

```bash
cd client
pnpm install
```

Create `.env` in `client/`:

```env
BOT_START_URL=""
NEXT_PUBLIC_BOT_NAME="Sales Agent"
NEXT_PUBLIC_API_URL=""
MONGO_URI=
```

Start the development server:

```bash
pnpm dev
```

Client runs at `http://localhost:3000`

### 2. Server Setup

```bash
cd server
```

**Option A: Using uv (recommended)**
```bash
uv run bot.py
```

**Option B: Using pip**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Create `.env` in `server/`:

```env
# Transport
DAILY_API_KEY=
DAILY_SAMPLE_ROOM_URL=

# Sarvam AI (STT/TTS)
SARVAM_API_KEY=
SARVAM_STT_MODEL=saarika:v2.5
SARVAM_TTS_MODEL=bulbul:v2
SARVAM_VOICE_ID=

# LLM
OPENROUTER_API_KEY=
OPENROUTER_MODEL=

# Memory
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/askto_memory

# Quota Configuration
MAX_TOKENS=10000
MAX_COINS=10
```

Server runs at `http://localhost:7860`

### 3. Database Setup

Start PostgreSQL and Redis using Docker:

```bash
cd server
docker-compose up -d
```

This creates the required tables automatically via `init.sql`.

---

## Project Structure

```
askto/
├── client/                          # Next.js Frontend
│   ├── src/
│   │   ├── app/                     # App Router pages & API routes
│   │   │   ├── api/                 # Backend API endpoints
│   │   │   │   ├── config/          # Bot configuration
│   │   │   │   ├── decode-token/    # JWT verification
│   │   │   │   ├── interview/save/  # Save session data
│   │   │   │   └── start/           # Start bot session
│   │   │   └── page.tsx             # Main page
│   │   ├── components/
│   │   │   ├── app/                 # Core app components
│   │   │   │   ├── animated-orb.tsx # Voice visualization
│   │   │   │   ├── transcript-panel.tsx
│   │   │   │   └── event-log.tsx
│   │   │   ├── ui/                  # Shadcn components
│   │   │   └── App.tsx              # Main app component
│   │   ├── hooks/                   # Custom React hooks
│   │   └── lib/                     # Utilities
│   └── package.json
│
├── server/                          # Python Bot Server
│   ├── agent/                       # LangGraph Agent
│   │   ├── graph.py                 # Main workflow definition
│   │   ├── llm_service.py           # Pipecat LLM integration
│   │   ├── state.py                 # Agent state definition
│   │   ├── nodes/                   # Graph nodes
│   │   │   ├── identity_node.py     # User identification
│   │   │   ├── memory_retriever.py  # Fetch user context
│   │   │   ├── response_node.py     # Generate response
│   │   │   ├── profile_extractor.py # Extract user info
│   │   │   └── memory_writer.py     # Persist to memory
│   │   ├── memory/                  # Memory layer
│   │   │   ├── postgres_client.py   # Long-term storage
│   │   │   └── redis_client.py      # Session state
│   │   └── prompts/                 # Session-specific prompts
│   │       ├── discovery_prompt.py
│   │       ├── pitch_prompt.py
│   │       └── objection_prompt.py
│   ├── bot.py                       # Main entry point
│   ├── docker-compose.yml           # Redis + PostgreSQL
│   ├── init.sql                     # Database schema
│   └── pyproject.toml               # Python dependencies
│
└── README.md
```

---

## API Endpoints

### Client API Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/start` | POST | Start a new bot session |
| `/api/config` | GET | Get token/coin configuration |
| `/api/decode-token` | POST | Verify JWT token |
| `/api/interview/save` | POST | Save session transcript |

### Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/start` | POST | Pipecat session start (WebRTC) |
| `/config` | GET | Bot configuration |

---

## Real-time Communication

The platform uses WebRTC for low-latency voice communication:

1. **Session Start**: Client requests a new session via `/api/start`
2. **WebRTC Setup**: Daily.co or SmallWebRTC transport is established
3. **Voice Pipeline**: Audio flows through STT → LLM → TTS
4. **State Updates**: Token usage and events sent via `rtvi.send_server_message()`

---

## Token Quota System

The platform includes a built-in usage quota system:

- **MAX_TOKENS**: Total tokens allowed per session
- **MAX_COINS**: User-facing quota units
- **Tokens per Coin**: `MAX_TOKENS / MAX_COINS`

When tokens are exhausted, the session ends gracefully with a notification dialog.

---

## Development

### Running Locally

1. Start databases: `cd server && docker-compose up -d`
2. Start server: `cd server && uv run bot.py`
3. Start client: `cd client && pnpm dev`

### Environment Variables

See the `.env` examples above for required configuration.
