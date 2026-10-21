"""Read one saved screenshot and work out what real-world thing is in it.

One Anthropic call per image. No agent loop, no MCP, no tool calls. That is
deliberate: this is the component whose accuracy is being measured, and an
agent loop would add latency, cost and nondeterminism to the measurement.

The prompt is the product here. Every rule in it came from looking at real
screenshots and watching the model fail, not from guessing.
"""

from __future__ import annotations

import base64
import io
import json
import os
import pathlib
import time
from typing import Any

import anthropic
from PIL import Image

MODEL = "claude-haiku-5-5"
MAX_IMAGE_PX = 1200
MAX_TOKENS = 1000
ASK_THRESHOLD = 0.7

CATEGORIES = (
    "book",
    "article",
    "place_food",
    "place_shop",
    "place_other",
    "travel_city",
    "video",
    "recipe",
    "event",
)

PROMPT = f"""This is a screenshot of a social post that someone saved because they
want to do, visit, read or watch the thing in it. Identify the ONE real-world
thing being saved.

Categories: {", ".join(CATEGORIES)}

book        a physical or ebook, needs an evening
article     a Substack post, essay, newsletter or blog post, fits 15 minutes
place_food  cafe, restaurant, bar, bakery, brewery
place_shop  any shop
place_other park, museum, viewpoint, national park
travel_city a city or region to visit
video       a film or show
recipe      something to cook
event       something with a date that passes

WHERE THE NAME COMES FROM. Use the first of these that is present:
1. A ranked or titled overlay naming the thing, often large and styled, such as
   "#6 Bacalar" or "#1 Oaxaca City". The number is the creator's ranking; strip
   it and keep the name.
2. A location card, which shows a name with a category, price tier, hours or
   address beneath it.
3. The creator's own pin label naming a place.
4. A book cover, product label or signage legible in the frame.
5. The caption, if it names the thing directly.

NEVER take the name from the search bar. The search bar is the person's query,
not the subject of the frame. One post can show six different places while the
search bar reads the same text on every frame, so trusting it produces six
identical wrong answers. The search bar is good evidence for the CATEGORY and
for why_saved, and is never the name.

Two more things that will mislead you:

- A venue in the location card is often only where the video was filmed. If the
  frame shows a specific book, dish or product, the save is THAT item. A post
  filmed in a bookshop showing four different book covers is four book saves,
  not four saves of the bookshop. Check for a book cover or product before you
  reach for the venue.
- The largest text is often a fragment of the video's running caption rather
  than a name. Bare words like "city", "a", "My", "and I", or a lone "#" are
  caption fragments. A titled overlay names something; a fragment does not.

Ignore app chrome entirely: nav bars, comment boxes, like and save counts,
carousel arrows, "Repost to followers", and advertising overlays.

Return ONLY a JSON object, no prose and no code fence:
{{"category": one of the categories above,
  "name": the real-world entity name, as someone would search for it,
  "why_saved": under 12 words, in the saver's voice,
  "confidence": 0.0 to 1.0,
  "evidence": under 30 words, what you actually read to decide}}

CONFIDENCE. Judge how certain you are about THIS frame, not how familiar the
thing is in general.

Go below {ASK_THRESHOLD} only when you genuinely cannot tell: no name source is
legible, the frame could be two different things, or the category is a real
coin-flip. A clearly titled book cover or a titled overlay is high confidence
even if the frame is busy.

Stay high when a name source is legible and unambiguous. Do not lower confidence
merely because the image is cluttered, because there is app chrome, or because
you recognise the thing easily.

The categories themselves have known soft edges; treat these as ordinary
judgement calls rather than reasons to drop confidence:
- a national park or a wine region is place_other or travel_city, not a failure
- a venue that is two things at once (a bookshop cafe, a plant nursery wine bar)
  takes whichever it is primarily visited for"""


class IntakeError(RuntimeError):
    """Raised when a screenshot could not be read into a usable result."""


def build_client() -> anthropic.Anthropic:
    """Construct a client, surfacing the TLS problem clearly if it bites.

    On a machine whose antivirus intercepts HTTPS, SSL_CERT_FILE must point at
    a bundle containing the AV's root. It is set in .env, so call load_dotenv()
    before this. See scripts/rebuild_ca_bundle.py.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise IntakeError("ANTHROPIC_API_KEY is not set; call load_dotenv() first")
    return anthropic.Anthropic()


def downscale(path: pathlib.Path, max_px: int = MAX_IMAGE_PX) -> bytes:
    """Shrink a screenshot so the payload stays small. Returns JPEG bytes."""
    img = Image.open(path)
    img.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _first_text(response: anthropic.types.Message) -> str:
    """Pull the first text block out of a response.

    Not response.content[0].text: this model emits a ThinkingBlock first, and
    indexing blindly raises AttributeError.
    """
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return block.text
    kinds = [getattr(b, "type", "?") for b in response.content]
    raise IntakeError(f"no text block in response, got {kinds}")


def read_screenshot(
    path: pathlib.Path,
    client: anthropic.Anthropic,
    *,
    retries: int = 2,
) -> dict[str, Any]:
    """Read one screenshot. Returns category, name, why_saved, confidence, evidence."""
    image_bytes = downscale(path)
    encoded = base64.standard_b64encode(image_bytes).decode()

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded,
                        }},
                        {"type": "text", "text": PROMPT},
                    ],
                }],
            )
            break
        except (anthropic.APIConnectionError, anthropic.RateLimitError) as exc:
            last_error = exc
            if attempt == retries:
                raise IntakeError(f"{path.name}: {type(exc).__name__} after {retries + 1} tries") from exc
            time.sleep(2 ** attempt)
    else:  # pragma: no cover
        raise IntakeError(f"{path.name}: {last_error}")

    raw = _first_text(response).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IntakeError(f"{path.name}: model did not return JSON: {raw[:160]}") from exc

    if parsed.get("category") not in CATEGORIES:
        parsed["confidence"] = 0.0
        parsed["evidence"] = f"invalid category {parsed.get('category')!r}; " + str(parsed.get("evidence", ""))[:80]

    parsed["image"] = path.name
    parsed["input_tokens"] = response.usage.input_tokens
    parsed["output_tokens"] = response.usage.output_tokens
    parsed["would_ask"] = float(parsed.get("confidence", 0)) < ASK_THRESHOLD
    return parsed
