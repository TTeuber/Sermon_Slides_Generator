"""Offline tests for the BibleGateway scraping code.

Saved HTML fixtures stand in for live responses, so `fetch_passage_text`
and `_remove_footnotes` are exercised without any network calls.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from sermon_slides_generator import _remove_footnotes, fetch_passage_text

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _mock_response(fixture_name: str) -> Mock:
    """Build a fake requests.Response backed by a saved HTML fixture."""
    response = Mock()
    response.content = (FIXTURES_DIR / fixture_name).read_bytes()
    response.raise_for_status = Mock()
    return response


class TestRemoveFootnotes:
    def _clean(self, html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        _remove_footnotes(soup)
        return soup

    def test_verse_numbers_are_kept(self):
        soup = self._clean('<p><sup class="versenum">16 </sup>For God loved the world</p>')
        assert soup.find("sup", class_="versenum") is not None
        assert "16" in soup.get_text()

    def test_footnote_markers_are_removed(self):
        soup = self._clean(
            '<p>in this way:<sup class="footnote">[<a href="#fn-a">a</a>]</sup> He gave</p>'
        )
        assert soup.find("sup") is None
        assert "[a]" not in soup.get_text()

    def test_crossreference_markers_are_removed(self):
        soup = self._clean(
            '<p>his one and only Son<sup class="crossreference">(<a href="#cr-A">A</a>)</sup></p>'
        )
        assert soup.find("sup") is None
        assert "(A)" not in soup.get_text()

    def test_mixed_superscripts_only_keep_versenum(self):
        soup = self._clean(
            '<p><sup class="versenum">1 </sup>Text<sup class="footnote">[a]</sup>'
            '<sup class="crossreference">(A)</sup></p>'
        )
        remaining = soup.find_all("sup")
        assert len(remaining) == 1
        assert remaining[0].get("class") == ["versenum"]


class TestFetchPassageText:
    def test_prose_passage_extracts_paragraph_text(self):
        with patch("sermon_slides_generator.requests.get", return_value=_mock_response("john_3_16_17.html")):
            paragraphs = fetch_passage_text("John 3:16-17")

        assert len(paragraphs) == 1
        text = paragraphs[0]
        assert "For God loved the world in this way" in text
        assert "but to save the world through him" in text

    def test_verse_numbers_survive_but_footnote_markers_do_not(self):
        with patch("sermon_slides_generator.requests.get", return_value=_mock_response("john_3_16_17.html")):
            text = fetch_passage_text("John 3:16-17")[0]

        assert "16" in text
        assert "17" in text
        assert "[a]" not in text
        assert "(A)" not in text

    def test_footnote_bodies_are_not_extracted(self):
        with patch("sermon_slides_generator.requests.get", return_value=_mock_response("john_3_16_17.html")):
            paragraphs = fetch_passage_text("John 3:16-17")

        combined = " ".join(paragraphs)
        assert "For God loved the world so much" not in combined
        assert "Footnotes" not in combined
        assert "Cross references" not in combined

    def test_poetry_line_breaks_become_spaces(self):
        with patch("sermon_slides_generator.requests.get", return_value=_mock_response("psalm_23.html")):
            paragraphs = fetch_passage_text("Psalm 23:1-3")

        assert len(paragraphs) == 1
        text = paragraphs[0]
        assert "The Lord is my shepherd; I have what I need." in text
        assert "\n" not in text
        assert "  " not in text  # br replacements must not leave double spaces

    def test_missing_passage_returns_empty_list(self):
        with patch("sermon_slides_generator.requests.get", return_value=_mock_response("no_results.html")):
            assert fetch_passage_text("Hezekiah 1:1") == []

    def test_network_error_returns_empty_list(self):
        with patch(
            "sermon_slides_generator.requests.get",
            side_effect=requests.RequestException("connection refused"),
        ):
            assert fetch_passage_text("John 3:16") == []

    def test_request_url_encodes_search_term_and_version(self):
        with patch("sermon_slides_generator.requests.get", return_value=_mock_response("john_3_16_17.html")) as mock_get:
            fetch_passage_text("John 3:16-17")

        requested_url = mock_get.call_args.args[0]
        assert "search=John%203%3A16-17" in requested_url
        assert "version=CSB" in requested_url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
