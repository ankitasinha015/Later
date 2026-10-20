"""Render the eval results as a page: screenshot beside what Later understood.

    python -m evals.render

Reads evals/intake/results.jsonl and writes evals/results.html. Makes no API
calls, so re-rendering is free and the page always matches the number already
written to HISTORY.md.

This is a debugging surface, so confidence and evidence are always shown.
DESIGN.md's "confidence badge only if below 0.8" rule applies to the shipped
app, where the reasoning is meant to stay quiet.

Colours are DESIGN.md's tokens; type is system fonts rather than Fraunces and
Inter, which are deferred until the app proper.
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
RESULTS = REPO / "evals" / "intake" / "results.jsonl"
OUTPUT = REPO / "evals" / "results.html"

PAPER, CARD, INK, MUTED, LINE, ACCENT = "#FAF7F2", "#FFFFFF", "#1F1B16", "#6B6359", "#E7E1D8", "#D9572B"

STAMP = {
    "book": "#3E6FB0", "article": "#5B6B8C", "place_food": "#C0702A",
    "place_shop": "#9B4D8A", "place_other": "#4C8B5A", "travel_city": "#2F8C8C",
    "video": "#B23A48", "recipe": "#7A8C2F", "event": "#D9572B",
}


def tint(hex_colour: str, alpha: float = 0.12) -> str:
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def chip(text: str, colour: str) -> str:
    return (f'<span style="background:{tint(colour)};color:{colour};font-size:12px;'
            f'padding:3px 10px;border-radius:999px;white-space:nowrap">{html.escape(text)}</span>')


def card(row: dict) -> str:
    category = row.get("category", "?")
    colour = STAMP.get(category, MUTED)
    ok = row.get("category_ok")
    border = LINE if ok else ACCENT

    chips = [chip(category, colour)]
    if row.get("would_ask"):
        chips.append(chip("would ask", ACCENT))
    if not ok:
        chips.append(chip(f"expected {row.get('expected_category')}", ACCENT))

    conf = row.get("confidence", 0)
    name_note = "" if row.get("name_ok") else (
        f'<div style="font-size:12px;color:{ACCENT};margin-top:4px">'
        f'expected name: {html.escape(str(row.get("expected_name", "")))}</div>')

    return f"""
<div style="display:flex;gap:14px;padding:16px;border-bottom:1px solid {LINE};border-left:3px solid {border}">
  <a href="intake/images/{html.escape(row['image'])}" style="flex:0 0 104px">
    <img src="intake/images/{html.escape(row['image'])}" alt="{html.escape(row['image'])}"
         style="width:104px;border-radius:8px;border:1px solid {LINE};display:block">
  </a>
  <div style="flex:1;min-width:0">
    <div style="font-size:11px;color:{MUTED};letter-spacing:.04em">
      {html.escape(row['image'])} &middot; LATER UNDERSTOOD
    </div>
    <div style="font-size:19px;color:{INK};margin:5px 0 9px;font-family:Georgia,'Times New Roman',serif">
      {html.escape(str(row.get('name', '?')))}
    </div>
    {name_note}
    <div style="display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:10px">
      {''.join(chips)}
      <span style="font-size:12px;color:{MUTED}">confidence {conf}</span>
    </div>
    <div style="font-size:13px;color:{INK};line-height:1.5;margin-bottom:6px">
      {html.escape(str(row.get('why_saved', '')))}
    </div>
    <div style="font-size:12px;color:{MUTED};line-height:1.5">
      <span style="color:{INK}">Evidence:</span> {html.escape(str(row.get('evidence', '')))}
    </div>
  </div>
</div>"""


def main() -> int:
    if not RESULTS.exists():
        print(f"no results at {RESULTS}. Run: python -m evals.run_intake")
        return 1

    rows = [json.loads(l) for l in RESULTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows:
        print("results file is empty")
        return 1

    clear = [r for r in rows if not r.get("expect_ask")]
    cat_acc = 100 * sum(r.get("category_ok", False) for r in clear) / len(clear) if clear else 0
    name_acc = 100 * sum(r.get("name_ok", False) for r in clear) / len(clear) if clear else 0
    asks = 100 * sum(r.get("would_ask", False) for r in rows) / len(rows)

    # Misses first: this page exists to show what went wrong.
    rows.sort(key=lambda r: (r.get("category_ok", False), r.get("name_ok", False), r["image"]))

    OUTPUT.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Later &middot; Intake results</title></head>
<body style="margin:0;background:{PAPER};font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:{INK}">
<div style="max-width:560px;margin:0 auto;padding:0 16px 48px">
  <div style="padding:28px 0 14px">
    <div style="font-size:25px;font-family:Georgia,'Times New Roman',serif">Intake results</div>
    <div style="font-size:13px;color:{MUTED};margin-top:6px">
      {len(rows)} screenshots &middot; category {cat_acc:.0f}% &middot;
      name {name_acc:.0f}% &middot; would-ask {asks:.0f}%
    </div>
    <div style="font-size:12px;color:{MUTED};margin-top:4px">
      Misses first. Accuracy counts the {len(clear)} unambiguous rows.
    </div>
  </div>
  <div style="background:{CARD};border:1px solid {LINE};border-radius:16px;overflow:hidden">
    {''.join(card(r) for r in rows)}
  </div>
</div>
</body></html>
""", encoding="utf-8", newline="\n")

    print(f"wrote {OUTPUT}")
    print(f"open it: start {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
