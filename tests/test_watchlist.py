import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from watchlist_db import WatchlistDb

class TestWatchlist(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = WatchlistDb(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_crud_operations(self):
        item = {
            "id": 157336,
            "tmdb_id": 157336,
            "media_type": "movie",
            "title": "Interstellar",
            "year": "2014",
            "vote_average": 8.6,
            "tier": "highly_recommend",
            "category": "Sci-Fi"
        }
        # Add
        self.assertTrue(self.db.add_item(item))

        # Status
        status = self.db.is_in_watchlist(157336, "movie")
        self.assertTrue(status["in_watchlist"])
        self.assertEqual(status["tier"], "highly_recommend")

        # Get
        items = self.db.get_items(tier="highly_recommend")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Interstellar")

        # Update Tier
        self.db.update_tier(157336, "movie", "watched")
        items = self.db.get_items(tier="watched")
        self.assertEqual(len(items), 1)

        # Export
        exported = self.db.export_json()
        self.assertEqual(exported["total_items"], 1)

        # Remove
        self.db.remove_item(157336, "movie")
        self.assertFalse(self.db.is_in_watchlist(157336, "movie")["in_watchlist"])

if __name__ == "__main__":
    unittest.main()
