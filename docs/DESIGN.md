# Design spec: Later

## Feeling
A field notebook, not a dashboard. Warm paper, ink, little colored stamps for each category.
Calm, personal, a bit editorial. The agents feel like a thoughtful friend leaving notes, not a feed.

## Principles
1. The screenshot is the hero. Always show the original image next to what the AI understood.
2. Every agent suggestion shows its reason in one line ("You saved this twice. Open till 6.").
3. One primary action per screen. Everything else is quiet.
4. Done is a celebration. Marking something done gets a small stamp animation.
5. Works one-handed on a phone. Web layout is the phone layout, centered, max width 480px, until iOS.

## Visual system

### Color (light / dark)
| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| paper | #FAF7F2 | #171513 | background |
| card | #FFFFFF | #221F1C | cards |
| ink | #1F1B16 | #F2EDE6 | primary text |
| ink-muted | #6B6359 | #A8A096 | secondary text |
| line | #E7E1D8 | #34302B | borders, dividers |
| accent | #D9572B | #F07A4F | the one action color (terracotta) |

Category stamps (fill at 12% opacity, text at full):
| Category | Color |
| --- | --- |
| book | #3E6FB0 indigo |
| article | #5B6B8C slate |
| place_food | #C0702A amber |
| place_shop | #9B4D8A plum |
| place_other | #4C8B5A sage |
| travel_city | #2F8C8C teal |
| video | #B23A48 cherry |
| recipe | #7A8C2F olive |
| event | #D9572B terracotta |

### Type
- Display and save names: Fraunces (serif), 600, sizes 28 / 22 / 18.
- UI and body: Inter, 400 and 600, sizes 16 / 14 / 12.
- Never more than 3 sizes on one screen.

### Shape and motion
- Card radius 16. Chip radius 999. Spacing scale 4, 8, 12, 16, 24, 32.
- Thin borders (1px line color), no heavy shadows.
- Motion: 200ms ease-out. Stamp animation on Done (scale 1.2 to 1, slight rotate).
- Respect reduced motion.

### Icons
Lucide icons, 1.5px stroke.

## Navigation
Bottom tab bar with 4 tabs: Today, Library, Map, Ask.
Inbox (agent questions) is a badge on Today. Agents settings live behind the profile icon on Today.

## Screens

### 1. Today (home)
- Header: greeting and date. Profile icon top right.
- Inbox banner if agents have questions: "Intake has 2 quick questions".
- "This weekend" card from the Planner: up to 3 picks, each with photo, name, when, reason line, and buttons Go / Not this time.
- "Ending soon" row: saves with expires_on within 10 days.
- "Upcoming trip" card if a trip is on the calendar: city, days away, count of saves, Open list.
- Empty state: "Share a screenshot to Later to get started." with a how-to.

### 2. Library
- Search bar at top.
- Category chips (scrollable): All, Books, Reads, Food, Shops, Places, Travel, Videos, Recipes, Events.
- Filters: city, status (Active default, Done, Let go, Gone). Gone covers `expired` and `closed`, which the Curator sets on Sundays. `needs_review` does not appear here; it surfaces in the Inbox.
- Masonry grid of screenshot thumbnails, each with the category stamp and name below.
- Long press: quick actions Done, Let go.

### 3. Save detail
- Top: the original screenshot (tap for full screen; swipe if several).
- "Later understood": name in Fraunces, category stamp, city, confidence badge only if below 0.8.
- Enriched block by category: hours and open now plus mini map (places); author, cover and year (books); where to watch (videos).
- "Why you saved it": why_saved line and @creator.
- Saved N times, first saved on date.
- Actions: primary depends on category (Directions, Find at library, Watch), then Done, Let go, Add to calendar.

### 4. Map
- Full-screen map of active place saves, pins colored by category.
- Toggle: Open now. Bottom sheet list of what is in view, sorted by distance.

### 5. Ask
- Chat with the Concierge. Suggested prompts as chips: "Plan my Saturday", "What books am I sitting on?", "Cafes near me".
- Results render as save cards inside the chat, not plain text.
- Action confirmations render as a card with Yes / No.

### 6. Inbox
- One card per agent question. The screenshot, the question, and 2 to 4 answer buttons.
- Done in one tap each.

### 7. Agents (settings)
- One row per agent: name, what it does, last run time, last result line, Run now button.
- Autonomy: switches that write the "OK to auto-" lines in memory/taste.md. Each switch explains what it allows.
- "What Later knows about you": renders taste.md, editable.
- Activity log: recent tool calls, for debugging.

## Accessibility
- Contrast 4.5:1 for text. Category is never shown by color alone (stamp has a label).
- Tap targets at least 44 by 44.
- Dynamic type supported on iOS.
