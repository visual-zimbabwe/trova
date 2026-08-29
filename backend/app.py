"""
Trova Core Backend Application Server
Provides REST API, static asset delivery, and live Omarchy theme synchronization.
"""

import os
import sys
import json
import time
import urllib.parse
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

# Import backend services
sys.path.insert(0, os.path.dirname(__file__))
from theme_watcher import ThemeWatcher
from omdb_service import OmdbService
from tmdb_service import TmdbService
from wikidata_service import WikidataService
from mpv_service import MpvService
from watchlist_db import WatchlistDb
from letterboxd_service import LetterboxdService
from analytics_service import AnalyticsService
from catalog_cache import CatalogCache
from favorites_db import FavoritesDb
from settings_service import SettingsService

class RecentSearchesService:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/trova")
        os.makedirs(self.config_dir, exist_ok=True)
        self.file_path = os.path.join(self.config_dir, "recent_searches.json")
        self.default_items = [
            "Interstellar",
            "Stranger Things",
            "Dune: Part Two",
            "Succession",
            "The Dark Knight"
        ]

    def get_recent(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return [str(item) for item in data if item][:5]
            except Exception:
                pass
        return list(self.default_items)

    def add_search(self, query):
        if not query or not isinstance(query, str):
            return self.get_recent()
        clean = query.strip()
        if not clean:
            return self.get_recent()

        current = self.get_recent()
        current = [item for item in current if item.lower() != clean.lower()]
        current.insert(0, clean)
        current = current[:5]

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RecentSearches Error] {e}")
        return current

