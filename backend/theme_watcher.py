"""
Trova Real-Time Omarchy Theme Watcher & Palette Synthesizer
Monitors Omarchy colors.toml and broadcasts SSE theme updates to WebKitGTK UI.
Provides complete, dynamic CSS color tokens
for both dark and light Omarchy themes (Evergreen, Oligarchy, Nord, Gruvbox, etc.).
"""

import os
import json
import time
import threading

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{max(0, min(255, int(r))):02x}{max(0, min(255, int(g))):02x}{max(0, min(255, int(b))):02x}"

def get_luminance(hex_str):
    try:
        r, g, b = hex_to_rgb(hex_str)
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    except Exception:
        return 0.0

def adjust_brightness(hex_str, factor):
    try:
        r, g, b = hex_to_rgb(hex_str)
        return rgb_to_hex(r * factor, g * factor, b * factor)
    except Exception:
        return hex_str

def blend_colors(hex_a, hex_b, ratio):
    try:
        r1, g1, b1 = hex_to_rgb(hex_a)
        r2, g2, b2 = hex_to_rgb(hex_b)
        r = r1 * (1 - ratio) + r2 * ratio
        g = g1 * (1 - ratio) + g2 * ratio
        b = b1 * (1 - ratio) + b2 * ratio
        return rgb_to_hex(r, g, b)
    except Exception:
        return hex_a

def hex_to_rgba(hex_str, alpha=0.9):
    try:
        r, g, b = hex_to_rgb(hex_str)
        return f"rgba({r}, {g}, {b}, {alpha})"
    except Exception:
        return hex_str

