# Backend Knowledge Base

## OVERVIEW
Python backend with agents and API for stock trading platform.

## STRUCTURE
```
backend/
├── app/
│   ├── agents/        # AI agents for analysis
│   └── services/      # Business services
├── entrypoints/
│   ├── api/           # API server and routers
│   └── cli/           # CLI tools
├── infrastructure/
├── tests/             # Unit tests
└── ...
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add agent | app/agents/ | Create new agent module |
| API endpoint | entrypoints/api/routers/ | Add router |
| Test | tests/ | Add unit test |

## CONVENTIONS
Follow project lint and format rules.

## ANTI-PATTERNS
No traffic amplification, prefer batch APIs.