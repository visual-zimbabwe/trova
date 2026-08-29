"""
Trova Wikidata & Soundtrack Service
Fetches accolades, awards, and soundtrack tracklists with audio previews.
"""

import urllib.request
import urllib.parse
import json

class WikidataService:
    def __init__(self):
        self.cache = {}

    def get_soundtracks(self, title, year=""):
        # Match soundtrack / OST tracks via open music metadata & curated fallbacks
        cache_key = f"{title}_{year}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        query = f"{title} Soundtrack"
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&media=music&entity=song&limit=10"
        
        tracks = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Trova/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    for item in data.get("results", []):
                        tracks.append({
                            "track_name": item.get("trackName"),
                            "artist_name": item.get("artistName"),
                            "album_name": item.get("collectionName"),
                            "artwork_url": item.get("artworkUrl100"),
                            "preview_url": item.get("previewUrl"),
                            "track_time_millis": item.get("trackTimeMillis")
                        })
        except Exception:
            pass

        self.cache[cache_key] = tracks
        return tracks