class ThemeWatcher:
    def __init__(self, on_theme_change_callback=None):
        self.callback = on_theme_change_callback
        self.home = os.path.expanduser("~")
        self.state_dir = os.path.join(self.home, ".local", "state", "omarchy", "current")
        self.theme_name_file = os.path.join(self.state_dir, "theme.name")
        self.colors_toml_file = os.path.join(self.state_dir, "theme", "colors.toml")
        self.vscode_theme_file = os.path.join(self.state_dir, "theme", "vscode-theme.json")
        self.last_theme_name = None
        self.last_colors_mtime = 0
        self.is_running = False
        self.thread = None

    def get_current_theme_data(self):
        """Reads current colors and synthesizes complete token set from Omarchy."""
        theme_name = "Evergreen"
        if os.path.exists(self.theme_name_file):
            try:
                with open(self.theme_name_file, "r") as f:
                    raw = f.read().strip()
                    if raw:
                        theme_name = raw.replace("-", " ").title()
            except Exception:
                pass

        raw_colors = self._parse_colors_toml(self.colors_toml_file)
        if not raw_colors:
            # Fallback to ~/.config/omarchy/themes/evergreen/colors.toml
            fallback = os.path.join(self.home, ".config", "omarchy", "themes", "evergreen", "colors.toml")
            raw_colors = self._parse_colors_toml(fallback)

        synthesized = self._synthesize_palette(raw_colors, theme_name)

        return {
            "name": theme_name,
            "mode": synthesized["mode"],
            "colors": synthesized,
            "raw": raw_colors
        }

    def _synthesize_palette(self, raw, theme_name):
        bg = raw.get("background", "#101913")
        fg = raw.get("foreground", "#a1af9c")
        accent = raw.get("accent", "#4a9a68")

        # Determine light or dark mode
        mode_hint = raw.get("mode")
        lum = get_luminance(bg)
        is_light = (mode_hint == "light") or (lum > 0.45)
        mode = "light" if is_light else "dark"

        if is_light:
            # Light Mode (e.g. Oligarchy)
            bg_base = bg
            bg_root = raw.get("darker_background") or blend_colors(bg, "#000000", 0.06)
            bg_surface = raw.get("dark_background") or blend_colors(bg, "#ffffff", 0.35)
            bg_card = blend_colors(bg, "#ffffff", 0.75)
            bg_hover = blend_colors(bg, accent, 0.12)
            bg_selected = raw.get("selection_background") or blend_colors(bg, accent, 0.22)
            bg_glass = hex_to_rgba(bg_surface, 0.92)
            bg_modal = hex_to_rgba(bg_surface, 0.98)

            text_title = raw.get("bright_foreground") or fg
            text_primary = raw.get("color7") or blend_colors(fg, bg, 0.15)
            text_secondary = raw.get("color8") or blend_colors(fg, bg, 0.45)
            text_muted = blend_colors(fg, bg, 0.65)
            text_on_accent = "#ffffff" if get_luminance(accent) < 0.5 else "#000000"

            border = blend_colors(bg, fg, 0.22)
            border_light = blend_colors(bg, fg, 0.12)
            border_focus = accent

            accent_hover = raw.get("color9") or adjust_brightness(accent, 0.85)
            accent_dim = hex_to_rgba(accent, 0.18)
            accent_glow = hex_to_rgba(accent, 0.25)

            badge_imdb = raw.get("yellow") or raw.get("color3") or "#a9791f"
            badge_rt = raw.get("red") or raw.get("color1") or "#c0271c"
            badge_meta = raw.get("green") or raw.get("color2") or "#5e6b33"
            badge_tmdb = raw.get("blue") or raw.get("color4") or "#3e5a78"
            gold = raw.get("color11") or raw.get("color3") or "#a9791f"

        else:
            # Dark Mode (e.g. Evergreen, Dark Omarchy)
            bg_base = bg
            bg_root = raw.get("darker_background") or adjust_brightness(bg, 0.65)
            bg_surface = raw.get("dark_background") or adjust_brightness(bg, 0.85)
            bg_card = adjust_brightness(bg, 1.25)
            bg_hover = raw.get("lighter_background") or adjust_brightness(bg, 1.7)
            bg_selected = raw.get("selection") or raw.get("selection_background") or adjust_brightness(bg, 2.0)
            bg_glass = hex_to_rgba(bg_surface, 0.88)
            bg_modal = hex_to_rgba(bg_root, 0.95)

            text_title = raw.get("bright_foreground") or "#ffffff"
            text_primary = raw.get("light_foreground") or fg
            text_secondary = fg
            text_muted = raw.get("muted") or raw.get("dark_foreground") or blend_colors(fg, bg, 0.5)
            text_on_accent = "#000000" if get_luminance(accent) > 0.4 else "#ffffff"

            border = raw.get("muted") or blend_colors(bg, fg, 0.2)
            border_light = hex_to_rgba(border, 0.3)
            border_focus = accent

            accent_hover = raw.get("bright_green") or raw.get("bright_blue") or adjust_brightness(accent, 1.25)
            accent_dim = hex_to_rgba(accent, 0.25)
            accent_glow = hex_to_rgba(accent, 0.35)

            badge_imdb = raw.get("yellow") or raw.get("bright_yellow") or "#c4a64e"
            badge_rt = raw.get("red") or raw.get("bright_red") or "#c87a5c"
            badge_meta = raw.get("green") or raw.get("bright_green") or "#6aae52"
            badge_tmdb = raw.get("cyan") or raw.get("blue") or "#52987a"
            gold = "#d4a853"

        return {
            "mode": mode,
            "bg_base": bg_base,
            "bg_root": bg_root,
            "bg_surface": bg_surface,
            "bg_card": bg_card,
            "bg_hover": bg_hover,
            "bg_selected": bg_selected,
            "bg_glass": bg_glass,
            "bg_modal": bg_modal,
            "text_title": text_title,
            "text_primary": text_primary,
            "text_secondary": text_secondary,
            "text_muted": text_muted,
            "text_on_accent": text_on_accent,
            "border": border,
            "border_light": border_light,
            "border_focus": border_focus,
            "accent": accent,
            "accent_hover": accent_hover,
            "accent_dim": accent_dim,
            "accent_glow": accent_glow,
            "gold": gold,
            "badge_imdb": badge_imdb,
            "badge_rt": badge_rt,
            "badge_meta": badge_meta,
            "badge_tmdb": badge_tmdb
        }

    def _parse_colors_toml(self, path):
        if not os.path.exists(path):
            return {}
        result = {}
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        result[k] = v
        except Exception:
            pass
        return result

    def _read_vscode_theme(self, path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False

    def _watch_loop(self):
        while self.is_running:
            try:
                current_data = self.get_current_theme_data()
                current_name = current_data["name"]
                mtime = os.path.getmtime(self.colors_toml_file) if os.path.exists(self.colors_toml_file) else 0

                if current_name != self.last_theme_name or mtime != self.last_colors_mtime:
                    self.last_theme_name = current_name
                    self.last_colors_mtime = mtime
                    if self.callback:
                        self.callback(current_data)
            except Exception:
                pass
            time.sleep(0.3)
