import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from watchlist_db import WatchlistDb
from tmdb_service import TmdbService
from analytics_service import AnalyticsService

class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = WatchlistDb(self.temp_db.name)
        self.tmdb = TmdbService()
        self.analytics = AnalyticsService(self.db, self.tmdb)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_metrics_calculation(self):
        self.db.add_item({
            "id": 1,
            "title": "Movie A",
            "media_type": "movie",
            "runtime": 120,
            "vote_average": 8.0,
            "genres": ["Sci-Fi", "Drama"],
            "year": "2020",
            "tier": "highly_recommend",
            "providers": {
                "US": {"providers": [{"service_key": "netflix", "name": "Netflix"}]}
            }
        })
        self.db.add_item({
            "id": 2,
            "title": "Movie B",
            "media_type": "movie",
            "runtime": 100,
            "vote_average": 9.0,
            "genres": ["Sci-Fi"],
            "year": "2022",
            "tier": "must_watch",
            "providers": {
                "US": {"providers": [{"service_key": "netflix", "name": "Netflix"}]}
            }
        })

        metrics = self.analytics.get_dashboard_metrics("US")
        self.assertEqual(metrics["total_items"], 2)
        self.assertEqual(metrics["movies_count"], 2)
        self.assertEqual(metrics["total_runtime_hours"], 3.7)
        self.assertEqual(metrics["average_rating"], 8.5)
        self.assertEqual(len(metrics["provider_coverage"]), 1)
        self.assertEqual(metrics["provider_coverage"][0]["percentage"], 100.0)

if __name__ == "__main__":
    unittest.main()
