"""Tests for the data logic around the Intake call.

The model's judgement is tested by the eval set in evals/, as CLAUDE.md
specifies. These cover the parts that are plain code: image downscaling,
pulling the right block out of a response, parsing, and the scoring helpers.

No API calls. The client is a stub.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Any

import pytest
from PIL import Image

from backend.intake import (
    ASK_THRESHOLD,
    CATEGORIES,
    IntakeError,
    _first_text,
    downscale,
    read_screenshot,
)
from evals.run_intake import name_matches, normalise


@dataclass
class Block:
    type: str
    text: str = ""


@dataclass
class Usage:
    input_tokens: int = 100
    output_tokens: int = 50


@dataclass
class Response:
    content: list[Block]
    usage: Usage = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.usage is None:
            self.usage = Usage()


class StubClient:
    """Stands in for anthropic.Anthropic. Returns whatever text it is given."""

    def __init__(self, text: str, *, thinking_first: bool = False) -> None:
        blocks = [Block("thinking", "deliberating")] if thinking_first else []
        blocks.append(Block("text", text))
        self._response = Response(blocks)
        self.messages = self
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Response:
        self.calls.append(kwargs)
        return self._response


@pytest.fixture
def screenshot(tmp_path):
    path = tmp_path / "test.png"
    Image.new("RGB", (1200, 2600), "navy").save(path)
    return path


GOOD = json.dumps({
    "category": "travel_city",
    "name": "Bacalar",
    "why_saved": "Lagoon swimming",
    "confidence": 0.9,
    "evidence": "Title overlay reads #6 Bacalar",
})


class TestDownscale:
    def test_caps_the_long_edge(self, screenshot):
        img = Image.open(io.BytesIO(downscale(screenshot, max_px=600)))
        assert max(img.size) <= 600

    def test_keeps_aspect_ratio(self, screenshot):
        img = Image.open(io.BytesIO(downscale(screenshot, max_px=600)))
        assert abs(img.size[0] / img.size[1] - 1200 / 2600) < 0.01

    def test_returns_jpeg(self, screenshot):
        assert Image.open(io.BytesIO(downscale(screenshot))).format == "JPEG"

    def test_shrinks_the_payload(self, screenshot):
        assert len(downscale(screenshot)) < screenshot.stat().st_size


class TestFirstText:
    def test_skips_a_thinking_block(self):
        got = _first_text(Response([Block("thinking", "hmm"), Block("text", "answer")]))
        assert got == "answer"

    def test_plain_text_response(self):
        assert _first_text(Response([Block("text", "answer")])) == "answer"

    def test_raises_when_no_text_block(self):
        with pytest.raises(IntakeError, match="no text block"):
            _first_text(Response([Block("thinking", "hmm")]))


class TestReadScreenshot:
    def test_parses_a_clean_response(self, screenshot):
        got = read_screenshot(screenshot, StubClient(GOOD))
        assert got["category"] == "travel_city"
        assert got["name"] == "Bacalar"
        assert got["image"] == "test.png"

    def test_survives_a_thinking_block(self, screenshot):
        got = read_screenshot(screenshot, StubClient(GOOD, thinking_first=True))
        assert got["name"] == "Bacalar"

    def test_strips_a_code_fence(self, screenshot):
        got = read_screenshot(screenshot, StubClient(f"```json\n{GOOD}\n```"))
        assert got["name"] == "Bacalar"

    def test_raises_on_non_json(self, screenshot):
        with pytest.raises(IntakeError, match="did not return JSON"):
            read_screenshot(screenshot, StubClient("I think this is a lagoon."))

    def test_rejects_a_category_outside_the_enum(self, screenshot):
        payload = json.dumps({**json.loads(GOOD), "category": "nightclub"})
        got = read_screenshot(screenshot, StubClient(payload))
        assert got["confidence"] == 0.0
        assert got["would_ask"] is True

    @pytest.mark.parametrize(
        ("confidence", "expected"),
        [(0.95, False), (ASK_THRESHOLD, False), (ASK_THRESHOLD - 0.01, True), (0.1, True)],
    )
    def test_would_ask_follows_the_threshold(self, screenshot, confidence, expected):
        payload = json.dumps({**json.loads(GOOD), "confidence": confidence})
        assert read_screenshot(screenshot, StubClient(payload))["would_ask"] is expected

    def test_records_token_usage(self, screenshot):
        got = read_screenshot(screenshot, StubClient(GOOD))
        assert got["input_tokens"] == 100 and got["output_tokens"] == 50

    def test_sends_one_image_and_one_prompt(self, screenshot):
        client = StubClient(GOOD)
        read_screenshot(screenshot, client)
        parts = client.calls[0]["messages"][0]["content"]
        assert [p["type"] for p in parts] == ["image", "text"]

    def test_prompt_names_every_category(self, screenshot):
        client = StubClient(GOOD)
        read_screenshot(screenshot, client)
        prompt = client.calls[0]["messages"][0]["content"][1]["text"]
        assert all(c in prompt for c in CATEGORIES)

    def test_prompt_forbids_the_search_bar_as_name(self, screenshot):
        """The bug the Mexico batch exposed. Guard it so it cannot come back."""
        client = StubClient(GOOD)
        read_screenshot(screenshot, client)
        prompt = client.calls[0]["messages"][0]["content"][1]["text"]
        assert "NEVER take the name from the search bar" in prompt


class TestNameMatching:
    @pytest.mark.parametrize("got,want", [
        ("Bacalar", "Bacalar"),
        ("bacalar", "BACALAR"),
        ("  Taxco  ", "Taxco"),
        ("The 33 Strategies of War by Robert Greene", "The 33 Strategies of War"),
        ("Daiso San Francisco", "Daiso"),
        ("Oaxaca City", "Oaxaca Citty"),
    ])
    def test_matches(self, got, want):
        assert name_matches(got, want)

    @pytest.mark.parametrize("got,want", [
        ("trinket stores San Francisco", "Topdrawer"),
        ("Valle de Guadalupe", "Bacalar"),
        ("", "Bacalar"),
        ("Bacalar", ""),
    ])
    def test_does_not_match(self, got, want):
        assert not name_matches(got, want)

    def test_normalise_collapses_whitespace_and_case(self):
        assert normalise("  Oaxaca   CITY ") == "oaxaca city"
