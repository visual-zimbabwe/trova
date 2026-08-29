"""
Trova Native Desktop Application & CLI Companion
Standalone Wayland native window powered by WebKitGTK / pywebview + CLI utilities.
"""

import os
import sys
import time
import json
import socket
import argparse
import threading
import glob

# Ensure backend directory and system site-packages are in sys.path
sys.path.insert(0, os.path.dirname(__file__))
for site_pkg in glob.glob("/usr/lib/python3*/site-packages"):
    if site_pkg not in sys.path:
        sys.path.append(site_pkg)

from app import TrovaServer

def find_free_port(start_port=8899):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    return 8899

def handle_cli_commands(args):
    # If subcommands are provided, execute fast CLI utilities without GUI window
    if args.command == "search":
        query = " ".join(args.query_terms)
        server = TrovaServer()
        res = server.tmdb_service.search_multi(query)
        results = res.get("results", [])
        if not results:
            print(f"\033[33mNo results found for '{query}'\033[0m")
            return True
        
        print(f"\n\033[1;32mTrova Search Results for '\033[1;37m{query}\033[1;32m':\033[0m\n")
        for i, item in enumerate(results[:10], 1):
            m_type = item.get("media_type", "movie").upper()
            title = item.get("title") or item.get("name")
            year = item.get("year") or "N/A"
            rating = f"[{item.get('vote_average')}]" if item.get('vote_average') else ""
            print(f" \033[1;33m{i:2d}.\033[0m \033[1m{title}\033[0m ({year}) [{m_type}] {rating}")
        print()
        return True

    elif args.command == "random":
        server = TrovaServer()
        rec = server.watchlist_db.get_random_recommendation()
        if not rec:
            favs = server.favorites_db.get_all()
            if favs:
                import random
                rec = random.choice(favs)
            else:
                print("\033[33mYour library is empty. Open Trova to add titles.\033[0m")
                return True
        print(f"\n\033[1;32mTrova Cinephile Pick:\033[0m \033[1;37m{rec.get('title')}\033[0m ({rec.get('year')})")
        if rec.get('category'):
            print(f"   Category: \033[33m{rec.get('category')}\033[0m")
        print()
        return True

    elif args.command == "play":
        query = " ".join(args.query_terms)
        server = TrovaServer()
        res = server.tmdb_service.search_multi(query)
        results = res.get("results", [])
        if not results:
            print(f"\033[33mNo title found for '{query}'\033[0m")
            return True
        first = results[0]
        details = server.tmdb_service.get_details(first.get("media_type", "movie"), first.get("id"))
        trailer = details.get("trailer") if details else None
        if trailer and trailer.get("url"):
            print(f"\033[1;32mLaunching MPV for '\033[1;37m{details.get('title')}\033[1;32m'...\033[0m")
            server.mpv_service.play_url(trailer["url"], details.get("title"))
        else:
            print(f"\033[33mNo official trailer stream found for '{details.get('title') if details else query}'.\033[0m")
        return True

    elif args.command == "stats":
        server = TrovaServer()
        summary = server.favorites_db.get_summary()
        total_favs = summary.get("total", 0)
        movies_cnt = summary.get("movies", 0)
        tv_cnt = summary.get("tv", 0)
        print("\n\033[1;32mTrova Cinema Library Stats:\033[0m")
        print(f"   Total Favorites: \033[1m{total_favs}\033[0m titles")
        print(f"   - \033[33mMovies:\033[0m    \033[1m{movies_cnt:4d}\033[0m titles")
        print(f"   - \033[36mTV Series:\033[0m \033[1m{tv_cnt:4d}\033[0m titles")
        print()
        return True

    elif args.command == "favs":
        server = TrovaServer()
        summary = server.favorites_db.get_summary()
        total_favs = summary.get("total", 0)
        if total_favs == 0:
            print("\033[33mNo favorites yet. Search any title in Trova and press F to favorite.\033[0m")
            return True

        movies = server.favorites_db.get_all(media_type="movie")
        tv_shows = server.favorites_db.get_all(media_type="tv")

        print(f"\n\033[1;32mTrova Favorites ({total_favs} titles):\033[0m\n")
        if movies:
            print(f" \033[1;33m▶ Movies\033[0m ({len(movies)} titles):")
            for item in movies[:10]:
                year = f"({item.get('year')})" if item.get('year') else ""
                print(f"   • \033[1m{item.get('title')}\033[0m {year}")
            if len(movies) > 10:
                print(f"   \033[90m... and {len(movies) - 10} more movies\033[0m")
            print()

        if tv_shows:
            print(f" \033[1;36m▶ TV Series\033[0m ({len(tv_shows)} titles):")
            for item in tv_shows[:10]:
                year = f"({item.get('year')})" if item.get('year') else ""
                print(f"   • \033[1m{item.get('title')}\033[0m {year}")
            if len(tv_shows) > 10:
                print(f"   \033[90m... and {len(tv_shows) - 10} more series\033[0m")
            print()
        return True

    elif args.command == "import-favorites":
        server = TrovaServer()
        file_path = args.file_path
        if not file_path:
            # Look for default watchlist JSON in project root
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates = glob.glob(os.path.join(root_dir, "trova-watchlist-*.json"))
            if candidates:
                file_path = candidates[0]
            else:
                print("\033[31mError: No JSON file path specified and none found in project root.\033[0m")
                return True

        if not os.path.exists(file_path):
            print(f"\033[31mError: File '{file_path}' does not exist.\033[0m")
            return True

        print(f"\n\033[1;32mImporting Trova Watchlist into Favorites from:\033[0m \033[1;37m{file_path}\033[0m")
        res = server.favorites_db.import_from_json(file_path)
        if res.get("success"):
            print(f"\033[1;32m✓ Successfully imported \033[1;37m{res.get('count')}\033[1;32m titles into Trova Favorites!\033[0m\n")
            print("   \033[1mCategories Breakdown:\033[0m")
            for cat in res.get("categories", []):
                print(f"   • \033[33m{cat['name']:24s}\033[0m \033[1m{cat['count']:4d}\033[0m titles")
            print()
        else:
            print(f"\033[31mImport failed: {res}\033[0m")
        return True

    elif args.command == "revert-import":
        server = TrovaServer()
        deleted = server.favorites_db.revert_bulk_import()
        print(f"\n\033[1;32m✓ Reverted bulk import. Removed \033[1;37m{deleted}\033[1;32m imported titles.\033[0m")
        summary = server.favorites_db.get_summary()
        print(f"   Remaining Favorites: \033[1m{summary.get('total', 0)}\033[0m titles across \033[1m{len(summary.get('categories', []))}\033[0m categories\n")
        return True

    elif args.command == "clear-favorites":
        server = TrovaServer()
        deleted = server.favorites_db.clear_all()
        print(f"\n\033[1;32m✓ Cleared all favorites ({deleted} titles removed).\033[0m\n")
        return True

    elif args.command == "export":
        server = TrovaServer()
        data = {
            "version": "2.0",
            "app": "Trova",
            "exported_at": time.time(),
            "favorites": server.favorites_db.get_all(),
            "categories": server.favorites_db.get_categories()
        }
        print(json.dumps(data, indent=2))
        return True

    return False

