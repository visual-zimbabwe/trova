// OmaTrova API Client

const API = {
  async getTheme() {
    try {
      const res = await fetch('/api/theme');
      return await res.json();
    } catch (e) {
      return null;
    }
  },

  async getSettings() {
    try {
      const res = await fetch('/api/settings');
      return await res.json();
    } catch (e) {
      return {
        services: [],
        enabled_services: ['netflix', 'prime', 'max', 'paramount_plus']
      };
    }
  },

  async updateSettings(enabledServices) {
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled_services: enabledServices })
      });
      return await res.json();
    } catch (e) {
      return null;
    }
  },

  async resetSettings() {
    try {
      const res = await fetch('/api/settings/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      return await res.json();
    } catch (e) {
      return null;
    }
  },

  async getHomeFeed() {
    const res = await fetch('/api/home');
    return await res.json();
  },

  async getRecentSearches() {
    try {
      const res = await fetch('/api/recent_searches');
      return await res.json();
    } catch (e) {
      return { results: ['Interstellar', 'Stranger Things', 'Dune: Part Two', 'Succession', 'The Dark Knight'] };
    }
  },

  async addRecentSearch(query) {
    try {
      const res = await fetch('/api/recent_searches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      return await res.json();
    } catch (e) {
      return null;
    }
  },

  async getFavoritesSummary() {
    try {
      const res = await fetch('/api/favorites/summary');
      return await res.json();
    } catch (e) {
      return { total: 0, movies: 0, tv: 0 };
    }
  },

  async getFavoritesShelf() {
    try {
      const res = await fetch('/api/favorites/shelf');
      return await res.json();
    } catch (e) {
      return { movies: [], tv: [] };
    }
  },

  async getFavoriteIds() {
    try {
      const res = await fetch('/api/favorites/ids');
      const data = await res.json();
      return data.ids || [];
    } catch (e) {
      return [];
    }
  },

  async getFavorites(mediaType = null, sortBy = 'added_at_desc', offset = 0, limit = 48, q = '') {
    try {
      const params = new URLSearchParams();
      if (mediaType && mediaType !== 'all') params.append('media_type', mediaType);
      if (sortBy) params.append('sort_by', sortBy);
      if (offset) params.append('offset', offset);
      if (limit) params.append('limit', limit);
      if (q && q.trim()) params.append('q', q.trim());
      const url = params.toString() ? `/api/favorites?${params.toString()}` : '/api/favorites';
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      return { favorites: [], count: 0 };
    }
  },

  async toggleFavorite(payload) {
    try {
      const res = await fetch('/api/favorites/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return await res.json();
    } catch (e) {
      return { is_favorite: false, favorites: [], categories: [] };
    }
  },

  async removeFavorite(id, mediaType = 'movie') {
    try {
      const res = await fetch(`/api/favorites?id=${id}&type=${encodeURIComponent(mediaType)}`, {
        method: 'DELETE'
      });
      return await res.json();
    } catch (e) {
      return { success: false };
    }
  },


  async setFavoriteCategory(id, mediaType, category) {
    try {
      const res = await fetch('/api/favorites/set_category', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, media_type: mediaType, category })
      });
      return await res.json();
    } catch (e) {
      return { success: false };
    }
  },

  async searchMulti(query, page = 1) {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&page=${page}`);
    return await res.json();
  },

  async discover(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`/api/discover?${qs}`);
    return await res.json();
  },

  async getDetails(mediaType, id) {
    const res = await fetch(`/api/details?type=${mediaType}&id=${id}`);
    return await res.json();
  },

  async getPerson(id) {
    const res = await fetch(`/api/person?id=${id}`);
    return await res.json();
  },

  async getCollection(id) {
    const res = await fetch(`/api/collection?id=${id}`);
    return await res.json();
  },

  async getSoundtracks(title, year = '') {
    const res = await fetch(`/api/soundtracks?title=${encodeURIComponent(title)}&year=${encodeURIComponent(year)}`);
    return await res.json();
  },

  async playInMpv(url, title = '') {
    const res = await fetch('/api/play_mpv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, title })
    });
    return await res.json();
  },

  async getWatchlist(tier = null, mediaType = null, sortBy = 'added_at_desc') {
    const params = new URLSearchParams();
    if (tier) params.append('tier', tier);
    if (mediaType) params.append('media_type', mediaType);
    if (sortBy) params.append('sort_by', sortBy);
    const res = await fetch(`/api/watchlist?${params.toString()}`);
    return await res.json();
  },

  async addToWatchlist(item) {
    const res = await fetch('/api/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    return await res.json();
  },

  async removeFromWatchlist(id, mediaType = 'movie') {
    const res = await fetch(`/api/watchlist?id=${id}&type=${mediaType}`, {
      method: 'DELETE'
    });
    return await res.json();
  },

  async getWatchlistStatus(id, mediaType = 'movie') {
    const res = await fetch(`/api/watchlist/status?id=${id}&type=${mediaType}`);
    return await res.json();
  },

  async getRandomRecommendation(tier = 'highly_recommend') {
    const res = await fetch(`/api/watchlist/random?tier=${tier}`);
    return await res.json();
  },

  async exportWatchlist() {
    const res = await fetch('/api/watchlist/export');
    return await res.json();
  },

  async importWatchlist(data) {
    const res = await fetch('/api/watchlist/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await res.json();
  },

  async importLetterboxd(csvText, tier = 'must_watch') {
    const res = await fetch('/api/watchlist/import_letterboxd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csv_text: csvText, tier })
    });
    return await res.json();
  },

  async getAnalytics(country = 'US') {
    const res = await fetch(`/api/analytics?country=${country}`);
    return await res.json();
  },

  async getFranchises() {
    const res = await fetch('/api/franchises');
    return await res.json();
  }
};
