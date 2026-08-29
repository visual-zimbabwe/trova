"""
Trova Cinephile Analytics & Streaming ROI Service
Computes streaming service coverage, genre breakdowns, and viewing statistics.
"""

from collections import Counter
import json

class AnalyticsService:
    def __init__(self, watchlist_db, tmdb_service):
        self.watchlist_db = watchlist_db
        self.tmdb_service = tmdb_service

    def get_dashboard_metrics(self, country="US"):
        items = self.watchlist_db.get_items()
        if not items:
            return self._empty_metrics()

        total_count = len(items)
        movies_count = sum(1 for i in items if i.get("media_type") == "movie")
        tv_count = total_count - movies_count

        total_runtime_minutes = 0
        total_rating = 0
        rated_items_count = 0

        genre_counts = Counter()
        decade_counts = Counter()
        tier_counts = Counter()
        provider_counts = Counter()

        for item in items:
            # Runtime
            rt = item.get("runtime")
            if rt:
                total_runtime_minutes += rt

            # Rating
            va = item.get("vote_average")
            if va and va > 0:
                total_rating += va
                rated_items_count += 1

            # Genres
            for g in item.get("genres", []):
                genre_counts[g] += 1

            # Decade
            year_str = item.get("year") or ""
            if len(year_str) == 4 and year_str.isdigit():
                decade = f"{year_str[:3]}0s"
                decade_counts[decade] += 1

            # Tier
            tier = item.get("tier", "must_watch")
            tier_counts[tier] += 1

            # Providers for country
            providers = item.get("providers", {})
            country_prov = providers.get(country, {}).get("providers", [])
            for p in country_prov:
                s_key = p.get("service_key") or p.get("name")
                provider_counts[s_key] += 1

        avg_rating = round(total_rating / rated_items_count, 1) if rated_items_count > 0 else 0.0

        # Top providers coverage
        provider_coverage = []
        for p_name, p_count in provider_counts.most_common(8):
            pct = round((p_count / total_count) * 100, 1)
            provider_coverage.append({
                "service": p_name,
                "count": p_count,
                "percentage": pct
            })

        top_genres = [
            {"genre": g, "count": c, "percentage": round((c / total_count) * 100, 1)}
            for g, c in genre_counts.most_common(8)
        ]

        decades = [
            {"decade": d, "count": c}
            for d, c in sorted(decade_counts.items())
        ]

        return {
            "total_items": total_count,
            "movies_count": movies_count,
            "tv_count": tv_count,
            "total_runtime_hours": round(total_runtime_minutes / 60, 1),
            "average_rating": avg_rating,
            "provider_coverage": provider_coverage,
            "top_genres": top_genres,
            "decades": decades,
            "tiers": dict(tier_counts)
        }

    def _empty_metrics(self):
        return {
            "total_items": 0,
            "movies_count": 0,
            "tv_count": 0,
            "total_runtime_hours": 0,
            "average_rating": 0.0,
            "provider_coverage": [],
            "top_genres": [],
            "decades": [],
            "tiers": {}
        }