def launch_gui(port=None):
    os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
    os.environ["WEBKIT_DISABLE_DMABUF_RENDERER"] = "1"

    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import GLib
        GLib.set_prgname("trova")
        GLib.set_application_name("Trova")
    except Exception:
        pass

    import webview

    port = port or find_free_port()
    server = TrovaServer(port=port)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait for server ready
    app_url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except (OSError, ConnectionRefusedError):
            time.sleep(0.05)

    # Read active theme background
    theme_data = server.theme_watcher.get_current_theme_data()
    bg_color = theme_data.get("colors", {}).get("bg_root", "#101913")

    # Native Window
    window = webview.create_window(
        title="Trova",
        url=app_url,
        width=1260,
        height=840,
        min_size=(860, 580),
        background_color=bg_color,
        text_select=True,
        zoomable=False
    )

    def on_closed():
        try:
            server.theme_watcher.stop()
            server.mpv_service.stop()
        except Exception:
            pass
        os._exit(0)

    window.events.closed += on_closed

    try:
        webview.start(gui="gtk", debug=False)
    except Exception:
        webview.start(debug=False)

def main():
    parser = argparse.ArgumentParser(description="Trova Standalone Where to Stream Companion")
    subparsers = parser.add_subparsers(dest="command", help="CLI Subcommands")

    search_p = subparsers.add_parser("search", help="Search movies, TV, and people")
    search_p.add_argument("query_terms", nargs="+", help="Search keywords")

    subparsers.add_parser("random", help="Roll a random recommendation from your favorites")

    play_p = subparsers.add_parser("play", help="Search and stream trailer in MPV")
    play_p.add_argument("query_terms", nargs="+", help="Movie or TV title")

    subparsers.add_parser("stats", help="Display cinema library and favorites analytics")
    subparsers.add_parser("favs", help="List all favorites grouped by category")

    import_fav_p = subparsers.add_parser("import-favorites", help="Import Trova JSON watchlist into categorized favorites")
    import_fav_p.add_argument("file_path", nargs="?", default=None, help="Path to Trova watchlist JSON file")

    subparsers.add_parser("revert-import", help="Revert the bulk JSON watchlist import")
    subparsers.add_parser("clear-favorites", help="Clear all favorites from database")

    subparsers.add_parser("export", help="Export favorites and watchlist to JSON")

    parser.add_argument("--port", type=int, default=None, help="Custom local server port")

    args = parser.parse_args()

    if args.command:
        handle_cli_commands(args)
    else:
        launch_gui(args.port)

if __name__ == "__main__":
    main()

