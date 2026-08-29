import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from favorites_db import FavoritesDb

class TestFavoritesCategories(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = FavoritesDb(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_toggle_and_status(self):
        # Insert favorite movie
        res = self.db.toggle(
            tmdb_id=157336,
            media_type="movie",
            title="Interstellar",
            year="2014",
            poster_path="/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
        )
        self.assertTrue(res["is_favorite"])

        # Check status
        status = self.db.is_favorite(157336, "movie")
        self.assertTrue(status["is_favorite"])

        # Check summary
        summary = self.db.get_summary()
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["movies"], 1)
        self.assertEqual(summary["tv"], 0)

    def test_shelf_items(self):
        self.db.toggle(157336, "movie", "Interstellar", "2014")
        self.db.toggle(27205, "movie", "Inception", "2010")
        self.db.toggle(66732, "tv", "Stranger Things", "2016")

        shelf = self.db.get_shelf_items(limit_per_type=5)
        self.assertEqual(len(shelf["movies"]), 2)
        self.assertEqual(len(shelf["tv"]), 1)
        self.assertEqual(shelf["movies"][0]["title"], "Inception")
        self.assertEqual(shelf["tv"][0]["title"], "Stranger Things")

    def test_get_all_media_type_filtering(self):
        self.db.toggle(1, "movie", "Movie A")
        self.db.toggle(2, "movie", "Movie B")
        self.db.toggle(3, "tv", "TV Show C")

        all_items = self.db.get_all()
        self.assertEqual(len(all_items), 3)

        movies = self.db.get_all(media_type="movie")
        self.assertEqual(len(movies), 2)

        tv_items = self.db.get_all(media_type="tv")
        self.assertEqual(len(tv_items), 1)

    def test_import_trova_json(self):
        sample_json = {
            "schemaVersion": 2,
            "exportKind": "find-streamer-watchlist",
            "items": [
                {
                    "tmdbId": 1001,
                    "mediaType": "movie",
                    "title": "Sample Film",
                    "year": "2024",
                    "posterUrl": "https://example.com/poster.jpg"
                },
                {
                    "tmdbId": 2002,
                    "mediaType": "tv",
                    "title": "Sample Series",
                    "year": "2025",
                    "posterUrl": "https://example.com/tv.jpg"
                }
            ]
        }
        res = self.db.import_from_json(sample_json)
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 2)

        summary = self.db.get_summary()
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["movies"], 1)
        self.assertEqual(summary["tv"], 1)

    def test_summary_and_ids(self):
        self.db.toggle(10, "movie", "Film 1")
        self.db.toggle(20, "movie", "Film 2")
        self.db.toggle(30, "tv", "Show 1")

        summary = self.db.get_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["movies"], 2)
        self.assertEqual(summary["tv"], 1)

        ids = self.db.get_favorite_ids()
        self.assertEqual(len(ids), 3)
        self.assertIn("movie_10", ids)
        self.assertIn("movie_20", ids)
        self.assertIn("tv_30", ids)

    def test_pagination_and_search(self):
        for i in range(10):
            self.db.toggle(100 + i, "movie", f"Avatar {i}")

        p1 = self.db.get_all(media_type="movie", offset=0, limit=4)
        self.assertEqual(len(p1), 4)

        p2 = self.db.get_all(media_type="movie", offset=4, limit=4)
        self.assertEqual(len(p2), 4)

        search_res = self.db.get_all(search="Avatar 3")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["title"], "Avatar 3")

if __name__ == "__main__":
    unittest.main()
