"""
OmaTrova Letterboxd & Trakt Import Service
Parses CSV and JSON movie lists, enriches titles, and imports into Watchlist.
"""

import csv
import io
import time

class LetterboxdService:
    def __init__(self, tmdb_service, watchlist_db):
        self.tmdb_service = tmdb_service
        self.watchlist_db = watchlist_db

    def import_csv_content(self, csv_text, target_tier="must_watch"):
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        imported = []
        failed = []

        for row in reader:
            title = row.get("Name") or row.get("Title") or row.get("Film")
            year = row.get("Year") or row.get("Release Date", "")[:4]
            user_rating = row.get("Rating")

            if not title:
                continue

            # Query TMDB
            search_query = f"{title} {year}".strip() if year else title
            res = self.tmdb_service.search_multi(search_query)
            candidates = res.get("results", [])

            movie_cand = None
            for c in candidates:
                if c.get("media_type") == "movie":
                    movie_cand = c
                    break
            
            if not movie_cand and candidates:
                movie_cand = candidates[0]

            if movie_cand:
                item_data = {
                    "id": movie_cand.get("id"),
                    "tmdb_id": movie_cand.get("id"),
                    "media_type": movie_cand.get("media_type", "movie"),
                    "title": movie_cand.get("title") or title,
                    "poster_path": movie_cand.get("poster_path"),
                    "backdrop_path": movie_cand.get("backdrop_path"),
                    "release_date": movie_cand.get("release_date") or (f"{year}-01-01" if year else ""),
                    "year": movie_cand.get("year") or year,
                    "vote_average": movie_cand.get("vote_average", 0.0),
                    "tier": target_tier,
                    "category": "Letterboxd Import",
                    "rating_user": float(user_rating) if user_rating else None
                }
                self.watchlist_db.add_item(item_data)
                imported.append(item_data["title"])
            else:
                failed.append(title)

        return {
            "success": True,
            "imported_count": len(imported),
            "failed_count": len(failed),
            "imported_titles": imported[:10],
            "failed_titles": failed[:10]
        }
