# Intake eval set manifest

The images themselves are gitignored (they are personal TikTok screenshots and
this repo is public). This manifest records what is in the set so the labels in
`expected.jsonl` can be reviewed without the images.

Collected 2026-10-15. 16 of a target 30.

## Source posts

The headline finding from this batch: **16 screenshots are only 6 posts.** Three
posts account for 13 of them, and in every case the frames capture *different*
entities, not the same one twice. Grouping was confirmed by identical engagement
counts within each set.

| Source post | Images | Entities captured |
| --- | --- | --- |
| `ryanholiday-painted-porch` | 003–006 | 4 different books |
| `fiobros-reading` | 011–015 | 5 different books |
| `cornersf-carousel` | 007, 009, 010, 016 | 4 different SF venues |
| `standalone-channel-islands` | 001 | 1 |
| `standalone-carmel` | 002 | 1 |
| `standalone-grand-teton` | 008 | 1 |

## Category distribution

| Category | Count |
| --- | --- |
| book | 9 |
| place_food | 3 |
| place_other | 2 |
| place_shop | 1 |
| travel_city | 1 |
| recipe, event, video | 0 |

This does not match the planned mix in the design doc's Decision 8 (7 food,
5 books, 4 shops, 4 travel, 3 places, 3 videos, 2 recipes, 2 events). The
planned mix was a guess inherited from the starter kit. Either collect the
remaining 14 to fill the gaps deliberately, or revise the target mix to match
real saving behavior.

## Ambiguous cases

5 of 16 are marked `expect_ask: true`, a 31% ask rate against a 15% target.
That gap is itself a finding: either the taxonomy needs work, or the target is
wrong.

- **001, 008** — national parks fit neither `travel_city` nor `place_other`
- **002** — four candidate entities in one frame: the city, a coffee shop, a
  pizza place, and the coastline
- **010** — "plant nursery wine bar", `place_food` and `place_shop` at once
- **016** — "bookstore garden cafe", same hybrid problem

## Signals present in the frames

Things Intake can read that are not currently in its prompt:

1. **The search bar** (001, 002, 008) carries the query that led to the save.
   Stronger intent evidence than the caption.
2. **The location card** (007, 009, 010, 016) carries name, category label,
   price tier, hours, open/closed state and address. This is most of what
   Phase 2's `find_place` was going to fetch from Google Places.
3. **Engagement counts** identify which screenshots share a source post.
4. **Creator handle** is visible in every frame.

## Traps

- The location tag is not always the thing saved. All four Holiday frames are
  tagged "The Painted Porch Book Shop, Bastrop" but the saves are the books.
- UI chrome (Amazon "FREE GIFT" overlay, nav bars, "Repost to followers",
  comment boxes) appears in several frames and must be ignored.
