import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from tmdb_service import TmdbService

class TestBackendApi(unittest.TestCase):
    def setUp(self):
        self.tmdb = TmdbService()

    def test_search_multi(self):
        res = self.tmdb.search_multi("Interstellar")
        self.assertIn("results", res)
        self.assertGreater(len(res["results"]), 0)
        first = res["results"][0]
        self.assertEqual(first["title"], "Interstellar")
        self.assertEqual(first["media_type"], "movie")
        self.assertEqual(first["year"], "2014")

    def test_details_streaming_countries(self):
        # Interstellar movie ID: 157336
        details = self.tmdb.get_details("movie", 157336)
        self.assertIsNotNone(details)
        self.assertEqual(details["title"], "Interstellar")
        self.assertIn("countries", details)
        self.assertGreater(len(details["countries"]), 0)

        # Verify country record fields
        first_country = details["countries"][0]
        self.assertIn("code", first_country)
        self.assertIn("name", first_country)
        self.assertIn("flag", first_country)
        self.assertIn("providers", first_country)
        self.assertGreater(len(first_country["providers"]), 0)

    def test_paramount_plus_us_only_rule(self):
        details = self.tmdb.get_details("movie", 157336)
        
        # Check US entry
        us_entry = next((c for c in details["countries"] if c["code"] == "US"), None)
        self.assertIsNotNone(us_entry, "US should be in Interstellar stream countries")
        us_provider_ids = [p["id"] for p in us_entry["providers"]]
        self.assertIn("paramount_plus", us_provider_ids)
        self.assertIn("prime", us_provider_ids)

    def test_only_four_streaming_platforms_allowed(self):
        allowed_ids = {"netflix", "prime", "max", "paramount_plus"}
        details = self.tmdb.get_details("movie", 157336)
        for country in details["countries"]:
            for provider in country["providers"]:
                self.assertIn(
                    provider["id"],
                    allowed_ids,
                    f"Unexpected streaming provider {provider['id']} found"
                )

    def test_paradigm_2_regions_and_hero(self):
        # Explicit US test
        details_us = self.tmdb.get_details("movie", 157336, user_country="US")
        self.assertIn("local_country", details_us)
        self.assertEqual(details_us["local_country"]["code"], "US")
        self.assertTrue(details_us["local_country"]["available"])
        self.assertGreater(len(details_us["local_country"]["providers"]), 0)

        # Dynamic location test (detected from system signals e.g. CA)
        details_dynamic = self.tmdb.get_details("movie", 157336)
        self.assertIn("local_country", details_dynamic)
        self.assertTrue(len(details_dynamic["local_country"]["code"]) == 2)
        self.assertIn("name", details_dynamic["local_country"])
        self.assertIn("flag", details_dynamic["local_country"])

        self.assertIn("service_counts", details_dynamic)
        counts = details_dynamic["service_counts"]
        self.assertIn("all", counts)
        self.assertIn("netflix", counts)
        self.assertIn("prime", counts)
        self.assertIn("max", counts)
        self.assertIn("paramount_plus", counts)
        self.assertGreater(counts["all"], 0)

        self.assertIn("regions", details_dynamic)
        self.assertGreater(len(details_dynamic["regions"]), 0)
        for region in details_dynamic["regions"]:
            self.assertIn("name", region)
            self.assertIn("emoji", region)
            self.assertIn("total", region)
            self.assertIn("countries", region)
            self.assertEqual(len(region["countries"]), region["total"])

    def test_trailer_extraction(self):
        details = self.tmdb.get_details("movie", 157336)
        self.assertIn("trailer", details)
        self.assertIsNotNone(details["trailer"])
        self.assertIn("url", details["trailer"])
        self.assertIn("youtube.com", details["trailer"]["url"])

if __name__ == "__main__":
    unittest.main()

