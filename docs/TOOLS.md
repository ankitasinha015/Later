# Tools spec: the `saves` MCP server

All agents reach data and the outside world only through these tools.
The description of each tool is what the agent reads, so keep descriptions exact.

## Data model: `Save`

| Field | Type | Notes |
| --- | --- | --- |
| id | str | uuid4 (stdlib; ULID needed a dependency and sortability is worthless at single-user scale) |
| source_post_id | str | groups saves that came from the same TikTok post. 84% of real screenshots are several entities from one post, so this is not optional |
| category | enum | see CLAUDE.md |
| name | str | the real-world entity name |
| status | enum | active, needs_review, done, let_go, expired, closed |
| why_saved | str | under 12 words, from caption or overlay |
| creator_handle | str or null | TikTok @handle if visible |
| city, neighborhood | str or null | |
| lat, lng | float or null | places only |
| external_id | str or null | Google place id, Open Library key, TMDB id |
| details | json | hours, author, runtime, etc. from enrichment |
| confidence | float | 0 to 1, from Intake |
| evidence | str | what Intake actually read to decide. Under 30 words |
| expires_on | date or null | events and pop-ups |
| screenshot_ids | list[str] | one save can have several screenshots |
| created_at, last_suggested_at, done_at | datetime | |

## Phase 1 tools (build first)

| Tool | Input | Returns | Notes |
| --- | --- | --- | --- |
| add_screenshot | image bytes, filename | Screenshot | the only way an image enters the system; nothing else created one |
| add_save | Save fields minus id | Save | validates category and status |
| search_saves | query?, category?, status?, city?, near (lat, lng, km)?, limit | list[Save] | text search on name, why_saved, city |
| update_save | id, fields | Save | never deletes |
| get_save | id | Save | |
| get_screenshot | screenshot_id | image | Intake only |

## Phase 2 tools: enrichment

| Tool | Backed by | Returns |
| --- | --- | --- |
| find_place | Google Places API (New), Text Search + Place Details | name, address, lat, lng, hours, open_now, business_status, place_id |
| find_book | Open Library search API | title, authors, year, cover url, key |
| find_title | TMDB search | title, year, type, tmdb id |
| check_watch_providers | TMDB watch providers (US) | list of services |
| web_search | any search API you choose | top 5 results |

## Phase 3 tools: context and memory

| Tool | Backed by | Returns |
| --- | --- | --- |
| check_calendar | Google Calendar API, read | free blocks and events for a date range |
| get_weather | Open-Meteo | hourly forecast for lat, lng, date |
| read_memory | `memory/*.md` | file text |
| update_taste | `memory/taste.md` | rewrites file; refuses if the Autonomy section changed |
| append_feedback | `memory/feedback.md` | appends one line |

## Phase 4 tools: talking and acting

| Tool | Backed by | Notes |
| --- | --- | --- |
| send_message | Telegram Bot API | enforces max one message per day across agents |
| ask_user | Telegram inline buttons | returns immediately; answer arrives as a later event |
| create_calendar_event | Google Calendar API, write | concierge only, needs Yes unless auto-allowed |
| create_trip_list | backend | returns a shareable in-app list |

## Removed 2026-10-15: want_score and link_duplicate

Both assumed the same real-world thing gets screenshotted repeatedly, and that
merging those repeats into one save with a rising score would signal how much
Ankita wants it.

Real saving does not work that way. Screenshots come in groups from a single
post, each capturing a *different* entity: five books from one video, four
venues from one carousel. There are no repeats to merge. Worse, a dedup pass
that keyed on the source post would collapse five distinct books into one save.

The Planner never needed it. Its ranking already runs on calendar free blocks,
weather, `expires_on`, open-now, taste, skip history and geographic grouping.
`want_score` was one boost out of eight.

Intake still avoids creating two rows for the same entity, but that is a check
before insert, not a tool and not a score.

## Rules for writing tools
- Every tool returns JSON with plain field names. Errors return `{"error": "...", "hint": "..."}` so the agent can recover.
- Guardrails live in tools, not only in prompts. Example: the one-message-per-day limit is enforced inside `send_message`.
- Log every tool call (agent, tool, input, ms, ok) to `data/tool_log.jsonl`. This is your debugging and eval trail.
