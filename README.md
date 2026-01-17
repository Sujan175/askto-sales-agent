# AskTo

## 🛠️ Tech Stack

### Client (`/client`)

- **Framework**: Next.js 16 (App Router)
- **Styling**: Tailwind CSS, Shadcn UI
- **State Management**: React Hooks
- **Voice/Video**: Pipecat Client SDK (`@pipecat-ai/client-js`, `@pipecat-ai/voice-ui-kit`)

### Server (`/server`)

- **Runtime**: Python
- **Framework**: Pipecat SDK
- **AI Services**: OpenAI (LLM & TTS), Deepgram (STT), Cartesia (TTS)
- **Transport**: Daily.co / WebRTC

### Database

- **Database**: MongoDB (via `mongodb` driver)

## ⚙️ Setup & Installation

### Prerequisites

- Node.js (v18+)
- Python (v3.10+)
- MongoDB instance
- Daily.co account (for WebRTC transport)
- OpenAI / Deepgram / Cartesia API keys

### 1. Client Setup

Navigate to the client directory:

```bash
cd client
```

Install dependencies:

```bash
pnpm install
```

Create a `.env` file in `client/`:

```env
BOT_START_URL=""

# For Pipecat Cloud (replace {agentName} with your agent name):
# BOT_START_URL="https://api.pipecat.daily.co/v1/public/{agentName}/start"
# BOT_START_PUBLIC_API_KEY="your-pipecat-cloud-public-api-key-here"

# Bot Configuration
NEXT_PUBLIC_BOT_NAME="AI Interviewer"

NEXT_PUBLIC_API_URL=""
# JWT_SECRET_KEY=""

MONGO_URI=
```

Run the development server:

```bash
pnpm dev
```

The client will be available at `http://localhost:3000`.

### 2. Server Setup

Navigate to the server directory:

```bash
cd server
```

Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in `server/`:

```env
# askto - Environment Variables
# Copy this file to .env and fill in your API keys

# Daily (Transport)
DAILY_API_KEY=
DAILY_SAMPLE_ROOM_URL=  # Optional: leave empty to create a new room

# ElevenLabs (STT/TTS)
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

OPENROUTER_API_KEY=
OPENROUTER_MODEL=

# Token and Coin Quota Configuration
MAX_TOKENS=1000  # Maximum tokens allowed per session
MAX_COINS=4 # Maximum coins available per session
MONGO_URI=
SARVAM_API_KEY=
SARVAM_STT_MODEL=
SARVAM_TTS_MODEL=
SARVAM_VOICE_ID=
```

Run the bot server:

```bash
python bot.py
```

The server will run on `http://localhost:7860`.

## 🔐 Authentication Flow

1.  **Token Generation**: An external service (or the `/decode` page) generates a JWT containing user and job details.
2.  **Verification**: The client verifies the token on mount via `/api/decode-token`.
3.  **Session Start**: When starting an interview, the token is passed to `/api/start` for validation before connecting to the bot.

## 📂 Project Structure

```
askto/
├── client/                 # Next.js Frontend
│   ├── src/app/            # App Router pages
│   ├── src/components/     # React components
│   ├── src/lib/            # Utilities (Auth, DB, etc.)
│   └── ...
├── server/                 # Python Bot Server
│   ├── bot.py              # Main bot entry point
│   └── ...
└── README.md               # Project Documentation
```