class TrovaServer:
    def __init__(self, port=8899, static_dir=None):
        self.port = port
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_dir = static_dir or os.path.join(self.root_dir, "frontend")
        
        # Initialize services
        self.settings_service = SettingsService()
        self.favorites_db = FavoritesDb()
        self.recent_searches_service = RecentSearchesService()
        self.theme_watcher = ThemeWatcher(on_theme_change_callback=self._on_theme_change)
        self.omdb_service = OmdbService()
        self.tmdb_service = TmdbService(omdb_service=self.omdb_service, settings_service=self.settings_service)
        self.wikidata_service = WikidataService()
        self.mpv_service = MpvService()
        self.watchlist_db = WatchlistDb()
        self.letterboxd_service = LetterboxdService(self.tmdb_service, self.watchlist_db)
        self.analytics_service = AnalyticsService(self.watchlist_db, self.tmdb_service)
        self.catalog_cache = CatalogCache(os.path.join(self.root_dir, "assets"))

        self.sse_clients = []
        self.sse_lock = threading.Lock()

    def _on_theme_change(self, new_theme_data):
        payload = f"data: {json.dumps(new_theme_data)}\n\n"
        with self.sse_lock:
            active_clients = []
            for client_wfile in self.sse_clients:
                try:
                    client_wfile.write(payload.encode("utf-8"))
                    client_wfile.flush()
                    active_clients.append(client_wfile)
                except Exception:
                    pass
            self.sse_clients = active_clients

    def run(self):
        self.theme_watcher.start()
        handler_factory = self._create_handler()
        httpd = ThreadingHTTPServer(("127.0.0.1", self.port), handler_factory)
        print(f"[Trova Server] Running at http://127.0.0.1:{self.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            self.theme_watcher.stop()
            httpd.server_close()

    def _create_handler(server_self):
        class TrovaHandler(SimpleHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=server_self.static_dir, **kwargs)

            def end_headers(self):
                # Force Connection: close on all responses to prevent WebKit
                # from holding idle keep-alive connections that exhaust the
                # browser's per-host connection limit (typically 6).
                self.send_header("Connection", "close")
                super().end_headers()

            def log_message(self, format, *args):
                # Silence standard asset access logs
                pass

            def _timed_log(self, path, start_time):
                elapsed = (time.time() - start_time) * 1000
                if elapsed > 50 and '/api/' in path:
                    print(f"[Trova Slow] {path} took {elapsed:.0f}ms")

            def send_json(self, data, status=200):
                blob = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(blob)))
                self.send_header("Connection", "close")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()
                self.wfile.write(blob)

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self):
                _req_start = time.time()
                parsed = urllib.parse.urlparse(self.path)
                path = parsed.path
                query = urllib.parse.parse_qs(parsed.query)

                # SSE Theme Event Stream
                if path == "/api/events":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "keep-alive")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()

                    # Send immediate theme state
                    try:
                        init_data = server_self.theme_watcher.get_current_theme_data()
                        init_blob = f"data: {json.dumps(init_data)}\n\n".encode("utf-8")
                        self.wfile.write(init_blob)
                        self.wfile.flush()
                    except Exception:
                        return

                    with server_self.sse_lock:
                        server_self.sse_clients.append(self.wfile)

                    try:
                        while True:
                            time.sleep(15)
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                    except Exception:
                        pass
                    finally:
                        with server_self.sse_lock:
                            if self.wfile in server_self.sse_clients:
                                server_self.sse_clients.remove(self.wfile)
                    return

                # API: Theme
                if path == "/api/theme":
                    return self.send_json(server_self.theme_watcher.get_current_theme_data())

                # API: Home Feed
                if path == "/api/home":
                    home_data = server_self.tmdb_service.get_trending_home()
                    home_data["franchises"] = server_self.catalog_cache.get_featured_franchises(8)
                    return self.send_json(home_data)

                # API: Search Multi
                if path == "/api/search":
                    q = query.get("q", [""])[0]
                    page = int(query.get("page", [1])[0])
                    result = server_self.tmdb_service.search_multi(q, page=page)
                    self._timed_log(f"/api/search?q={q}", _req_start)
                    return self.send_json(result)

                # API: Discover
                if path == "/api/discover":
                    media_type = query.get("media_type", ["movie"])[0]
                    kwargs = {
                        "page": int(query.get("page", [1])[0]),
                        "sort_by": query.get("sort_by", ["popularity.desc"])[0],
                        "with_genres": query.get("with_genres", [None])[0],
                        "without_genres": query.get("without_genres", [None])[0],
                        "year_min": query.get("year_min", [None])[0],
                        "year_max": query.get("year_max", [None])[0],
                        "vote_min": query.get("vote_min", [None])[0],
                        "with_origin_country": query.get("with_origin_country", [None])[0],
                        "with_original_language": query.get("with_original_language", [None])[0],
                        "without_keywords": query.get("without_keywords", [None])[0]
                    }
                    return self.send_json(server_self.tmdb_service.discover(media_type=media_type, **kwargs))

                # API: Settings Get
                if path == "/api/settings":
                    return self.send_json(server_self.settings_service.get_settings())

                # API: Favorites Summary (Sub-millisecond total, movies, and TV counts)
                if path == "/api/favorites/summary":
                    return self.send_json(server_self.favorites_db.get_summary())

                # API: Favorites Shelf (Recent favorites grouped by Movies and TV)
                if path == "/api/favorites/shelf":
                    return self.send_json(server_self.favorites_db.get_shelf_items())

                # API: Favorites Compact ID List (for instant in-memory star checks)
                if path == "/api/favorites/ids":
                    return self.send_json({"ids": server_self.favorites_db.get_favorite_ids()})

                # API: Favorites Get (with optional media_type filter, pagination & search)
                if path == "/api/favorites":
                    m_type = query.get("media_type", [None])[0]
                    sort_by = query.get("sort_by", ["added_at_desc"])[0]
                    q = query.get("q", [None])[0]
                    limit = int(query.get("limit", [0])[0]) or None
                    offset = int(query.get("offset", [0])[0])

                    favs = server_self.favorites_db.get_all(
                        media_type=m_type,
                        sort_by=sort_by,
                        offset=offset,
                        limit=limit,
                        search=q
                    )
                    return self.send_json({
                        "favorites": favs,
                        "count": len(favs),
                        "offset": offset,
                        "limit": limit
                    })

                # API: Recent Searches
                if path == "/api/recent_searches":
                    return self.send_json({"results": server_self.recent_searches_service.get_recent()})

                # API: Title Details
                if path == "/api/details":
                    m_type = query.get("type", ["movie"])[0]
                    t_id = query.get("id", [""])[0]
                    if not t_id:
                        return self.send_json({"error": "Missing ID"}, 400)
                    details = server_self.tmdb_service.get_details(m_type, t_id)
                    if details:
                        # Automatically record into persistent recent searches
                        if details.get("title"):
                            server_self.recent_searches_service.add_search(details["title"])
                        # Append favorite status
                        fav_status = server_self.favorites_db.is_favorite(t_id, m_type)
                        details["is_favorite"] = fav_status.get("is_favorite", False)
                        # Append watchlist status
                        wl_status = server_self.watchlist_db.is_in_watchlist(t_id, m_type)
                        details["in_watchlist"] = wl_status["in_watchlist"]
                        details["tier"] = wl_status["tier"]
                        self._timed_log(f"/api/details?type={m_type}&id={t_id}", _req_start)
                        return self.send_json(details)
                    return self.send_json({"error": "Not found"}, 404)

                # API: Person Details
                if path == "/api/person":
                    p_id = query.get("id", [""])[0]
                    if not p_id:
                        return self.send_json({"error": "Missing person ID"}, 400)
                    person = server_self.tmdb_service.get_person(p_id)
                    return self.send_json(person or {"error": "Not found"})

                # API: Collection / Franchise
                if path == "/api/collection":
                    c_id = query.get("id", [""])[0]
                    collection = server_self.tmdb_service.get_collection(c_id)
                    if not collection:
                        collection = server_self.catalog_cache.get_franchise(int(c_id) if c_id.isdigit() else 0)
                    return self.send_json(collection or {"error": "Not found"})

                # API: Soundtracks
                if path == "/api/soundtracks":
                    title = query.get("title", [""])[0]
                    year = query.get("year", [""])[0]
                    tracks = server_self.wikidata_service.get_soundtracks(title, year)
                    return self.send_json({"tracks": tracks})

                # API: Watchlist Get
                if path == "/api/watchlist":
                    tier = query.get("tier", [None])[0]
                    media_type = query.get("media_type", [None])[0]
                    sort_by = query.get("sort_by", ["added_at_desc"])[0]
                    items = server_self.watchlist_db.get_items(tier=tier, media_type=media_type, sort_by=sort_by)
                    return self.send_json({"items": items, "total": len(items)})

                # API: Watchlist Status
                if path == "/api/watchlist/status":
                    t_id = query.get("id", [""])[0]
                    m_type = query.get("type", ["movie"])[0]
                    return self.send_json(server_self.watchlist_db.is_in_watchlist(t_id, m_type))

                # API: Watchlist Random Recommendation
                if path == "/api/watchlist/random":
                    tier = query.get("tier", ["highly_recommend"])[0]
                    rec = server_self.watchlist_db.get_random_recommendation(tier)
                    return self.send_json(rec or {"error": "No recommendation found"})

                # API: Watchlist Export
                if path == "/api/watchlist/export":
                    return self.send_json(server_self.watchlist_db.export_json())

                # API: Analytics
                if path == "/api/analytics":
                    country = query.get("country", ["US"])[0]
                    return self.send_json(server_self.analytics_service.get_dashboard_metrics(country))

                # API: Franchises list
                if path == "/api/franchises":
                    return self.send_json({"franchises": server_self.catalog_cache.get_featured_franchises(30)})

                # Asset fallback: assets/
                if path.startswith("/assets/"):
                    asset_rel = path[len("/assets/"):]
                    asset_path = os.path.join(server_self.root_dir, "assets", asset_rel)
                    if os.path.exists(asset_path) and os.path.isfile(asset_path):
                        self.send_response(200)
                        if asset_path.endswith(".svg"):
                            self.send_header("Content-Type", "image/svg+xml")
                        elif asset_path.endswith(".png"):
                            self.send_header("Content-Type", "image/png")
                        elif asset_path.endswith(".json"):
                            self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        with open(asset_path, "rb") as f:
                            self.wfile.write(f.read())
                        return

                # Static SPA router fallback
                return super().do_GET()

            def do_POST(self):
                parsed = urllib.parse.urlparse(self.path)
                path = parsed.path
                
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

                try:
                    payload = json.loads(body) if body else {}
                except Exception:
                    payload = {}

                # API: Update Settings
                if path == "/api/settings":
                    enabled = payload.get("enabled_services", [])
                    return self.send_json(server_self.settings_service.update_settings(enabled))

                # API: Reset Settings to Defaults
                if path == "/api/settings/reset":
                    return self.send_json(server_self.settings_service.reset_to_defaults())

                # API: Toggle Favorite
                if path == "/api/favorites/toggle":
                    tmdb_id = payload.get("id") or payload.get("tmdb_id")
                    media_type = payload.get("media_type", "movie")
                    title = payload.get("title", "")
                    year = payload.get("year", "")
                    poster_path = payload.get("poster_path", "")
                    res = server_self.favorites_db.toggle(tmdb_id, media_type, title, year, poster_path)
                    return self.send_json({
                        "is_favorite": res.get("is_favorite", False)
                    })

                # API: Set Favorite Category (Compatibility stub)
                if path == "/api/favorites/set_category":
                    return self.send_json({"success": True})

                # API: Import JSON directly to Favorites
                if path == "/api/favorites/import":
                    res = server_self.favorites_db.import_from_json(payload)
                    return self.send_json(res)

                # API: Add Recent Search
                if path == "/api/recent_searches":
                    query_str = payload.get("query", "")
                    res = server_self.recent_searches_service.add_search(query_str)
                    return self.send_json({"results": res})

                # API: Play in MPV
                if path == "/api/play_mpv":
                    url = payload.get("url")
                    title = payload.get("title", "Trova Video")
                    if not url:
                        return self.send_json({"success": False, "error": "Missing URL"}, 400)
                    result = server_self.mpv_service.play_url(url, title)
                    return self.send_json(result)

                # API: Add / Update Watchlist
                if path == "/api/watchlist":
                    server_self.watchlist_db.add_item(payload)
                    return self.send_json({"success": True})

                # API: Import JSON
                if path == "/api/watchlist/import":
                    res = server_self.watchlist_db.import_json(payload)
                    return self.send_json(res)

                # API: Import Letterboxd CSV
                if path == "/api/watchlist/import_letterboxd":
                    csv_text = payload.get("csv_text", "")
                    tier = payload.get("tier", "must_watch")
                    res = server_self.letterboxd_service.import_csv_content(csv_text, tier)
                    return self.send_json(res)

                self.send_json({"error": "Endpoint not found"}, 404)

            def do_DELETE(self):
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                path = parsed.path

                if path == "/api/favorites":
                    t_id = query.get("id", [""])[0]
                    m_type = query.get("type", ["movie"])[0]
                    if t_id:
                        server_self.favorites_db.remove(t_id, m_type)
                        return self.send_json({
                            "success": True,
                            "favorites": server_self.favorites_db.get_all(),
                            "categories": server_self.favorites_db.get_categories()
                        })
                    return self.send_json({"error": "Missing ID"}, 400)

                if path == "/api/watchlist":
                    t_id = query.get("id", [""])[0]
                    m_type = query.get("type", ["movie"])[0]
                    if t_id:
                        server_self.watchlist_db.remove_item(t_id, m_type)
                        return self.send_json({"success": True})
                    return self.send_json({"error": "Missing ID"}, 400)

                self.send_json({"error": "Endpoint not found"}, 404)

        return TrovaHandler

if __name__ == "__main__":
    server = TrovaServer(port=8899)
    server.run()
