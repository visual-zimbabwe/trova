import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from test_theme_watcher import TestThemeWatcher
from test_watchlist import TestWatchlist
from test_favorites import TestFavoritesDb
from test_favorites_categories import TestFavoritesCategories
from test_analytics import TestAnalytics
from test_backend_api import TestBackendApi

def suite():
    loader = unittest.defaultTestLoader
    s = unittest.TestSuite()
    s.addTests(loader.loadTestsFromTestCase(TestThemeWatcher))
    s.addTests(loader.loadTestsFromTestCase(TestWatchlist))
    s.addTests(loader.loadTestsFromTestCase(TestFavoritesDb))
    s.addTests(loader.loadTestsFromTestCase(TestFavoritesCategories))
    s.addTests(loader.loadTestsFromTestCase(TestAnalytics))
    s.addTests(loader.loadTestsFromTestCase(TestBackendApi))
    return s

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite())
    sys.exit(0 if res.wasSuccessful() else 1)
