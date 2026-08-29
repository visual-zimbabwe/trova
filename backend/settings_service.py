"""
Trova Settings & Streaming Service Preferences
Manages customizable active streaming providers with persistent JSON storage.
"""

import os
import json

ALL_SERVICES = [
    # Global Core
    {
        "id": "netflix",
        "name": "Netflix",
        "group": "Global Core",
        "region_badge": "Global",
        "color": "#E50914",
        "logo_url": "/assets/logos/netflix.png",
        "default": True
    },
    {
        "id": "prime",
        "name": "Prime Video",
        "group": "Global Core",
        "region_badge": "Global",
        "color": "#00A8E1",
        "logo_url": "/assets/logos/prime.png",
        "default": True
    },
    {
        "id": "max",
        "name": "Max",
        "group": "Global Core",
        "region_badge": "Global",
        "color": "#002BE7",
        "logo_url": "/assets/logos/max.png",
        "default": True
    },
    {
        "id": "paramount_plus",
        "name": "Paramount+",
        "group": "Global Core",
        "region_badge": "Global",
        "color": "#0064FF",
        "logo_url": "/assets/logos/paramount_plus.png",
        "default": True
    },
    {
        "id": "disney_plus",
        "name": "Disney+",
        "group": "Global Core",
        "region_badge": "Global",
        "color": "#113CCF",
        "logo_url": "/assets/logos/disney_plus.svg",
        "default": False
    },
    {
        "id": "apple_tv_plus",
        "name": "Apple TV+",
        "group": "Global Core",
        "region_badge": "Global",
        "color": "#000000",
        "logo_url": "/assets/logos/apple_tv_plus.svg",
        "default": False
    },
    # United States
    {
        "id": "hulu",
        "name": "Hulu",
        "group": "United States",
        "region_badge": "US",
        "color": "#1CE783",
        "logo_url": "/assets/logos/hulu.svg",
        "default": False
    },
    {
        "id": "peacock",
        "name": "Peacock",
        "group": "United States",
        "region_badge": "US",
        "color": "#000000",
        "logo_url": "/assets/logos/peacock.svg",
        "default": False
    },
    # Canada
    {
        "id": "cbc_gem",
        "name": "CBC Gem",
        "group": "Canada 🇨🇦",
        "region_badge": "Free VoD",
        "color": "#E60000",
        "logo_url": "/assets/logos/cbc_gem.svg",
        "default": False
    },
    # United Kingdom
    {
        "id": "bbc_iplayer",
        "name": "BBC iPlayer",
        "group": "United Kingdom 🇬🇧",
        "region_badge": "Free VoD",
        "color": "#F54997",
        "logo_url": "/assets/logos/bbc_iplayer.svg",
        "default": False
    },
    {
        "id": "channel4",
        "name": "Channel 4",
        "group": "United Kingdom 🇬🇧",
        "region_badge": "Free VoD",
        "color": "#000000",
        "logo_url": "/assets/logos/channel4.svg",
        "default": False
    },
    {
        "id": "itvx",
        "name": "ITVX",
        "group": "United Kingdom 🇬🇧",
        "region_badge": "Free VoD",
        "color": "#FFE500",
        "logo_url": "/assets/logos/itvx.svg",
        "default": False
    },
    # Australia
    {
        "id": "sbs_on_demand",
        "name": "SBS On Demand",
        "group": "Australia 🇦🇺",
        "region_badge": "Free VoD",
        "color": "#FA5900",
        "logo_url": "/assets/logos/sbs_on_demand.svg",
        "default": False
    },
    {
        "id": "abc_iview",
        "name": "ABC iview",
        "group": "Australia 🇦🇺",
        "region_badge": "Free VoD",
        "color": "#00A5D6",
        "logo_url": "/assets/logos/abc_iview.svg",
        "default": False
    }
]

DEFAULT_ENABLED_SERVICES = ["netflix", "prime", "max", "paramount_plus"]

class SettingsService:
    def __init__(self, config_dir=None):
        if config_dir is None:
            self.config_dir = os.path.expanduser("~/.config/trova")
        else:
            self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.settings_file = os.path.join(self.config_dir, "settings.json")

    def get_settings(self):
        enabled = list(DEFAULT_ENABLED_SERVICES)
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "enabled_services" in data:
                        saved = data.get("enabled_services", [])
                        valid_ids = {s["id"] for s in ALL_SERVICES}
                        filtered = [s for s in saved if s in valid_ids]
                        if filtered:
                            enabled = filtered
            except Exception as e:
                print(f"[SettingsService] Error loading settings: {e}")

        return {
            "services": ALL_SERVICES,
            "enabled_services": enabled
        }

    def get_enabled_services(self):
        return self.get_settings()["enabled_services"]

    def update_settings(self, enabled_services):
        valid_ids = {s["id"] for s in ALL_SERVICES}
        filtered = [s for s in enabled_services if s in valid_ids]
        if not filtered:
            filtered = list(DEFAULT_ENABLED_SERVICES)

        data = {
            "enabled_services": filtered
        }

        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SettingsService] Error saving settings: {e}")

        return {
            "services": ALL_SERVICES,
            "enabled_services": filtered
        }

    def reset_to_defaults(self):
        return self.update_settings(DEFAULT_ENABLED_SERVICES)
