# Later

A personal app where AI agents turn my TikTok screenshots into things I actually do.
Books, cafes, shops, travel, videos, recipes, events.

## Goal
Help Ankita actually do one saved thing a week, without nagging.

## Success
- At least 4 saved things done per month (counted from "Did you go?" taps).
- Intake hits the targets in `evals/README.md` (category 95%, name 90% fuzzy). That file is the single source of truth for accuracy.
- Never more than one nudge per day.

## Who it's for
One person: Ankita, SF Bay Area. Not multi-user. No auth beyond a single API token in v1.

## How Claude should work in this repo
- I am learning. Before writing a new module, explain the plan in 3 to 5 lines and the main tradeoff. Then build it.
- Keep each change small and runnable. After each step, tell me how to run and test it.
- Write tests for tools and data logic. Agents are tested with the eval set in `evals/`.
- Plain, readable code over clever code. Type hints everywhere in Python. TypeScript strict mode in the app.
- Never hardcode API keys. Read them from `.env` (see `.env.example`).
- Ask before adding a new dependency.

## Architecture (API-first)
- `backend/` Python 3.12, FastAPI, SQLModel on SQLite (`data/later.db`), images in `data/images/`.
- `backend/mcp_server/` the `saves` MCP server. All agents use these tools. Spec: `docs/TOOLS.md`.
- `backend/agents/` runners that load `.claude/agents/*.md` with the Claude Agent SDK.
- `backend/scheduler.py` APScheduler: Curator Sunday 8:00, Planner Friday 9:00 (America/Los_Angeles).
- `backend/telegram_bot.py` two-way chat with the Concierge, plus outgoing nudges.
- `app/` Expo (React Native) + Expo Router + TypeScript. Runs on web now, iOS later. Design spec: `docs/DESIGN.md`.

## The agents
| Agent | File | Trigger | Default autonomy |
| --- | --- | --- | --- |
| Intake | `.claude/agents/intake.md` | New screenshot | Acts alone on saves data |
| Curator | `.claude/agents/curator.md` | Sunday 8:00 | Suggest |
| Planner | `.claude/agents/planner.md` | Friday 9:00 | Suggest |
| Concierge | `.claude/agents/concierge.md` | My message | Act with my OK |

Agents never call each other. They share tools and memory.

## Memory
- `memory/taste.md` what agents have learned about me. Plain text. I can edit it.
- `memory/feedback.md` append-only log of what I did, skipped, or said.
- Agents read both before deciding. Only Curator rewrites `taste.md`. Any agent may append to `feedback.md`.

## Autonomy ladder
1. Suggest: tell me.
2. Prepare: get it ready (draft calendar event), I finish it.
3. Act with OK: ask, then do it on "yes".
4. Act alone: only where `memory/taste.md` has an explicit "OK to auto-..." line.

## Rules for all agents
- Max one outgoing message per day across all agents. Planner has priority on Friday, Curator on Sunday.
- Max 3 suggestions per message. Each gets one line on why it fits. (Was 4 here and 3 in `planner.md`; resolved to 3, the stricter of the two.)
- If unsure what a screenshot is, ask me one short question. Never guess silently.
- Never spend money, book, or reserve anything paid.
- Silence beats a bad suggestion.

## Categories
book, place_food (cafe, restaurant, bar, bakery), place_shop, place_other (park, museum, viewpoint, national park), travel_city, video (movie, show), recipe, event

Ambiguous screenshots go to `needs_review`, never to a catch-all category. `product` and `other` were dropped 2026-10-15: `DESIGN.md` had no stamp colour for either, and a wrong save is worse than a `needs_review` save.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
