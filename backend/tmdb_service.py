"""
OmaTrova TMDB API Service — Streamlined "Where to Stream" Engine
Resolves global streaming availability across Netflix, Prime Video, Max, and Paramount+ (USA only).
"""

import os
import json
import time
import sqlite3
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

TMDB_BASE = "https://api.themoviedb.org/3"
HARDCODED_BEARER_TOKEN = (
    "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4ZWNkNDE1YWJhY2VmMzYxM2I5NDc1MWQ5OWRhODU2YSIsIm5iZiI6MTc3MTgwMDUzOS45ODU5OTk4LCJzdWIiOiI2OTliODdkYmYwMTE1NmYxNDljNWE1MTgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.oXCB5rLBXE6TwtgHGup4lEEX-dI0uTXGUVP8PQesics"
)

# Standard Full Country Names Mapping (ISO 3166-1 alpha-2)
COUNTRY_NAMES = {
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "AG": "Antigua and Barbuda",
    "AI": "Anguilla",
    "AL": "Albania",
    "AM": "Armenia",
    "AO": "Angola",
    "AQ": "Antarctica",
    "AR": "Argentina",
    "AS": "American Samoa",
    "AT": "Austria",
    "AU": "Australia",
    "AW": "Aruba",
    "AX": "Aland Islands",
    "AZ": "Azerbaijan",
    "BA": "Bosnia and Herzegovina",
    "BB": "Barbados",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BF": "Burkina Faso",
    "BG": "Bulgaria",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BL": "Saint Barthelemy",
    "BM": "Bermuda",
    "BN": "Brunei Darussalam",
    "BO": "Bolivia",
    "BQ": "Bonaire, Sint Eustatius and Saba",
    "BR": "Brazil",
    "BS": "Bahamas",
    "BT": "Bhutan",
    "BV": "Bouvet Island",
    "BW": "Botswana",
    "BY": "Belarus",
    "BZ": "Belize",
    "CA": "Canada",
    "CC": "Cocos (Keeling) Islands",
    "CD": "Democratic Republic of the Congo",
    "CF": "Central African Republic",
    "CG": "Republic of the Congo",
    "CH": "Switzerland",
    "CI": "Cote d'Ivoire",
    "CK": "Cook Islands",
    "CL": "Chile",
    "CM": "Cameroon",
    "CN": "China",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "CV": "Cape Verde",
    "CW": "Curacao",
    "CX": "Christmas Island",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "EH": "Western Sahara",
    "ER": "Eritrea",
    "ES": "Spain",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FJ": "Fiji",
    "FK": "Falkland Islands",
    "FM": "Micronesia",
    "FO": "Faroe Islands",
    "FR": "France",
    "GA": "Gabon",
    "GB": "United Kingdom",
    "GD": "Grenada",
    "GE": "Georgia",
    "GF": "French Guiana",
    "GG": "Guernsey",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GL": "Greenland",
    "GM": "Gambia",
    "GN": "Guinea",
    "GP": "Guadeloupe",
    "GQ": "Equatorial Guinea",
    "GR": "Greece",
    "GS": "South Georgia and the South Sandwich Islands",
    "GT": "Guatemala",
    "GU": "Guam",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HK": "Hong Kong",
    "HM": "Heard and McDonald Islands",
    "HN": "Honduras",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IM": "Isle of Man",
    "IN": "India",
    "IO": "British Indian Ocean Territory",
    "IQ": "Iraq",
    "IR": "Iran",
    "IS": "Iceland",
    "IT": "Italy",
    "JE": "Jersey",
    "JM": "Jamaica",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KG": "Kyrgyzstan",
    "KH": "Cambodia",
    "KI": "Kiribati",
    "KM": "Comoros",
    "KN": "Saint Kitts and Nevis",
    "KP": "North Korea",
    "KR": "South Korea",
    "KW": "Kuwait",
    "KY": "Cayman Islands",
    "KZ": "Kazakhstan",
    "LA": "Laos",
    "LB": "Lebanon",
    "LC": "Saint Lucia",
    "LI": "Liechtenstein",
    "LK": "Sri Lanka",
    "LR": "Liberia",
    "LS": "Lesotho",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "LY": "Libya",
    "MA": "Morocco",
    "MC": "Monaco",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MF": "Saint Martin",
    "MG": "Madagascar",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar",
    "MN": "Mongolia",
    "MO": "Macao",
    "MP": "Northern Mariana Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MS": "Montserrat",
    "MT": "Malta",
    "MU": "Mauritius",
    "MV": "Maldives",
    "MW": "Malawi",
    "MX": "Mexico",
    "MY": "Malaysia",
    "MZ": "Mozambique",
    "NA": "Namibia",
    "NC": "New Caledonia",
    "NE": "Niger",
    "NF": "Norfolk Island",
    "NG": "Nigeria",
    "NI": "Nicaragua",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NR": "Nauru",
    "NU": "Niue",
    "NZ": "New Zealand",
    "OM": "Oman",
    "PA": "Panama",
    "PE": "Peru",
    "PF": "French Polynesia",
    "PG": "Papua New Guinea",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "PM": "Saint Pierre and Miquelon",
    "PN": "Pitcairn Islands",
    "PR": "Puerto Rico",
    "PS": "State of Palestine",
    "PT": "Portugal",
    "PW": "Palau",
    "PY": "Paraguay",
    "QA": "Qatar",
    "RE": "Reunion",
    "RO": "Romania",
    "RS": "Serbia",
    "RU": "Russia",
    "RW": "Rwanda",
    "SA": "Saudi Arabia",
    "SB": "Solomon Islands",
    "SC": "Seychelles",
    "SD": "Sudan",
    "SE": "Sweden",
    "SG": "Singapore",
    "SH": "Saint Helena",
    "SI": "Slovenia",
    "SJ": "Svalbard and Jan Mayen",
    "SK": "Slovakia",
    "SL": "Sierra Leone",
    "SM": "San Marino",
    "SN": "Senegal",
    "SO": "Somalia",
    "SR": "Suriname",
    "SS": "South Sudan",
    "ST": "Sao Tome and Principe",
    "SV": "El Salvador",
    "SX": "Sint Maarten",
    "SY": "Syria",
    "SZ": "Eswatini",
    "TC": "Turks and Caicos Islands",
    "TD": "Chad",
    "TF": "French Southern Territories",
    "TG": "Togo",
    "TH": "Thailand",
    "TJ": "Tajikistan",
    "TK": "Tokelau",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TN": "Tunisia",
    "TO": "Tonga",
    "TR": "Turkey",
    "TT": "Trinidad and Tobago",
    "TV": "Tuvalu",
    "TW": "Taiwan",
    "TZ": "Tanzania",
    "UA": "Ukraine",
    "UG": "Uganda",
    "UM": "United States Minor Outlying Islands",
    "US": "United States of America",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VA": "Holy See (Vatican City)",
    "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela",
    "VG": "British Virgin Islands",
    "VI": "United States Virgin Islands",
    "VN": "Vietnam",
    "VU": "Vanuatu",
    "WF": "Wallis and Futuna",
    "WS": "Samoa",
    "XK": "Kosovo",
    "YE": "Yemen",
    "YT": "Mayotte",
    "ZA": "South Africa",
    "ZM": "Zambia",
    "ZW": "Zimbabwe"
}

