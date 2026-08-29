"""
Trova Dynamic Location Resolution Engine
Resolves current user location across 5 prioritized tiers:
1. NordVPN Active Exit Country (if connected)
2. User Config Override (~/.config/trova/config.json)
3. System Timezone (America/Vancouver -> CA, etc.)
4. Cached IP Geolocation
5. System Locale (LANG environment variable)
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
from pathlib import Path

# Comprehensive IANA Timezone to ISO-3166-1 alpha-2 mapping
TIMEZONE_MAP = {
    # Canada
    "America/Vancouver": "CA", "America/Toronto": "CA", "America/Edmonton": "CA",
    "America/Winnipeg": "CA", "America/Halifax": "CA", "America/St_Johns": "CA",
    "America/Regina": "CA", "America/Montreal": "CA", "America/Calgary": "CA",
    "America/Ottawa": "CA", "America/Quebec": "CA", "America/Victoria": "CA",
    "America/Whitehorse": "CA", "America/Yellowknife": "CA", "America/Iqaluit": "CA",
    
    # United States
    "America/New_York": "US", "America/Chicago": "US", "America/Los_Angeles": "US",
    "America/Denver": "US", "America/Phoenix": "US", "America/Detroit": "US",
    "America/Anchorage": "US", "America/Honolulu": "US", "America/Boise": "US",
    "America/Indiana/Indianapolis": "US", "America/Kentucky/Louisville": "US",
    "America/Adak": "US", "America/Menominee": "US", "America/Juneau": "US",
    
    # United Kingdom & Ireland
    "Europe/London": "GB", "Europe/Belfast": "GB", "Europe/Dublin": "IE",
    
    # Europe
    "Europe/Berlin": "DE", "Europe/Paris": "FR", "Europe/Rome": "IT",
    "Europe/Madrid": "ES", "Europe/Amsterdam": "NL", "Europe/Stockholm": "SE",
    "Europe/Oslo": "NO", "Europe/Copenhagen": "DK", "Europe/Helsinki": "FI",
    "Europe/Zurich": "CH", "Europe/Vienna": "AT", "Europe/Warsaw": "PL",
    "Europe/Lisbon": "PT", "Europe/Brussels": "BE", "Europe/Prague": "CZ",
    "Europe/Athens": "GR", "Europe/Bucharest": "RO", "Europe/Budapest": "HU",
    "Europe/Zagreb": "HR", "Europe/Sofia": "BG", "Europe/Bratislava": "SK",
    "Europe/Ljubljana": "SI", "Europe/Tallinn": "EE", "Europe/Riga": "LV",
    "Europe/Vilnius": "LT", "Atlantic/Reykjavik": "IS", "Europe/Luxembourg": "LU",
    "Europe/Kyiv": "UA", "Europe/Belgrade": "RS", "Europe/Sarajevo": "BA",
    
    # Asia-Pacific
    "Australia/Sydney": "AU", "Australia/Melbourne": "AU", "Australia/Brisbane": "AU",
    "Australia/Perth": "AU", "Australia/Adelaide": "AU", "Australia/Hobart": "AU",
    "Pacific/Auckland": "NZ", "Asia/Tokyo": "JP", "Asia/Seoul": "KR",
    "Asia/Kolkata": "IN", "Asia/Calcutta": "IN", "Asia/Singapore": "SG",
    "Asia/Kuala_Lumpur": "MY", "Asia/Manila": "PH", "Asia/Jakarta": "ID",
    "Asia/Bangkok": "TH", "Asia/Ho_Chi_Minh": "VN", "Asia/Hong_Kong": "HK",
    "Asia/Taipei": "TW", "Asia/Karachi": "PK", "Asia/Dhaka": "BD",
    
    # Latin America
    "America/Sao_Paulo": "BR", "America/Rio_Branco": "BR", "America/Manaus": "BR",
    "America/Mexico_City": "MX", "America/Tijuana": "MX", "America/Monterrey": "MX",
    "America/Argentina/Buenos_Aires": "AR", "America/Buenos_Aires": "AR",
    "America/Santiago": "CL", "America/Bogota": "CO", "America/Lima": "PE",
    "America/Guayaquil": "EC", "America/Montevideo": "UY", "America/Caracas": "VE",
    "America/Costa_Rica": "CR", "America/Panama": "PA", "America/Santo_Domingo": "DO",
    "America/Guatemala": "GT", "America/Puerto_Rico": "PR",
    
    # Middle East & Africa
    "Asia/Jerusalem": "IL", "Europe/Istanbul": "TR", "Asia/Dubai": "AE",
    "Asia/Riyadh": "SA", "Africa/Cairo": "EG", "Africa/Johannesburg": "ZA",
    "Africa/Lagos": "NG", "Africa/Nairobi": "KE", "Africa/Casablanca": "MA",
    "Africa/Accra": "GH", "Africa/Algiers": "DZ", "Africa/Tunis": "TN"
}

class LocationService:
    def __init__(self):
        self._cached_country = None
        self._last_resolved_time = 0
        self._cache_ttl = 30  # Re-check signals every 30s to catch VPN connections

    def get_current_country_code(self) -> str:
        now = time.time()
        if self._cached_country and (now - self._last_resolved_time) < self._cache_ttl:
            return self._cached_country

        country = (
            self._check_nordvpn() or
            self._check_user_config() or
            self._check_system_timezone() or
            self._check_ip_geolocation() or
            self._check_system_locale() or
            "CA"  # Fallback to Canada based on system timezone
        )

        self._cached_country = country.upper().strip()
        self._last_resolved_time = now
        return self._cached_country

    def _check_nordvpn(self):
        """Tier 1: Detect active NordVPN exit connection"""
        import shutil
        if not shutil.which("nordvpn"):
            return None
        try:
            res = subprocess.run(["nordvpn", "status"], capture_output=True, text=True, timeout=0.8)
            if res.returncode == 0 and "Status: Connected" in res.stdout:
                for line in res.stdout.splitlines():
                    if line.strip().startswith("Country:"):
                        country_name = line.split(":", 1)[1].strip()
                        # Map common country names to ISO
                        name_lower = country_name.lower()
                        if "united states" in name_lower or name_lower == "usa":
                            return "US"
                        elif "canada" in name_lower:
                            return "CA"
                        elif "united kingdom" in name_lower or "uk" in name_lower or "britain" in name_lower:
                            return "GB"
                        elif "australia" in name_lower:
                            return "AU"
                        elif "germany" in name_lower:
                            return "DE"
                        elif "france" in name_lower:
                            return "FR"
                        elif "japan" in name_lower:
                            return "JP"
                        elif "netherlands" in name_lower:
                            return "NL"
        except Exception:
            pass
        return None

    def _check_user_config(self):
        """Tier 2: Check ~/.config/trova/config.json"""
        for config_path in [
            Path.home() / ".config" / "trova" / "config.json"
        ]:
            if config_path.exists():
                try:
                    data = json.loads(config_path.read_text(encoding="utf-8"))
                    home_c = data.get("home_country")
                    if home_c and home_c.upper() != "AUTO" and len(home_c) == 2:
                        return home_c.upper()
                except Exception:
                    pass
        return None

    def _check_system_timezone(self):
        """Tier 3: Check system timezone via /etc/localtime symlink or timedatectl"""
        tz = None
        # 1. Fast readlink /etc/localtime (< 0.1ms)
        if os.path.islink("/etc/localtime"):
            try:
                target = os.readlink("/etc/localtime")
                if "zoneinfo/" in target:
                    tz = target.split("zoneinfo/", 1)[1].strip()
            except Exception:
                pass

        # 2. /etc/timezone fallback
        if not tz and os.path.exists("/etc/timezone"):
            try:
                with open("/etc/timezone", "r", encoding="utf-8") as f:
                    tz = f.read().strip()
            except Exception:
                pass

        # 3. timedatectl fallback
        if not tz:
            try:
                res = subprocess.run(["timedatectl"], capture_output=True, text=True, timeout=0.8)
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if "Time zone:" in line:
                            parts = line.split("Time zone:", 1)[1].strip().split()
                            if parts:
                                tz = parts[0]
                                break
            except Exception:
                pass

        if tz and tz in TIMEZONE_MAP:
            return TIMEZONE_MAP[tz]

        return None

    def _check_ip_geolocation(self):
        """Tier 4: Fast cached public IP geolocation"""
        try:
            req = urllib.request.Request("https://ifconfig.co/country-iso", headers={"User-Agent": "Trova/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                code = resp.read().decode("utf-8").strip()
                if len(code) == 2 and code.isalpha():
                    return code.upper()
        except Exception:
            pass
        return None

    def _check_system_locale(self):
        """Tier 5: System locale LANG"""
        lang = os.environ.get("LANG", "")
        if "_" in lang:
            country_part = lang.split("_", 1)[1].split(".", 1)[0]
            if len(country_part) == 2 and country_part.isalpha():
                return country_part.upper()
        return None

