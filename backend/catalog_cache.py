"""
Trova Catalog & Franchise Cache Service
Provides fast local pre-indexed franchises and cinematic collections.
"""

import os
import json
from collections import defaultdict

class CatalogCache:
    def __init__(self, assets_dir=None):
        if assets_dir is None:
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        self.assets_dir = assets_dir
        self.collections_file = os.path.join(assets_dir, "collection_movies.json")
        self.franchises = []
        self.franchise_map = {}
        self._load_collections()

    def _load_collections(self):
        if not os.path.exists(self.collections_file):
            return

        try:
            with open(self.collections_file, "r") as f:
                movies = json.load(f)

            collections_dict = defaultdict(list)
            meta_dict = {}

            for m in movies:
                col = m.get("collection")
                if col and "id" in col:
                    col_id = col["id"]
                    vote = m.get("vote_average")
                    vote_avg = round(float(vote), 1) if vote is not None else 0.0
                    collections_dict[col_id].append({
                        "id": m.get("id"),
                        "media_type": "movie",
                        "title": m.get("title"),
                        "poster_path": m.get("poster_path") or col.get("poster_path"),
                        "backdrop_path": col.get("backdrop_path"),
                        "release_date": m.get("release_date"),
                        "year": (m.get("release_date") or "")[:4],
                        "vote_average": vote_avg
                    })
                    if col_id not in meta_dict:
                        meta_dict[col_id] = {
                            "id": col_id,
                            "name": col.get("name"),
                            "poster_path": col.get("poster_path"),
                            "backdrop_path": col.get("backdrop_path")
                        }

            # Filter franchises with at least 2 titles
            franchises = []
            for col_id, parts in collections_dict.items():
                if len(parts) >= 2:
                    meta = meta_dict[col_id]
                    parts.sort(key=lambda x: x.get("release_date") or "9999")
                    franchises.append({
                        "id": col_id,
                        "name": meta["name"],
                        "poster_path": meta["poster_path"],
                        "backdrop_path": meta["backdrop_path"],
                        "part_count": len(parts),
                        "parts": parts
                    })

            # Sort popular franchises first (part_count, high-vote parts)
            franchises.sort(key=lambda x: (x["part_count"], max((p["vote_average"] for p in x["parts"]), default=0)), reverse=True)
            self.franchises = franchises
            self.franchise_map = {f["id"]: f for f in franchises}
        except Exception as e:
            print(f"[CatalogCache Error] {e}")

    def get_featured_franchises(self, limit=12):
        return self.franchises[:limit]

    def get_franchise(self, franchise_id):
        return self.franchise_map.get(franchise_id)
