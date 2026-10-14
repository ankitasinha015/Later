# Tools spec: the `saves` MCP server

All agents reach data and the outside world only through these tools.
The description of each tool is what the agent reads, so keep descriptions exact.

## Data model: `Save`

| Field | Type | Notes |
| --- | --- | --- |
| id | str | ULID |
| category | enum | see CLAUDE.md |
| name | str | the real-world entity name |
| status | enum | active, needs_review, done, let_go, expired, closed |
| why_saved | str | under 12 words, from caption or overlay |
| creator_handle | str or null | TikTok @handle if visible |
| city, neighborhood | str or null | |
| lat, lng | float or null | places only |
| external_id | str or null | Google place id, Open Library key, TMDB id |
| details | json | hours, author, runtime, etc. from enrichment |
| want_score | int | 1 + number of duplicates merged |
| confidence | float | 0 to 1, from Intake |
| expires_on | date or null | events and pop-ups |
| screenshot_ids | list[str] | one save can have several screenshots |
| created_at, last_suggested_at, done_at | datetime | |

## Phase 1 tools (build first)

| Tool | Input | Returns | Notes |
| --- | --- | --- | --- |
| add_save | Save fields minus id | Save | validates category and status |
| search_saves | query?, category?, status?, city?, near (lat, lng, km)?, limit | list[Save] | text search on name, why_saved, city |
| update_save | id, fields | Save | never deletes |
| get_save | id | Save | |
| get_screenshot | screenshot_id | image | Intake only |
| link_duplicate | save_id, screenshot_id | Save | adds screenshot, +1 want_score |

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

## Rules for writing tools
- Every tool returns JSON with plain field names. Errors return `{"error": "...", "hint": "..."}` so the agent can recover.
- Guardrails live in tools, not only in prompts. Example: the one-message-per-day limit is enforced inside `send_message`.
- Log every tool call (agent, tool, input, ms, ok) to `data/tool_log.jsonl`. This is your debugging and eval trail.
