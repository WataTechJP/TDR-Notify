import hashlib
import unittest
from unittest.mock import Mock, patch

from backend import scraper


class ScraperTests(unittest.TestCase):
    @patch("backend.scraper.requests.get")
    def test_is_allowed_by_robots_allows_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.text = "User-agent: *\nDisallow:"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        allowed = scraper.is_allowed_by_robots(
            "https://example.com/news/update", "DisneyMonitorBot/1.0", 5
        )

        self.assertTrue(allowed)
        mock_get.assert_called_once_with(
            "https://example.com/robots.txt",
            headers={"User-Agent": "DisneyMonitorBot/1.0"},
            timeout=5,
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("backend.scraper.requests.get")
    def test_is_allowed_by_robots_disallows_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.text = "User-agent: *\nDisallow: /news/"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        allowed = scraper.is_allowed_by_robots(
            "https://example.com/news/update", "DisneyMonitorBot/1.0", 5
        )

        self.assertFalse(allowed)

    @patch("backend.scraper.requests.get")
    def test_get_section_hash_returns_sha256_for_selector_text(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.text = """
            <html>
                <body>
                    <div class="linkList6 listUpdate">
                        <ul>
                            <li>Park</li>
                            <li>Update</li>
                        </ul>
                    </div>
                </body>
            </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        actual_hash = scraper.get_section_hash(
            "https://example.com/news/update",
            ".linkList6.listUpdate ul",
            "DisneyMonitorBot/1.0",
            5,
        )

        expected_hash = hashlib.sha256("Park\nUpdate".encode("utf-8")).hexdigest()
        self.assertEqual(actual_hash, expected_hash)
        mock_get.assert_called_once_with(
            "https://example.com/news/update",
            headers={"User-Agent": "DisneyMonitorBot/1.0"},
            timeout=5,
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("backend.scraper.requests.get")
    def test_get_section_hash_raises_if_selector_missing(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.text = "<html><body><p>No matching section</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(ValueError, r"Selector not found: \.missing"):
            scraper.get_section_hash(
                "https://example.com/news/update", ".missing", "DisneyMonitorBot/1.0", 5
            )


if __name__ == "__main__":
    unittest.main()
