# JARVIS2026 Folder Structure

```text
JARVIS2026/
│
├─ app/
│  ├─ core/
│  ├─ services/
│  ├─ security/
│  ├─ main.py
│  ├─ settings.py
│  ├─ schemas.py
│  ├─ orchestrator.py
│  ├─ events.py
│  ├─ approvals.py
│  └─ bus.py
│
├─ agents/
│  ├─ director/
│  │  ├─ instructions.md
│  │  └─ config.json
│  ├─ dev/
│  │  ├─ instructions.md
│  │  └─ config.json
│  ├─ cto/
│  │  ├─ instructions.md
│  │  └─ config.json
│  ├─ business/
│  │  ├─ instructions.md
│  │  └─ config.json
│  └─ notes/
│     ├─ instructions.md
│     └─ config.json
│
├─ providers/
│  ├─ llm/
│  ├─ stt/
│  ├─ tts/
│  └─ wake/
│
├─ tools/
├─ memory/
├─ ui/
├─ tests/
├─ scripts/
├─ docs/
├─ workspace/
├─ logs/
├─ config/
│
├─ README.md
├─ ARCHITECTURE.md
├─ ROADMAP.md
├─ SECURITY.md
├─ .env.example
├─ .gitignore
└─ pyproject.toml