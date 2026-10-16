# Feedback log

Append-only. One line per event, newest at the bottom.
Format: `YYYY-MM-DD | agent | save_id or - | event | note`
Events: suggested, went, skipped, kept, let_go, said, no_fit
Note field may carry `trigger=` to record what prompted a suggestion:
`friday_message`, `opened_app`, or `was_nearby`.
Example: `2026-10-23 | planner-manual | - | suggested | trigger=friday_message; Stonemill Matcha, open till 6`

2026-10-14 | setup | - | said | Log created.
