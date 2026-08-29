import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from theme_watcher import ThemeWatcher

class TestThemeWatcher(unittest.TestCase):
    def setUp(self):
        self.watcher = ThemeWatcher()

    def test_theme_data_structure(self):
        data = self.watcher.get_current_theme_data()
        self.assertIn("name", data)
        self.assertIn("mode", data)
        self.assertIn("colors", data)
        colors = data["colors"]
        self.assertIn("bg_base", colors)
        self.assertIn("bg_root", colors)
        self.assertIn("bg_surface", colors)
        self.assertIn("text_title", colors)
        self.assertIn("accent", colors)

    def test_light_mode_synthesis(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("""
accent = "#c0271c"
foreground = "#1a160f"
background = "#eae0cb"
selection_background = "#c0271c"
""")
            temp_path = f.name

        try:
            raw = self.watcher._parse_colors_toml(temp_path)
            synthesized = self.watcher._synthesize_palette(raw, "Oligarchy")
            self.assertEqual(synthesized["mode"], "light")
            self.assertEqual(synthesized["bg_base"], "#eae0cb")
            self.assertEqual(synthesized["accent"], "#c0271c")
            self.assertEqual(synthesized["text_on_accent"], "#ffffff")
        finally:
            os.remove(temp_path)

    def test_dark_mode_synthesis(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("""
accent = "#4a9a68"
foreground = "#a1af9c"
background = "#101913"
""")
            temp_path = f.name

        try:
            raw = self.watcher._parse_colors_toml(temp_path)
            synthesized = self.watcher._synthesize_palette(raw, "Evergreen")
            self.assertEqual(synthesized["mode"], "dark")
            self.assertEqual(synthesized["bg_base"], "#101913")
            self.assertEqual(synthesized["accent"], "#4a9a68")
        finally:
            os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
