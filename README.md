# Later starter kit

Drop this folder into a new repo, open it in Claude Code, and follow the phases in the build guide doc.

```
later/
├── CLAUDE.md                 project brain: goal, rules, architecture
├── .claude/agents/           one file per agent (intake, curator, planner, concierge)
├── memory/taste.md           what agents learn about you (you can edit it)
├── memory/feedback.md        append-only log of what you did or skipped
├── docs/TOOLS.md             spec for the saves MCP server
├── docs/DESIGN.md            UI and visual design spec
├── evals/README.md           how to test the agents
└── .env.example              keys you will need, copy to .env
```

Claude Code will create `backend/`, `app/` and `data/` as you go.

First run:
1. `git init` in this folder.
2. Copy `.env.example` to `.env` and add your Anthropic key.
3. Open Claude Code here and paste the Phase 0 prompt from the guide.
