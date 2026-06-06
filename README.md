@"
# JARVIS2026

Local-first multi-agent desktop assistant inspired by a Jarvis-style command center.

## Goal

Build a free/local AI assistant with:

- Director Agent
- Dev Agent
- CTO Agent
- Business Agent
- Notes Agent
- Local LLM through Ollama
- Local memory with SQLite and Markdown journal
- Desktop UI with animated orb
- Push-to-talk first
- Wake word and clap detection later
- Human approval gates for dangerous tools

## MVP Philosophy

Do not start with 21 agents.

Start with 5 strong agents and a strict orchestrator.

## Main Stack

- Python 3.11+
- uv
- Pydantic v2
- Ollama
- Qwen2.5 models
- PySide6
- SQLite
- faster-whisper
- Piper TTS
- pytest
- ruff
- mypy

## Status

Initial folder structure created.
"@ | Set-Content README.md