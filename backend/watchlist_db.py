"""
OmaTrova Watchlist & Persistent Database Service
Stores user watchlists, custom categories, watch tiers, and JSON backups.
"""

import os
import sqlite3
import json
import time
import random

class WatchlistDb:
    def __init__(self, db_path=None):
        if db_path is None:
            data_dir = os.path.expanduser("~/.local/share/omatrova")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "watchlist.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tmdb_id INTEGER NOT NULL,
                    imdb_id TEXT,
                    media_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    poster_path TEXT,
                    backdrop_path TEXT,
                    release_date TEXT,
                    year TEXT,
                    vote_average REAL,
                    genres TEXT,
                    runtime INTEGER,
                    tier TEXT DEFAULT 'must_watch',
                    category TEXT DEFAULT 'General',
                    notes TEXT,
                    rating_user REAL,
                    providers_json TEXT,
                    added_at REAL,
                    updated_at REAL,
                    UNIQUE(tmdb_id, media_type)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT,
                    created_at REAL
                )
            """)
            # Ensure default categories
            defaults = [
                ("Highly Recommend", "#d4a853"),
                ("Must Watch", "#4a9a68"),
                ("Watched", "#52987a"),
                ("Hidden Gems", "#d08e74")
            ]
            for name, color in defaults:
                conn.execute(
                    "INSERT OR IGNORE INTO categories (name, color, created_at) VALUES (?, ?, ?)",
                    (name, color, time.time())
                )
            conn.commit()

    def add_item(self, item):
        tmdb_id = item.get("id") or item.get("tmdb_id")
        media_type = item.get("media_type", "movie")
        title = item.get("title") or item.get("name", "Untitled")
        imdb_id = item.get("imdb_id")
        poster_path = item.get("poster_path")
        backdrop_path = item.get("backdrop_path")
        release_date = item.get("release_date") or item.get("first_air_date")
        year = item.get("year") or (release_date[:4] if release_date else "")
        vote_average = item.get("vote_average", 0.0)
        genres = json.dumps(item.get("genres", []))
        runtime = item.get("runtime")
        tier = item.get("tier", "must_watch")
        category = item.get("category", "General")
        notes = item.get("notes", "")
        rating_user = item.get("rating_user")
        providers = json.dumps(item.get("providers", {}))
        now = time.time()

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO watchlist (
                    tmdb_id, imdb_id, media_type, title, poster_path, backdrop_path,
                    release_date, year, vote_average, genres, runtime, tier,
                    category, notes, rating_user, providers_json, added_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tmdb_id, media_type) DO UPDATE SET
                    tier = excluded.tier,
                    category = excluded.category,
                    notes = coalesce(excluded.notes, watchlist.notes),
                    rating_user = coalesce(excluded.rating_user, watchlist.rating_user),
                    providers_json = excluded.providers_json,
                    updated_at = excluded.updated_at
            """, (
                tmdb_id, imdb_id, media_type, title, poster_path, backdrop_path,
                release_date, year, vote_average, genres, runtime, tier,
                category, notes, rating_user, providers, now, now
            ))
            conn.commit()
        return True

    def remove_item(self, tmdb_id, media_type="movie"):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM watchlist WHERE tmdb_id = ? AND media_type = ?", (tmdb_id, media_type))
            conn.commit()
        return True

    def update_tier(self, tmdb_id, media_type, tier):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE watchlist SET tier = ?, updated_at = ? WHERE tmdb_id = ? AND media_type = ?",
                (tier, time.time(), tmdb_id, media_type)
            )
            conn.commit()
        return True

    def get_items(self, tier=None, media_type=None, sort_by="added_at_desc"):
        query = "SELECT * FROM watchlist WHERE 1=1"
        params = []

        if tier and tier != "all":
            query += " AND tier = ?"
            params.append(tier)

        if media_type and media_type != "all":
            query += " AND media_type = ?"
            params.append(media_type)

        if sort_by == "added_at_desc":
            query += " ORDER BY added_at DESC"
        elif sort_by == "added_at_asc":
            query += " ORDER BY added_at ASC"
        elif sort_by == "rating_desc":
            query += " ORDER BY vote_average DESC"
        elif sort_by == "title_asc":
            query += " ORDER BY title ASC"
        elif sort_by == "year_desc":
            query += " ORDER BY year DESC"

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()

        items = []
        for r in rows:
            d = dict(r)
            d["genres"] = json.loads(d["genres"]) if d.get("genres") else []
            d["providers"] = json.loads(d["providers_json"]) if d.get("providers_json") else {}
            items.append(d)
        return items

    def is_in_watchlist(self, tmdb_id, media_type="movie"):
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, tier, category FROM watchlist WHERE tmdb_id = ? AND media_type = ?",
                (tmdb_id, media_type)
            ).fetchone()
            if row:
                return {"in_watchlist": True, "tier": row["tier"], "category": row["category"]}
            return {"in_watchlist": False, "tier": None, "category": None}

    def get_random_recommendation(self, tier="highly_recommend"):
        items = self.get_items(tier=tier)
        if not items:
            items = self.get_items()
        if not items:
            return None
        return random.choice(items)

    def export_json(self):
        items = self.get_items()
        return {
            "version": "1.0",
            "app": "OmaTrova",
            "exported_at": time.time(),
            "total_items": len(items),
            "items": items
        }

    def import_json(self, data):
        if not data or "items" not in data:
            return {"success": False, "imported_count": 0, "error": "Invalid format"}
        
        count = 0
        for item in data["items"]:
            try:
                self.add_item(item)
                count += 1
            except Exception:
                pass
        return {"success": True, "imported_count": count}
