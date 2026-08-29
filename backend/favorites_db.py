"""
Trova Favorites Database Service
Provides persistent SQLite storage for user favorite titles with first-class category support.
"""

import os
import sqlite3
import json
import time
from typing import Optional, List, Dict, Any

class FavoritesDb:
    def __init__(self, db_path=None):
        if db_path is None:
            data_dir = os.path.expanduser("~/.local/share/trova")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "favorites.db")
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
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tmdb_id INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    year TEXT,
                    poster_path TEXT,
                    category TEXT DEFAULT 'Watch Next',
                    added_at REAL NOT NULL,
                    UNIQUE(tmdb_id, media_type)
                )
            """)

            # Migration: Ensure category column exists in legacy databases
            cursor = conn.execute("PRAGMA table_info(favorites)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "category" not in columns:
                conn.execute("ALTER TABLE favorites ADD COLUMN category TEXT DEFAULT 'Watch Next'")

            conn.commit()

    def is_favorite(self, tmdb_id, media_type="movie") -> Dict[str, Any]:
        if not tmdb_id:
            return {"is_favorite": False}
        try:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "SELECT 1 FROM favorites WHERE tmdb_id = ? AND media_type = ? LIMIT 1",
                    (int(tmdb_id), str(media_type).lower())
                )
                row = cur.fetchone()
                return {"is_favorite": bool(row)}
        except Exception:
            return {"is_favorite": False}

    def toggle(self, tmdb_id, media_type, title="", year="", poster_path="", category=None) -> Dict[str, Any]:
        if not tmdb_id:
            return {"is_favorite": False}

        t_id = int(tmdb_id)
        m_type = str(media_type).lower()

        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT id FROM favorites WHERE tmdb_id = ? AND media_type = ?",
                (t_id, m_type)
            )
            row = cur.fetchone()
            if row:
                conn.execute("DELETE FROM favorites WHERE id = ?", (row["id"],))
                conn.commit()
                return {"is_favorite": False}
            else:
                if not title or not str(title).strip():
                    return {"is_favorite": False}
                conn.execute("""
                    INSERT INTO favorites (tmdb_id, media_type, title, year, poster_path, category, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (t_id, m_type, str(title).strip(), str(year or ""), str(poster_path or ""), category or "", time.time()))
                conn.commit()
                return {"is_favorite": True}

    def set_category(self, tmdb_id, media_type, category) -> bool:
        if not tmdb_id:
            return False
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE favorites SET category = ? WHERE tmdb_id = ? AND media_type = ?",
                (str(category or "").strip(), int(tmdb_id), str(media_type).lower())
            )
            conn.commit()
            return cur.rowcount > 0

    def get_summary(self, category=None) -> Dict[str, Any]:
        """Returns total count, movie count, and TV count in sub-millisecond time (< 0.1ms)."""
        with self._get_conn() as conn:
            cur_types = conn.execute("""
                SELECT media_type, count(*) as count
                FROM favorites
                GROUP BY media_type
            """)
            type_counts = {row["media_type"]: row["count"] for row in cur_types.fetchall()}
            movies_count = type_counts.get("movie", 0)
            tv_count = type_counts.get("tv", 0)
            total = movies_count + tv_count

            return {
                "total": total,
                "movies": movies_count,
                "tv": tv_count,
                "categories": []
            }

    def get_shelf_items(self, limit_per_type=8) -> Dict[str, List[Dict[str, Any]]]:
        """Returns recent favorites grouped by Movies and TV Series for fast home shelf rendering."""
        with self._get_conn() as conn:
            cur_m = conn.execute("""
                SELECT tmdb_id, media_type, title, year, poster_path, added_at
                FROM favorites
                WHERE media_type = 'movie'
                ORDER BY added_at DESC
                LIMIT ?
            """, (limit_per_type,))
            movies = [dict(row) for row in cur_m.fetchall()]

            cur_t = conn.execute("""
                SELECT tmdb_id, media_type, title, year, poster_path, added_at
                FROM favorites
                WHERE media_type = 'tv'
                ORDER BY added_at DESC
                LIMIT ?
            """, (limit_per_type,))
            tv = [dict(row) for row in cur_t.fetchall()]

            return {
                "movies": movies,
                "tv": tv
            }

    def get_favorite_ids(self) -> List[str]:
        """Returns lightweight flat array of 'type_id' strings for instant in-memory search decoration."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT media_type, tmdb_id FROM favorites")
            return [f"{row['media_type']}_{row['tmdb_id']}" for row in cur.fetchall()]

    def get_all(self, category=None, media_type=None, sort_by="added_at_desc", offset=0, limit=None, search=None) -> List[Dict[str, Any]]:
        query = "SELECT tmdb_id, media_type, title, year, poster_path, category, added_at FROM favorites WHERE 1=1"
        params = []

        if category and category != "all":
            query += " AND category = ?"
            params.append(category)

        if media_type and media_type != "all":
            query += " AND media_type = ?"
            params.append(media_type)

        if search and search.strip():
            query += " AND title LIKE ?"
            params.append(f"%{search.strip()}%")

        if sort_by == "added_at_desc":
            query += " ORDER BY added_at DESC"
        elif sort_by == "added_at_asc":
            query += " ORDER BY added_at ASC"
        elif sort_by == "title_asc":
            query += " ORDER BY title ASC"
        elif sort_by == "year_desc":
            query += " ORDER BY year DESC"

        if limit is not None and int(limit) > 0:
            query += " LIMIT ? OFFSET ?"
            params.append(int(limit))
            params.append(int(offset or 0))

        with self._get_conn() as conn:
            cur = conn.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def get_categories(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT category, count(*) as count 
                FROM favorites 
                WHERE category IS NOT NULL AND category != ''
                GROUP BY category 
                ORDER BY count DESC, category ASC
            """)
            return [{"name": row["category"], "count": row["count"]} for row in cur.fetchall()]

    def remove(self, tmdb_id, media_type) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM favorites WHERE tmdb_id = ? AND media_type = ?",
                (int(tmdb_id), str(media_type).lower())
            )
            conn.commit()
            return cur.rowcount > 0

    def import_from_json(self, json_data_or_path) -> Dict[str, Any]:
        """
        Imports titles directly into favorites with category mapping.
        Supports both Trova Android Schema v2 (find-streamer-watchlist) and Trova native exports.
        """
        if isinstance(json_data_or_path, str):
            with open(json_data_or_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json_data_or_path

        items = data.get("items", [])
        if not items:
            return {"success": False, "count": 0, "categories": []}

        imported_count = 0
        now = time.time()

        with self._get_conn() as conn:
            for item in items:
                tmdb_id = item.get("tmdbId") or item.get("tmdb_id") or item.get("id")
                if not tmdb_id:
                    continue

                media_type = (item.get("mediaType") or item.get("media_type") or "movie").lower()
                title = item.get("title") or item.get("name") or "Untitled"
                year = str(item.get("year") or "")
                poster_path = item.get("posterUrl") or item.get("poster_path") or ""
                category = item.get("watchlistCategoryLabel") or item.get("category") or "Watch Next"

                conn.execute("""
                    INSERT INTO favorites (tmdb_id, media_type, title, year, poster_path, category, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(tmdb_id, media_type) DO UPDATE SET
                        category = excluded.category,
                        title = excluded.title,
                        year = excluded.year,
                        poster_path = excluded.poster_path
                """, (int(tmdb_id), media_type, title.strip(), year, poster_path, category.strip(), now))
                imported_count += 1
            conn.commit()

        categories = self.get_categories()
        return {
            "success": True,
            "count": imported_count,
            "categories": categories
        }

    def revert_bulk_import(self, timestamp_threshold=1787963830.0) -> int:
        """Removes all items from the bulk import batch."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM favorites WHERE added_at >= ?", (timestamp_threshold,))
            conn.commit()
            return cur.rowcount

    def clear_all(self) -> int:
        """Clears all favorites completely."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM favorites")
            conn.commit()
            return cur.rowcount