# Population & Popularity Sorting Priority
POPULARITY_RANK = {
    "US": 1, "GB": 2, "CA": 3, "AU": 4, "DE": 5, "FR": 6, "JP": 7, "NL": 8,
    "SE": 9, "ES": 10, "IT": 11, "BR": 12, "MX": 13, "IN": 14, "KR": 15, "AR": 16,
    "NZ": 17, "NO": 18, "DK": 19, "FI": 20, "CH": 21, "AT": 22, "PL": 23, "PT": 24,
    "BE": 25, "IE": 26, "ZA": 27, "SG": 28, "MY": 29, "CL": 30, "CO": 31, "PH": 32,
    "ID": 33, "TR": 34, "TH": 35, "IL": 36, "CZ": 37, "GR": 38, "RO": 39, "HU": 40,
    "HK": 41, "TW": 42
}

# Regional Continental Classifications
COUNTRY_REGIONS = {
    # North America
    "US": "North America", "CA": "North America", "MX": "North America", "BM": "North America", "GL": "North America", "PM": "North America",
    # Europe
    "GB": "Europe", "DE": "Europe", "FR": "Europe", "IT": "Europe", "ES": "Europe", "NL": "Europe", "SE": "Europe", "NO": "Europe",
    "DK": "Europe", "FI": "Europe", "CH": "Europe", "AT": "Europe", "BE": "Europe", "IE": "Europe", "PL": "Europe", "PT": "Europe",
    "CZ": "Europe", "GR": "Europe", "RO": "Europe", "HU": "Europe", "UA": "Europe", "HR": "Europe", "BG": "Europe", "SK": "Europe",
    "SI": "Europe", "EE": "Europe", "LV": "Europe", "LT": "Europe", "IS": "Europe", "LU": "Europe", "AL": "Europe", "AD": "Europe",
    "BA": "Europe", "CY": "Europe", "GI": "Europe", "LI": "Europe", "MC": "Europe", "MD": "Europe", "ME": "Europe", "MK": "Europe",
    "MT": "Europe", "RS": "Europe", "SM": "Europe", "VA": "Europe", "XK": "Europe", "GG": "Europe", "JE": "Europe", "IM": "Europe",
    # Asia-Pacific
    "AU": "Asia-Pacific", "NZ": "Asia-Pacific", "JP": "Asia-Pacific", "KR": "Asia-Pacific", "IN": "Asia-Pacific", "SG": "Asia-Pacific",
    "MY": "Asia-Pacific", "PH": "Asia-Pacific", "ID": "Asia-Pacific", "TH": "Asia-Pacific", "VN": "Asia-Pacific", "HK": "Asia-Pacific",
    "TW": "Asia-Pacific", "PK": "Asia-Pacific", "BD": "Asia-Pacific", "FJ": "Asia-Pacific", "KH": "Asia-Pacific", "LK": "Asia-Pacific",
    "MM": "Asia-Pacific", "MN": "Asia-Pacific", "NP": "Asia-Pacific", "PG": "Asia-Pacific", "MO": "Asia-Pacific", "PF": "Asia-Pacific",
    # Latin America
    "BR": "Latin America", "AR": "Latin America", "CL": "Latin America", "CO": "Latin America", "PE": "Latin America", "EC": "Latin America",
    "UY": "Latin America", "VE": "Latin America", "CR": "Latin America", "PA": "Latin America", "DO": "Latin America", "GT": "Latin America",
    "PR": "Latin America", "BO": "Latin America", "PY": "Latin America", "SV": "Latin America", "HN": "Latin America", "NI": "Latin America",
    "JM": "Latin America", "TT": "Latin America", "BS": "Latin America", "BB": "Latin America", "AG": "Latin America", "BZ": "Latin America",
    "CU": "Latin America", "CW": "Latin America", "DM": "Latin America", "GD": "Latin America", "GY": "Latin America", "HT": "Latin America",
    "KN": "Latin America", "LC": "Latin America", "SR": "Latin America", "VC": "Latin America", "AW": "Latin America", "MQ": "Latin America",
    "GP": "Latin America", "GF": "Latin America", "KY": "Latin America", "TC": "Latin America", "VG": "Latin America", "VI": "Latin America",
    # Middle East & Africa
    "IL": "Middle East & Africa", "TR": "Middle East & Africa", "AE": "Middle East & Africa", "SA": "Middle East & Africa", "EG": "Middle East & Africa",
    "ZA": "Middle East & Africa", "NG": "Middle East & Africa", "KE": "Middle East & Africa", "GH": "Middle East & Africa", "MA": "Middle East & Africa",
    "DZ": "Middle East & Africa", "JO": "Middle East & Africa", "KW": "Middle East & Africa", "LB": "Middle East & Africa", "OM": "Middle East & Africa",
    "QA": "Middle East & Africa", "TN": "Middle East & Africa", "BH": "Middle East & Africa", "IQ": "Middle East & Africa", "MU": "Middle East & Africa",
    "SN": "Middle East & Africa", "UG": "Middle East & Africa", "TZ": "Middle East & Africa", "CI": "Middle East & Africa", "CM": "Middle East & Africa",
    "ET": "Middle East & Africa", "AO": "Middle East & Africa", "ZW": "Middle East & Africa", "ZM": "Middle East & Africa", "MZ": "Middle East & Africa",
    "RE": "Middle East & Africa", "YT": "Middle East & Africa", "CV": "Middle East & Africa", "SZ": "Middle East & Africa", "BW": "Middle East & Africa"
}

