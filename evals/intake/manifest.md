# Intake eval set manifest

The images themselves are gitignored (they are personal TikTok screenshots and
this repo is public). This manifest records what is in the set so the labels in
`expected.jsonl` can be reviewed without the images.

Collected 2026-10-15. **19 of a target 30.**

## Source posts

The headline finding: **19 screenshots are only 7 posts, and 84% of them come
from a post capturing several different entities.** In every multi-entity case
the frames hold *different* things, not the same thing twice. Grouping was
confirmed by identical engagement counts within each set.

| Source post | Images | Entities captured |
| --- | --- | --- |
| `fiobros-reading` | 011–015 | 5 different books |
| `ryanholiday-painted-porch` | 003–006 | 4 different books |
| `cornersf-carousel` | 007, 009, 010, 016 | 4 different SF venues |
| `adrianalovegood-trinket` | 017–019 | 3 different SF shops |
| `standalone-channel-islands` | 001 | 1 |
| `standalone-carmel` | 002 | 1 |
| `standalone-grand-teton` | 008 | 1 |

Only 3 of 19 screenshots are a lone entity from a lone post.

## Category distribution

| Category | Count |
| --- | --- |
| book | 9 |
| place_shop | 4 |
| place_food | 3 |
| place_other | 2 |
| travel_city | 1 |
| recipe, event, video | 0 |

Books and places are the whole set. The design doc's Decision 8 mix (7 food,
5 books, 4 shops, 4 travel, 3 places, 3 videos, 2 recipes, 2 events) was a
starter-kit guess and does not describe this data.

## Ambiguous cases

6 of 19 are marked `expect_ask: true`, a **32% ask rate against a 15% target**.
The gap is a finding in itself: either the taxonomy needs work or the target is
wrong.

- **001, 008** — national parks fit neither `travel_city` nor `place_other`
- **002** — four candidate entities in one frame: the city, a coffee shop, a
  pizza place, and the coastline
- **010** — "plant nursery wine bar", `place_food` and `place_shop` at once
- **016** — "bookstore garden cafe", same hybrid problem
- **019** — the shop is literally named "My Favorite", which reads as a phrase

## Signals present in the frames

Things Intake can read that are not currently in its prompt:

1. **The search bar** (001, 002, 008, 017–019) carries the query that led to the
   save. Stronger intent evidence than the caption.
2. **The TikTok location card** (007, 009, 010, 016) carries name, category
   label, price tier, hours, open/closed state and address. This is most of what
   Phase 2's `find_place` was going to fetch from Google Places.
3. **The creator's own pin label** (017–019) names the entity in frame, e.g.
   "Daiso", "Topdrawer", "My Favorite". Present when there is no location card.
4. **Engagement counts** identify which screenshots share a source post.
5. **Creator handle** is visible in every frame.

## Traps

- **The big overlay word is usually not the name.** In 017–019 it reads "city",
  "a", "My", which are fragments of the video's running caption. An Intake that
  reaches for the largest text gets all three wrong.
- **The location tag is not always the thing saved.** All four Holiday frames
  are tagged "The Painted Porch Book Shop, Bastrop" but the saves are books.
- **UI chrome** (Amazon "FREE GIFT" overlay, nav bars, "Repost to followers",
  comment boxes, carousel arrows) appears throughout and must be ignored.

## Still missing from the set

- **True duplicates** — the same entity saved twice on different days. Zero so
  far, which means `link_duplicate` and `want_score` cannot be tested at all.
- **Non-saves** — receipts, texts, memes, ordinary photos. Zero so far, and
  Intake has no reject state, only `needs_review` which means "unsure".
- **recipe, event, video** — zero examples. May mean the sample is small, or may
  mean those categories do not describe real saving behavior.
