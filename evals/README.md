# Evals

Agents fail quietly. These checks tell you if a prompt change made things better or worse.

## intake/
- Put 30 of your real screenshots in `evals/intake/images/`. Mix categories: about 8 food, 6 books, 4 shops, 4 travel, 4 videos, 4 other.
- For each, write the right answer in `evals/intake/expected.jsonl`:
  `{"image": "001.png", "category": "book", "name": "Tomorrow, and Tomorrow, and Tomorrow", "city": null}`
- Run `python -m evals.run_intake`. It reports category accuracy, name match rate (fuzzy), and how often the agent asked instead of guessing.
- Target: category 95%, name 90%, asks under 15%.

## planner/
- Write 5 fake weekends in `evals/planner/weeks/`: calendar, weather, a small saves list, recent feedback.
- For each, write what a good plan must and must not include.
- Run `python -m evals.run_planner`. A second Claude call grades each plan against the rules (LLM as judge), and you read the 5 plans yourself.

## Rule
Run evals before you change any agent .md file, and again after. Write the scores in `evals/HISTORY.md`.
