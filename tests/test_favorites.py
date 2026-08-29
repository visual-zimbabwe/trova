import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from favorites_db import FavoritesDb

class TestFavoritesDb(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db = FavoritesDb(self.temp_file.name)

    def tearDown(self):
        try:
            os.unlink(self.temp_file.name)
        except Exception:
            pass

    def test_toggle_and_is_favorite(self):
        tmdb_id = 157336
        media_type = "movie"
        title = "Interstellar"
        year = "2014"

        # Initially not favorite
        self.assertFalse(self.db.is_favorite(tmdb_id, media_type)["is_favorite"])

        # Toggle to add
        res = self.db.toggle(tmdb_id, media_type, title, year)
        self.assertTrue(res["is_favorite"])
        self.assertTrue(self.db.is_favorite(tmdb_id, media_type)["is_favorite"])

        # Verify get_all
        all_favs = self.db.get_all()
        self.assertEqual(len(all_favs), 1)
        self.assertEqual(all_favs[0]["title"], "Interstellar")
        self.assertEqual(all_favs[0]["tmdb_id"], 157336)
        self.assertEqual(all_favs[0]["media_type"], "movie")

        # Toggle again to remove
        res2 = self.db.toggle(tmdb_id, media_type, title, year)
        self.assertFalse(res2["is_favorite"])
        self.assertFalse(self.db.is_favorite(tmdb_id, media_type)["is_favorite"])
        self.assertEqual(len(self.db.get_all()), 0)

    def test_multiple_favorites_ordering(self):
        self.db.toggle(157336, "movie", "Interstellar", "2014")
        self.db.toggle(66732, "tv", "Stranger Things", "2016")

        favs = self.db.get_all()
        self.assertEqual(len(favs), 2)
        # Most recently added is first
        self.assertEqual(favs[0]["title"], "Stranger Things")
        self.assertEqual(favs[1]["title"], "Interstellar")

if __name__ == "__main__":
    unittest.main()
