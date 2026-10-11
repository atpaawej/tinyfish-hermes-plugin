"""Unit tests for TinyFish Web Search Provider."""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

import httpx

from provider import TinyFishWebSearchProvider, register


class TestTinyFishWebSearchProvider(unittest.TestCase):
    """Test suite for TinyFishWebSearchProvider."""

    def setUp(self):
        self.provider = TinyFishWebSearchProvider()

    def test_metadata_and_capabilities(self):
        """Test provider identification and advertised capabilities."""
        self.assertEqual(self.provider.name, "tinyfish")
        self.assertEqual(self.provider.display_name, "TinyFish")
        self.assertTrue(self.provider.supports_search())
        self.assertTrue(self.provider.supports_extract())

    def test_is_available_without_key(self):
        """is_available must return False without making network calls when key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(self.provider.is_available())

    def test_is_available_with_key(self):
        """is_available must return True when key is set."""
        with patch.dict(os.environ, {"TINYFISH_API_KEY": "test-key-123"}):
            self.assertTrue(self.provider.is_available())

    def test_search_missing_key(self):
        """search returns error envelope if TINYFISH_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            res = self.provider.search("test query")
            self.assertFalse(res["success"])
            self.assertIn("TINYFISH_API_KEY", res["error"])

    def test_search_empty_query(self):
        """search returns error envelope if query is empty."""
        with patch.dict(os.environ, {"TINYFISH_API_KEY": "test-key-123"}):
            res = self.provider.search("   ")
            self.assertFalse(res["success"])
            self.assertIn("empty", res["error"].lower())

    @patch("httpx.Client.get")
    def test_search_success_mapping(self, mock_get):
        """search must map TinyFish results to Hermes standard search envelope."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": "artificial intelligence",
            "total_results": 2,
            "results": [
                {
                    "position": 1,
                    "site_name": "Example AI",
                    "title": "Intro to AI",
                    "snippet": "A brief overview of artificial intelligence.",
                    "url": "https://example.com/ai",
                },
                {
                    "position": 2,
                    "site_name": "Tech News",
                    "title": "AI in 2026",
                    "snippet": "Latest trends in AI.",
                    "url": "https://example.com/ai-2026",
                },
            ],
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"TINYFISH_API_KEY": "test-key-123"}):
            res = self.provider.search("artificial intelligence", limit=5)

        self.assertTrue(res["success"])
        self.assertIn("data", res)
        self.assertIn("web", res["data"])
        items = res["data"]["web"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "Intro to AI")
        self.assertEqual(items[0]["url"], "https://example.com/ai")
        self.assertEqual(items[0]["description"], "A brief overview of artificial intelligence.")
        self.assertEqual(items[0]["position"], 1)

        # Verify headers and params sent to TinyFish API
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["X-API-Key"], "test-key-123")
        self.assertEqual(kwargs["params"]["query"], "artificial intelligence")

    @patch("httpx.Client.get")
    def test_search_http_401_error(self, mock_get):
        """search must return a helpful error message on HTTP 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized: Invalid API Key"
        mock_req = MagicMock()
        mock_get.side_effect = httpx.HTTPStatusError("401 Unauthorized", request=mock_req, response=mock_response)

        with patch.dict(os.environ, {"TINYFISH_API_KEY": "bad-key"}):
            res = self.provider.search("test")

        self.assertFalse(res["success"])
        self.assertIn("authentication failed", res["error"].lower())

    def test_extract_empty_urls(self):
        """extract returns error envelope if URL list is empty."""
        with patch.dict(os.environ, {"TINYFISH_API_KEY": "test-key-123"}):
            res = self.provider.extract([])
            self.assertFalse(res["success"])
            self.assertIn("No URLs provided", res["error"])

    @patch("httpx.Client.post")
    def test_extract_success_mapping(self, mock_post):
        """extract must map TinyFish fetch results to Hermes standard extract envelope."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/article",
                    "final_url": "https://example.com/article",
                    "title": "Clean Markdown Article",
                    "description": "Article summary",
                    "text": "# Article Header\n\nClean markdown content here.",
                }
            ],
            "errors": [],
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TINYFISH_API_KEY": "test-key-123"}):
            res = self.provider.extract(["https://example.com/article"])

        self.assertTrue(res["success"])
        pages = res["data"]
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["url"], "https://example.com/article")
        self.assertEqual(pages[0]["title"], "Clean Markdown Article")
        self.assertEqual(pages[0]["content"], "# Article Header\n\nClean markdown content here.")
        self.assertEqual(pages[0]["raw_content"], "# Article Header\n\nClean markdown content here.")

        # Verify POST payload sent
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["X-API-Key"], "test-key-123")
        self.assertEqual(kwargs["json"]["urls"], ["https://example.com/article"])
        self.assertEqual(kwargs["json"]["format"], "markdown")

    @patch("httpx.Client.post")
    def test_extract_with_individual_error(self, mock_post):
        """extract must gracefully capture per-URL failures."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/ok",
                    "final_url": "https://example.com/ok",
                    "title": "OK Page",
                    "text": "Valid text",
                }
            ],
            "errors": [
                {
                    "url": "https://example.com/bad",
                    "error": "404 Not Found",
                }
            ],
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TINYFISH_API_KEY": "test-key-123"}):
            res = self.provider.extract(["https://example.com/ok", "https://example.com/bad"])

        self.assertTrue(res["success"])
        pages = res["data"]
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["url"], "https://example.com/ok")
        self.assertEqual(pages[1]["url"], "https://example.com/bad")
        self.assertEqual(pages[1]["error"], "404 Not Found")

    def test_register_context(self):
        """register(ctx) must invoke ctx.register_web_search_provider with the provider."""
        mock_ctx = MagicMock()
        register(mock_ctx)
        mock_ctx.register_web_search_provider.assert_called_once()
        registered_provider = mock_ctx.register_web_search_provider.call_args[0][0]
        self.assertIsInstance(registered_provider, TinyFishWebSearchProvider)
        self.assertEqual(registered_provider.name, "tinyfish")


if __name__ == "__main__":
    unittest.main()
