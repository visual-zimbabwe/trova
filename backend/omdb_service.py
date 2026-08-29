"""
Trova OMDb API Service
Fetches critic scores, awards, ratings and localized metadata from OMDb.
"""

import os
import json
import urllib.request
import urllib.parse

OMDB_API_KEY = "cd05d48b"
OMDB_BASE = "https://www.omdbapi.com/"

class OmdbService:
    def __init__(self):
        self.cache = {}
        self.cache_dir = os.path.expanduser("~/.cache/trova")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "omdb_cache.json")
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    def get_ratings(self, imdb_id):
        if not imdb_id:
            return self._empty_ratings()

        if imdb_id in self.cache:
            return self.cache[imdb_id]

        url = f"{OMDB_BASE}?i={urllib.parse.quote(imdb_id)}&apikey={OMDB_API_KEY}"
        req = urllib.request.Request(url, headers={"User-Agent": "Trova/1.0", "Accept": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    if data.get("Response") == "True":
                        res = self._format_omdb_response(data)
                        self.cache[imdb_id] = res
                        if len(self.cache) % 10 == 0:
                            self._save_cache()
                        return res
        except Exception:
            pass

        return self._empty_ratings()

    def _format_omdb_response(self, data):
        imdb_rating = data.get("imdbRating")
        if imdb_rating and imdb_rating != "N/A":
            imdb_rating = f"{imdb_rating}/10"
        else:
            imdb_rating = None

        metascore = data.get("Metascore")
        if metascore == "N/A":
            metascore = None

        rt_rating = None
        for rating in data.get("Ratings", []):
            if rating.get("Source") == "Rotten Tomatoes":
                rt_rating = rating.get("Value")
                break

        awards = data.get("Awards")
        if awards == "N/A":
            awards = None

        rated = data.get("Rated")
        if rated in ("N/A", "Not Rated", "Unrated"):
            rated = None

        box_office = data.get("BoxOffice")
        if box_office == "N/A":
            box_office = None

        return {
            "imdbRating": imdb_rating,
            "imdbVotes": data.get("imdbVotes") if data.get("imdbVotes") != "N/A" else None,
            "rottenTomatoes": rt_rating,
            "metascore": metascore,
            "awards": awards,
            "rated": rated,
            "writer": data.get("Writer") if data.get("Writer") != "N/A" else None,
            "actors": data.get("Actors") if data.get("Actors") != "N/A" else None,
            "plot": data.get("Plot") if data.get("Plot") != "N/A" else None,
            "boxOffice": box_office,
            "production": data.get("Production") if data.get("Production") != "N/A" else None
        }

    def _empty_ratings(self):
        return {
            "imdbRating": None,
            "imdbVotes": None,
            "rottenTomatoes": None,
            "metascore": None,
            "awards": None,
            "rated": None,
            "writer": None,
            "actors": None,
            "plot": None,
            "boxOffice": None,
            "production": None
        }
