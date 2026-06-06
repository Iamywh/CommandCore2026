# JARVIS2026 - Local Multi-Agent Research Summary

## Goal

Build a local-first desktop AI assistant inspired by a Jarvis-style command center.

The system must run by default with free/local/open-source tools, without paid APIs.

The assistant will start with 5 agents:

1. Director Agent
2. Dev Agent
3. CTO Agent
4. Business Agent
5. Notes Agent

The goal is not to create 21 agents immediately. The goal is to create a stable, safe, extensible core.

---

## Recommended MVP Stack

### Main language

Python 3.11+

### Project management

uv

### Code quality

- pytest
- pytest-asyncio
- ruff
- mypy
- pre-commit

### Local LLM runtime

Ollama

### Default local models

General reasoning:

- qwen2.5:7b

Coding:

- qwen2.5-coder:7b

### Speech-to-text

Start with:

- faster-whisper

Alternative:

- Vosk for lighter command-based STT

### Text-to-speech

Start with:

- Piper

Fallback:

- pyttsx3

### UI

Start with:

- PySide6

Future option:

- Electron + React
- Tauri + React

### Memory

Start with:

- SQLite
- Markdown journal
- JSONL logs

Future option:

- Chroma
- FAISS

---

## Core Architecture

The assistant must follow this structure:

User input
↓
Activation layer
↓
Speech-to-text or text input
↓
Director Agent
↓
Specialized agents
↓
Tool layer
↓
Memory layer
↓
Final response
↓
Text-to-speech and UI update

The Director Agent is the only agent allowed to delegate tasks.

Specialist agents must not talk freely to each other.

All inter-agent communication must use structured JSON envelopes validated with Pydantic.

---

## MVP Agents

### Director Agent

Responsibilities:

- understand user request
- classify intent
- decide which agent should work
- delegate tasks
- collect agent results
- produce final response
- request human approval when tools are dangerous

The Director does not directly execute shell, git, browser, or filesystem actions.

---

### Dev Agent

Responsibilities:

- analyze code
- create implementation plans
- modify files inside allowed workspace
- inspect git status and diffs
- run safe tests
- suggest commits

Requires approval for:

- deleting files
- git commits
- shell commands with side effects
- modifying files outside workspace

---

### CTO Agent

Responsibilities:

- architecture decisions
- technical tradeoffs
- risk analysis
- scalability
- maintainability
- security review

---

### Business Agent

Responsibilities:

- business impact
- priorities
- roadmap
- client-facing summary
- practical next actions

Useful later for OperaCore, Menuria, Nonna Angela and client projects.

---

### Notes Agent

Responsibilities:

- summarize decisions
- save progress
- update local memory
- create markdown reports
- maintain daily project journal

---

## Security Rules

The assistant must be safe by default.

Dangerous tools require human approval.

Safe actions:

- read files inside workspace
- git status
- git diff
- memory read
- notes read

Approval required:

- write files
- delete files
- run shell commands
- git commit
- git push
- browser automation
- reading sensitive files

Denied by default:

- deleting folders recursively
- exposing secrets
- reading .env without explicit approval
- running commands outside workspace
- executing unknown scripts
- sending data to cloud APIs without user approval

---

## Memory Strategy

Use SQLite as canonical memory.

Use markdown or JSONL journal for human-readable records.

Memory types:

- decisions
- daily summaries
- project status
- agent outputs
- errors
- approved actions
- rejected actions
- tool calls

---

## UI Requirements

The desktop app must include:

- animated orb
- status label
- transcript panel
- active agent panel
- tool call panel
- push-to-talk button
- final answer panel

Orb states:

- idle
- listening
- thinking
- speaking
- error

---

## Voice Strategy

MVP starts with push-to-talk.

Wake word and clap detection come later.

Reason:

wake word and clap detection can trigger false activations.

No dangerous tool should ever run automatically after wake detection.

---

## Future Features

After MVP:

- wake word
- double clap detection
- GitHub integration
- Codex prompt generation
- local project indexing
- vector memory
- calendar tools
- email tools
- browser automation
- more agents
- OperaCore command center mode

---

## Development Philosophy

Do not overbuild.

Do not start with 21 agents.

Build a strong core with 5 agents first.

Every component must be modular and replaceable.

The project must run locally by default.

External APIs are optional, never required.

The system must degrade gracefully if Ollama, STT, TTS or optional tools are missing.