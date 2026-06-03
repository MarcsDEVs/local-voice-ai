<div align="center">
  <img src="./frontend/.github/assets/template-light.webp" alt="App Icon" width="80" />
  <h1>Local Voice AI</h1>
  <p>Lightweight voice AI agent that connects to existing OpenAI-compatible services.</p>
  <p>A simplified, containerized AI voice assistant using WebRTC powered by <a href="https://docs.livekit.io/agents?utm_source=local-voice-ai">LiveKit Agents</a>.</p>
</div>

## Overview

This project is a streamlined version that includes:

- **LiveKit** for WebRTC realtime audio + rooms
- **LiveKit Agents (Python)** to orchestrate the STT → LLM → TTS pipeline
- **External OpenAI-compatible APIs** for:
  - Speech-to-text (Nemotron, Whisper, etc.)
  - LLM inference (llama.cpp, Ollama, etc.)
  - Text-to-speech (Kokoro, etc.)
- **Webhook delegation** to route conversations to other agents
- **Next.js + Tailwind** frontend UI
- Fully containerized via Docker Compose

## Quick Start

### 1. Configure your services

Edit `.env` with your service endpoints:

```env
# LiveKit
LIVEKIT_URL=ws://10.0.0.3:7880
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880

# LLM (OpenAI-compatible)
LLAMA_BASE_URL=http://10.0.0.3:8000/v1
LLAMA_MODEL=qwen3-4b

# STT (OpenAI-compatible)
STT_BASE_URL=http://10.0.0.3:8000/v1
STT_MODEL=nemotron-speech-streaming

# TTS (OpenAI-compatible)
TTS_BASE_URL=http://10.0.0.3:8880/v1
TTS_MODEL=kokoro
TTS_VOICE=af_nova

# Webhook (optional - for delegating to another agent)
WEBHOOK_ENABLED=true
WEBHOOK_URL=http://10.0.0.3:5678/webhook/AI-AGI
```

### 2. Start the services

```bash
docker compose up --build
```

### 3. Open the frontend

Visit [http://localhost:3000](http://localhost:3000) in your browser to start chatting.

## Architecture

Each component communicates over a shared Docker network:

- `livekit_agent`: Python agent (LiveKit Agents SDK)
- `frontend`: Next.js client UI

## Configuration

### Environment Variables

- **LIVEKIT_URL**: Internal LiveKit WebSocket URL (e.g., `ws://10.0.0.3:7880`)
- **NEXT_PUBLIC_LIVEKIT_URL**: Browser-accessible LiveKit URL (e.g., `ws://localhost:7880`)
- **LLAMA_BASE_URL**: LLM OpenAI-compatible endpoint
- **LLAMA_MODEL**: Model name/ID
- **STT_BASE_URL**: Speech-to-text OpenAI-compatible endpoint
- **STT_MODEL**: STT model name/ID
- **TTS_BASE_URL**: Text-to-speech OpenAI-compatible endpoint
- **TTS_MODEL**: TTS model name
- **TTS_VOICE**: TTS voice selection
- **WEBHOOK_ENABLED**: Enable webhook delegation
- **WEBHOOK_URL**: Webhook endpoint to delegate conversations

## Agent Features

### Function Tools

The agent has built-in tools:

- **multiply_numbers**: Simple math demonstration
- **delegate_to_agent**: Delegate conversations to another agent via webhook

### Webhook Delegation

Send a request to the agent to delegate to another service:

```python
# In the LLM response, use the delegate_to_agent tool
{
    "tool_call": "delegate_to_agent",
    "params": {
        "reason": "This question requires specialized knowledge"
    }
}
```

The webhook payload includes:

```json
{
    "timestamp": "2024-01-01T12:00:00",
    "reason": "Reason for delegation",
    "conversation_history": [...],
    "room_name": "room_name"
}
```

## Development

Use `.env.local` files in `frontend` and `livekit_agent` dirs for local development:

```bash
# Frontend
cd frontend
pnpm install
pnpm dev

# Agent (in another terminal)
cd livekit_agent
uv sync
uv run python src/agent.py dev
```

## Project Structure

```
.
├─ frontend/        # Next.js UI client
├─ livekit_agent/   # Python voice agent (LiveKit Agents)
├─ docker-compose.yml
└─ .env
```

## Requirements

- Docker + Docker Compose
- External services running (LLM, STT, TTS, LiveKit)
- Recommended: 4GB+ RAM

## Supported OpenAI-compatible Services

### LLM
- llama.cpp
- Ollama
- vLLM
- Any OpenAI-compatible LLM API

### STT
- Nemotron (via FastAPI wrapper)
- Whisper (via VoxBox)
- Any OpenAI-compatible STT API

### TTS
- Kokoro
- Any OpenAI-compatible TTS API

## License

MIT License - see LICENSE file for details
