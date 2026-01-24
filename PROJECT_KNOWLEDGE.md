# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-23
**Commit:** 19de3ea
**Branch:** main

## OVERVIEW
AI Stock Trading Platform with Python backend, TypeScript frontend, and memory system.

## STRUCTURE
```
stock-trading-platform/
├── backend/          # Python backend with agents and API
├── frontendV2/       # TypeScript/React frontend
├── memory_system/    # Independent cognitive storage layer
├── skills/           # Tool skills for market data, etc.
├── agent/            # Agent core
├── specs/            # Specifications
├── assets/           # Images and docs
└── README.md         # Project readme
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| API endpoints | backend/entrypoints/api/ | Routers and servers |
| Frontend pages | frontendV2/src/pages/ | UI components |
| Agents | backend/app/agents/ | Personal finance, news sentiment |
| Tests | backend/tests/ | Unit tests |
| Config | .config.yaml | API keys |

## CODE MAP
No LSP available, skipped.

## CONVENTIONS
- Code verification: Only lint and format
- No running tests or services by agents
- Document-first principle for non-fix tasks

## ANTI-PATTERNS (THIS PROJECT)
- Running tests or starting services
- Skipping context gathering
- No pre-execution without confirmation

## UNIQUE STYLES
- AI-generated code
- Multi-agent paradigms (ReAct, debate, master-sub)
- Memory system with triple layers

## COMMANDS
```bash
pip install -r requirements.txt
cp .config.yaml.example .config.yaml
python -m backend.entrypoints.api.server
cd frontendV2 && npm install && npm run dev
```

## NOTES
- Requires VPN for data sources in some regions
- Experimental AI features