REGION_METADATA = {
    "North America": {"emoji": "🌎", "order": 1},
    "Europe": {"emoji": "🌍", "order": 2},
    "Asia-Pacific": {"emoji": "🌏", "order": 3},
    "Latin America": {"emoji": "🌎", "order": 4},
    "Middle East & Africa": {"emoji": "🌍", "order": 5},
    "Other Regions": {"emoji": "🌐", "order": 6}
}

def get_flag_emoji(country_code):
    if len(country_code) == 2 and country_code.isalpha():
        return chr(ord(country_code[0].upper()) - 65 + 0x1F1E6) + chr(ord(country_code[1].upper()) - 65 + 0x1F1E6)
    return "🌐"

from location_service import LocationService

class TmdbService:
    def __init__(self, omdb_service=None, settings_service=None):
        self.omdb_service = omdb_service
        self.settings_service = settings_service
        self.location_service = LocationService()
        self.cache = {}
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        cache_dir = os.path.expanduser("~/.cache/trova")
        os.makedirs(cache_dir, exist_ok=True)
        self.db_cache_path = os.path.join(cache_dir, "tmdb_cache.db")
        self._init_cache_db()

    def _init_cache_db(self):
        try:
            with sqlite3.connect(self.db_cache_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tmdb_cache (
                        key TEXT PRIMARY KEY,
                        response TEXT NOT NULL,
                        cached_at REAL NOT NULL
                    )
                """)
                conn.commit()
        except Exception:
            pass

    def _get_cached_response(self, cache_key, ttl=86400):
        try:
            with sqlite3.connect(self.db_cache_path) as conn:
                cur = conn.execute("SELECT response, cached_at FROM tmdb_cache WHERE key = ?", (cache_key,))
                row = cur.fetchone()
                if row:
                    cached_json, cached_at = row[0], row[1]
                    if (time.time() - cached_at) < ttl:
                        return json.loads(cached_json)
        except Exception:
            pass
        return None

    def _set_cached_response(self, cache_key, data):
        try:
            blob = json.dumps(data)
            with sqlite3.connect(self.db_cache_path) as conn:
                conn.execute("""
                    INSERT INTO tmdb_cache (key, response, cached_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        response = excluded.response,
                        cached_at = excluded.cached_at
                """, (cache_key, blob, time.time()))
                conn.commit()
        except Exception:
            pass

    def _make_request(self, endpoint, params=None):
        if params is None:
            params = {}
        
        query_string = urllib.parse.urlencode(params)
        cache_key = f"{endpoint}?{query_string}" if query_string else endpoint

        # Check local persistent cache
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            return cached

        url = f"{TMDB_BASE}{endpoint}"
        if query_string:
            url = f"{url}?{query_string}"

        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {HARDCODED_BEARER_TOKEN}",
                "Accept": "application/json",
                "User-Agent": "Trova/2.0"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    self._set_cached_response(cache_key, data)
                    return data
        except Exception as e:
            print(f"[TMDB Error] {endpoint}: {e}")
        return None

    def search_multi(self, query, page=1):
        if not query or not query.strip():
            return {"results": [], "total_results": 0}

        data = self._make_request("/search/multi", {
            "query": query.strip(),
            "page": page,
            "include_adult": "false"
        })

        if not data or "results" not in data:
            return {"results": [], "total_results": 0}

        results = []
        for item in data["results"]:
            media_type = item.get("media_type")
            if media_type not in ("movie", "tv"):
                continue

            title = item.get("title") or item.get("name")
            release_date = item.get("release_date") or item.get("first_air_date")
            year = release_date[:4] if release_date else ""

            results.append({
                "id": item.get("id"),
                "media_type": media_type,
                "title": title,
                "year": year,
                "release_date": release_date,
                "vote_average": round(float(item.get("vote_average") or 0.0), 1),
                "vote_count": item.get("vote_count", 0),
                "popularity": item.get("popularity", 0),
                "poster_path": item.get("poster_path")
            })

        # Rank by vote count and popularity
        results.sort(key=lambda x: (x.get("vote_count", 0) or 0, x.get("popularity", 0) or 0), reverse=True)

        return {
            "results": results[:20],
            "total_results": data.get("total_results", len(results))
        }

    def get_details(self, media_type, tmdb_id, user_country=None):
        endpoint = f"/{media_type}/{tmdb_id}"
        data = self._make_request(endpoint, {
            "append_to_response": "watch/providers,videos"
        })

        if not data:
            return None

        title = data.get("title") or data.get("name") or "Unknown Title"
        release_date = data.get("release_date") or data.get("first_air_date")
        year = release_date[:4] if release_date else ""

        if not user_country:
            user_country = self.location_service.get_current_country_code()

        # Global country availability matrix & regional grouping
        raw_providers = data.get("watch/providers", {}).get("results", {})
        extracted = self._extract_watch_providers(raw_providers, user_country=user_country)

        # Extract official YouTube trailer
        trailer = None
        raw_videos = data.get("videos", {}).get("results", [])
        for v in raw_videos:
            if v.get("site") == "YouTube" and v.get("key"):
                v_type = v.get("type", "")
                if v_type in ("Trailer", "Teaser", "Clip"):
                    trailer = {
                        "key": v["key"],
                        "name": v.get("name", "Official Trailer"),
                        "type": v_type,
                        "url": f"https://www.youtube.com/watch?v={v['key']}"
                    }
                    if v_type == "Trailer":
                        break

        return {
            "id": data.get("id"),
            "media_type": media_type,
            "title": title,
            "year": year,
            "release_date": release_date,
            "countries": extracted["countries"],
            "regions": extracted["regions"],
            "service_counts": extracted["service_counts"],
            "local_country": extracted["local_country"],
            "trailer": trailer,
            "poster_path": data.get("poster_path"),
            "total_countries": len(extracted["countries"])
        }

    def _get_active_services_set(self):
        if self.settings_service:
            return set(self.settings_service.get_enabled_services())
        return {"netflix", "prime", "max", "paramount_plus"}

    def _match_core_service(self, provider, country_code, enabled_set=None):
        pid = provider.get("provider_id")
        name = (provider.get("provider_name") or "").lower()

        # 1. Netflix (Global)
        if pid in (8, 1796) or "netflix" in name:
            service_id = "netflix"
            service_name = "Netflix"
            color = "#E50914"
            logo = "/assets/logos/netflix.png"

        # 2. Amazon Prime Video (Global)
        elif pid in (9, 119, 10, 2100) or "prime video" in name or "amazon prime" in name or "amazon video" in name:
            service_id = "prime"
            service_name = "Prime Video"
            color = "#00A8E1"
            logo = "/assets/logos/prime.png"

        # 3. Max / HBO Max (Global)
        elif pid in (1899, 384, 1825) or "hbo max" in name or name == "max" or name.startswith("max ") or "max amazon" in name:
            service_id = "max"
            service_name = "Max"
            color = "#002BE7"
            logo = "/assets/logos/max.png"

        # 4. Paramount+ (GLOBAL - All Countries)
        elif pid in (531, 582, 633, 1773, 2303, 2616) or "paramount+" in name or "paramount plus" in name:
            service_id = "paramount_plus"
            service_name = "Paramount+"
            color = "#0064FF"
            logo = "/assets/logos/paramount_plus.png"

        # 5. Disney+ (Global)
        elif pid in (337,) or "disney+" in name or "disney plus" in name:
            service_id = "disney_plus"
            service_name = "Disney+"
            color = "#113CCF"
            logo = "/assets/logos/disney_plus.svg"

        # 6. Apple TV+ (Global)
        elif pid in (350, 2) or "apple tv+" in name or "apple tv plus" in name or (pid == 2 and "apple" in name):
            service_id = "apple_tv_plus"
            service_name = "Apple TV+"
            color = "#000000"
            logo = "/assets/logos/apple_tv_plus.svg"

        # 7. Hulu (USA / Global)
        elif pid in (15,) or "hulu" in name:
            service_id = "hulu"
            service_name = "Hulu"
            color = "#1CE783"
            logo = "/assets/logos/hulu.svg"

        # 8. Peacock (USA / Global)
        elif pid in (386, 387) or "peacock" in name:
            service_id = "peacock"
            service_name = "Peacock"
            color = "#000000"
            logo = "/assets/logos/peacock.svg"

        # 9. CBC Gem (Canada)
        elif pid in (546,) or "cbc gem" in name or "gem" in name:
            service_id = "cbc_gem"
            service_name = "CBC Gem"
            color = "#E60000"
            logo = "/assets/logos/cbc_gem.svg"

        # 10. BBC iPlayer (UK)
        elif pid in (38,) or "bbc iplayer" in name or (country_code == "GB" and "iplayer" in name):
            service_id = "bbc_iplayer"
            service_name = "BBC iPlayer"
            color = "#F54997"
            logo = "/assets/logos/bbc_iplayer.svg"

        # 11. Channel 4 (UK)
        elif pid in (103,) or "channel 4" in name or "all 4" in name or "all4" in name:
            service_id = "channel4"
            service_name = "Channel 4"
            color = "#000000"
            logo = "/assets/logos/channel4.svg"

        # 12. ITVX (UK)
        elif pid in (41,) or "itvx" in name or "itv hub" in name:
            service_id = "itvx"
            service_name = "ITVX"
            color = "#FFE500"
            logo = "/assets/logos/itvx.svg"

        # 13. SBS On Demand (Australia)
        elif pid in (300, 268) or "sbs on demand" in name or "sbs" in name:
            service_id = "sbs_on_demand"
            service_name = "SBS On Demand"
            color = "#FA5900"
            logo = "/assets/logos/sbs_on_demand.svg"

        # 14. ABC iview (Australia)
        elif pid in (305,) or "abc iview" in name or "iview" in name:
            service_id = "abc_iview"
            service_name = "ABC iview"
            color = "#00A5D6"
            logo = "/assets/logos/abc_iview.svg"

        else:
            return None

        # Filter by enabled services set
        if enabled_set is not None and service_id not in enabled_set:
            return None

        return {
            "id": service_id,
            "key": service_id,
            "name": service_name,
            "color": color,
            "logo_url": logo,
            "local_logo": logo
        }

    def _extract_watch_providers(self, results, user_country="CA"):
        target_code = (user_country or "CA").upper().strip()
        enabled_set = self._get_active_services_set()

        # Initialize dynamic service counts
        service_counts = {"all": 0}
        for s_id in enabled_set:
            service_counts[s_id] = 0

        if not results:
            return {
                "countries": [],
                "regions": [],
                "service_counts": service_counts,
                "local_country": {
                    "code": target_code,
                    "name": COUNTRY_NAMES.get(target_code, target_code),
                    "flag": get_flag_emoji(target_code),
                    "available": False,
                    "providers": []
                }
            }

        countries_list = []

        for code, c_data in results.items():
            streams = c_data.get("flatrate", []) + c_data.get("free", []) + c_data.get("ads", [])
            seen_keys = set()
            matched_providers = []

            for p in streams:
                service = self._match_core_service(p, code, enabled_set)
                if service and service["key"] not in seen_keys:
                    seen_keys.add(service["key"])
                    provider_entry = {
                        "id": service["id"],
                        "key": service["key"],
                        "name": service["name"],
                        "color": service["color"],
                        "logo_url": service["logo_url"],
                        "local_logo": service["local_logo"]
                    }
                    matched_providers.append(provider_entry)
                    if service["id"] in service_counts:
                        service_counts[service["id"]] += 1

            if matched_providers:
                country_name = COUNTRY_NAMES.get(code, code)
                flag = get_flag_emoji(code)
                rank = POPULARITY_RANK.get(code, 999)
                region = COUNTRY_REGIONS.get(code, "Other Regions")

                countries_list.append({
                    "code": code,
                    "name": country_name,
                    "flag": flag,
                    "rank": rank,
                    "region": region,
                    "providers": matched_providers
                })

        # Sort by popularity rank ascending, then by country name
        countries_list.sort(key=lambda c: (c["rank"], c["name"]))
        service_counts["all"] = len(countries_list)

        # Dynamic Local country resolution
        local_country_entry = next((c for c in countries_list if c["code"] == target_code), None)
        if local_country_entry:
            local_country = {
                "code": target_code,
                "name": local_country_entry["name"],
                "flag": local_country_entry["flag"],
                "available": True,
                "providers": local_country_entry["providers"]
            }
        else:
            local_country = {
                "code": target_code,
                "name": COUNTRY_NAMES.get(target_code, target_code),
                "flag": get_flag_emoji(target_code),
                "available": False,
                "providers": []
            }

        # Group by regions
        region_buckets = {}
        for c in countries_list:
            r = c.get("region", "Other Regions")
            if r not in region_buckets:
                region_buckets[r] = []
            region_buckets[r].append(c)

        regions_list = []
        for r_name, r_countries in region_buckets.items():
            meta = REGION_METADATA.get(r_name, {"emoji": "🌐", "order": 99})
            regions_list.append({
                "name": r_name,
                "emoji": meta["emoji"],
                "order": meta["order"],
                "total": len(r_countries),
                "countries": r_countries
            })

        regions_list.sort(key=lambda x: x["order"])

        return {
            "countries": countries_list,
            "regions": regions_list,
            "service_counts": service_counts,
            "local_country": local_country
        }

    def discover(self, media_type="movie", **kwargs):
        # Kept for backward compatibility
        return {"results": []}

    def get_trending_home(self):
        # Kept for backward compatibility
        return {"results": []}

