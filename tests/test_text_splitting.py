"""Tests for the text-chunking logic that splits passages into slide-sized pieces."""

import pytest

from sermon_slides_generator import (
    MAX_CHARS_PER_LINE,
    MAX_LINES_PER_SLIDE,
    _estimate_lines,
    _split_long_paragraph,
    _split_text_for_slides,
)


class TestEstimateLines:
    def test_empty_text_needs_no_lines(self):
        assert _estimate_lines("", MAX_CHARS_PER_LINE) == 0

    def test_short_text_fits_on_one_line(self):
        assert _estimate_lines("For God so loved the world", MAX_CHARS_PER_LINE) == 1

    def test_text_at_limit_wraps_to_second_line(self):
        text = "x" * MAX_CHARS_PER_LINE
        assert _estimate_lines(text, MAX_CHARS_PER_LINE) == 2

    def test_long_text_scales_with_length(self):
        text = "x" * (MAX_CHARS_PER_LINE * 3)
        assert _estimate_lines(text, MAX_CHARS_PER_LINE) == 4


class TestSplitLongParagraph:
    def test_short_text_returns_single_chunk(self):
        chunks = _split_long_paragraph("A short verse.", MAX_CHARS_PER_LINE, MAX_LINES_PER_SLIDE)
        assert chunks == ["A short verse."]

    def test_splits_at_sentence_boundaries(self):
        sentence = "This is a sentence that repeats to fill space. "
        text = (sentence * 40).strip()
        chunks = _split_long_paragraph(text, MAX_CHARS_PER_LINE, MAX_LINES_PER_SLIDE)

        assert len(chunks) > 1
        max_chars = MAX_CHARS_PER_LINE * MAX_LINES_PER_SLIDE
        for chunk in chunks:
            assert len(chunk) <= max_chars
            assert chunk.endswith(".")

    def test_no_text_is_lost(self):
        sentence = "The word count of every chunk must add back up. "
        text = (sentence * 30).strip()
        chunks = _split_long_paragraph(text, MAX_CHARS_PER_LINE, MAX_LINES_PER_SLIDE)

        original_words = text.split()
        chunked_words = " ".join(chunks).split()
        assert chunked_words == original_words


class TestSplitTextForSlides:
    def test_empty_input_produces_no_slides(self):
        assert _split_text_for_slides([]) == []

    def test_single_short_paragraph_is_one_slide(self):
        slides = _split_text_for_slides(["For God so loved the world."])
        assert slides == ["For God so loved the world."]

    def test_two_short_paragraphs_share_a_slide(self):
        paragraphs = ["First short paragraph.", "Second short paragraph."]
        slides = _split_text_for_slides(paragraphs)
        assert len(slides) == 1
        assert "First short paragraph." in slides[0]
        assert "Second short paragraph." in slides[0]

    def test_long_passage_spans_multiple_slides(self):
        long_paragraph = ("In the beginning God created the heavens and the earth. " * 30).strip()
        slides = _split_text_for_slides([long_paragraph])
        assert len(slides) > 1

    def test_no_paragraph_text_is_lost(self):
        paragraphs = [
            ("Verse text that goes on for a while to force wrapping. " * 10).strip(),
            "A short closing verse.",
        ]
        slides = _split_text_for_slides(paragraphs)
        combined = " ".join(" ".join(slides).split())
        for paragraph in paragraphs:
            for word in paragraph.split():
                assert word in combined

    def test_blank_paragraphs_are_skipped(self):
        slides = _split_text_for_slides(["", "Only real content.", ""])
        assert slides == ["Only real content."]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
