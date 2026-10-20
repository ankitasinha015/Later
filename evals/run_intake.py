"""Run Intake over the labelled screenshots and score it.

    python -m evals.run_intake

Writes evals/intake/results.jsonl (one record per image) and appends a dated
row to evals/HISTORY.md. The results file is the contract with render.py: the
page is built from it, so re-rendering never costs another API call and the
published number always matches the page.

Scoring follows the targets in evals/README.md:
    category 95%, name 90% fuzzy at 0.85, asks under 15%

Rows marked expect_ask in expected.jsonl are genuinely ambiguous to a human.
They are scored on whether Intake asked, not on whether it guessed the same
category a human did.
"""

from __future__ import annotations

import datetime as dt
import difflib
import json
import pathlib
import sys

from dotenv import load_dotenv

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from backend.intake import IntakeError, build_client, read_screenshot  # noqa: E402

IMAGES = REPO / "evals" / "intake" / "images"
EXPECTED = REPO / "evals" / "intake" / "expected.jsonl"
RESULTS = REPO / "evals" / "intake" / "results.jsonl"
HISTORY = REPO / "evals" / "HISTORY.md"

NAME_MATCH_THRESHOLD = 0.85


def normalise(name: str) -> str:
    return " ".join(str(name or "").lower().split())


def name_matches(got: str, want: str) -> bool:
    a, b = normalise(got), normalise(want)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= NAME_MATCH_THRESHOLD


def load_expected() -> list[dict]:
    return [
        json.loads(line)
        for line in EXPECTED.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    load_dotenv(REPO / ".env")

    expected = load_expected()
    if not expected:
        print(f"no labels in {EXPECTED}")
        return 1

    try:
        client = build_client()
    except IntakeError as exc:
        print(f"could not start: {exc}")
        return 1

    results: list[dict] = []
    failures: list[str] = []

    print(f"running {len(expected)} screenshots through {__import__('backend.intake', fromlist=['MODEL']).MODEL}\n")

    for row in expected:
        path = IMAGES / row["image"]
        if not path.exists():
            failures.append(f"{row['image']}: image missing")
            continue
        try:
            got = read_screenshot(path, client)
        except IntakeError as exc:
            failures.append(str(exc))
            continue

        got["expected_category"] = row.get("category")
        got["expected_name"] = row.get("name")
        got["expect_ask"] = bool(row.get("expect_ask"))
        got["source_post"] = row.get("source_post")
        got["category_ok"] = got.get("category") == row.get("category")
        got["name_ok"] = name_matches(got.get("name", ""), row.get("name", ""))
        results.append(got)

        flag = "ok " if got["category_ok"] else "MISS"
        ask = " ask" if got["would_ask"] else "    "
        print(f"  {flag}{ask}  {got['image']}  {got.get('category','?'):<12} {str(got.get('name',''))[:42]}")

    if not results:
        print("\nnothing scored")
        for f in failures:
            print(f"  {f}")
        return 1

    RESULTS.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    # Unambiguous rows carry the accuracy score. Ambiguous ones are judged on
    # whether Intake had the sense to flag them.
    clear = [r for r in results if not r["expect_ask"]]
    ambiguous = [r for r in results if r["expect_ask"]]

    cat_acc = 100 * sum(r["category_ok"] for r in clear) / len(clear) if clear else 0.0
    name_acc = 100 * sum(r["name_ok"] for r in clear) / len(clear) if clear else 0.0
    ask_rate = 100 * sum(r["would_ask"] for r in results) / len(results)
    caught = 100 * sum(r["would_ask"] for r in ambiguous) / len(ambiguous) if ambiguous else 0.0
    tokens_in = sum(r.get("input_tokens", 0) for r in results)

    print(f"\n{'=' * 58}")
    print(f"  scored {len(results)} of {len(expected)}  ({len(clear)} clear, {len(ambiguous)} ambiguous)")
    print(f"  category accuracy  {cat_acc:5.1f}%   target 95%   [clear rows only]")
    print(f"  name match         {name_acc:5.1f}%   target 90%   [fuzzy at {NAME_MATCH_THRESHOLD}]")
    print(f"  would-ask rate     {ask_rate:5.1f}%   target <15%")
    print(f"  ambiguous caught   {caught:5.1f}%   [did it flag the hard ones]")
    print(f"  input tokens       {tokens_in:,}")
    print(f"{'=' * 58}")

    for r in clear:
        if not r["category_ok"]:
            print(f"  MISS {r['image']}: said {r.get('category')}/{str(r.get('name'))[:30]}, "
                  f"expected {r['expected_category']}/{str(r['expected_name'])[:30]}")
    for f in failures:
        print(f"  FAIL {f}")

    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if not HISTORY.exists():
        HISTORY.write_text(
            "# Eval history\n\nOne row per run. Append only.\n\n"
            "| when | n | category | name | asks | caught | note |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n",
            encoding="utf-8", newline="\n",
        )
    with HISTORY.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"| {stamp} | {len(results)} | {cat_acc:.1f}% | {name_acc:.1f}% | "
                 f"{ask_rate:.1f}% | {caught:.1f}% | |\n")

    print(f"\n  wrote {RESULTS.relative_to(REPO)}")
    print(f"  appended to {HISTORY.relative_to(REPO)}")
    print(f"  now run: python -m evals.render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
