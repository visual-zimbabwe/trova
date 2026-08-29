import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from settings_service import SettingsService, ALL_SERVICES, DEFAULT_ENABLED_SERVICES
from tmdb_service import TmdbService

class TestSettingsService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = SettingsService(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_settings(self):
        data = self.settings.get_settings()
        self.assertEqual(len(data["services"]), 14)
        self.assertEqual(data["enabled_services"], ["netflix", "prime", "max", "paramount_plus"])

    def test_update_and_persist_settings(self):
        new_services = ["netflix", "hulu", "cbc_gem", "bbc_iplayer"]
        updated = self.settings.update_settings(new_services)
        self.assertEqual(updated["enabled_services"], new_services)

        # Reload from disk
        fresh = SettingsService(self.temp_dir.name)
        self.assertEqual(fresh.get_enabled_services(), new_services)

    def test_reset_to_defaults(self):
        self.settings.update_settings(["hulu", "peacock"])
        reset = self.settings.reset_to_defaults()
        self.assertEqual(reset["enabled_services"], DEFAULT_ENABLED_SERVICES)

    def test_global_paramount_plus_matching(self):
        tmdb = TmdbService(settings_service=self.settings)
        
        # Test Paramount+ matches in Canada (CA)
        ca_p = {"provider_id": 531, "provider_name": "Paramount Plus"}
        matched = tmdb._match_core_service(ca_p, "CA", {"paramount_plus"})
        self.assertIsNotNone(matched)
        self.assertEqual(matched["id"], "paramount_plus")
        self.assertEqual(matched["name"], "Paramount+")

        # Test Paramount+ matches in Great Britain (GB)
        gb_p = {"provider_id": 531, "provider_name": "Paramount+"}
        matched_gb = tmdb._match_core_service(gb_p, "GB", {"paramount_plus"})
        self.assertIsNotNone(matched_gb)

    def test_regional_services_matching(self):
        self.settings.update_settings(["netflix", "cbc_gem", "bbc_iplayer", "sbs_on_demand", "hulu"])
        tmdb = TmdbService(settings_service=self.settings)
        active = set(self.settings.get_enabled_services())

        # CBC Gem (Canada)
        gem = {"provider_id": 546, "provider_name": "CBC Gem"}
        self.assertIsNotNone(tmdb._match_core_service(gem, "CA", active))

        # BBC iPlayer (UK)
        bbc = {"provider_id": 38, "provider_name": "BBC iPlayer"}
        self.assertIsNotNone(tmdb._match_core_service(bbc, "GB", active))

        # SBS On Demand (Australia)
        sbs = {"provider_id": 300, "provider_name": "SBS On Demand"}
        self.assertIsNotNone(tmdb._match_core_service(sbs, "AU", active))

        # Hulu (US)
        hulu = {"provider_id": 15, "provider_name": "Hulu"}
        self.assertIsNotNone(tmdb._match_core_service(hulu, "US", active))

if __name__ == "__main__":
    unittest.main()
