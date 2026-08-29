// OmaTrova Reactive Watchlist Store

const WatchlistStore = {
  items: [],
  listeners: [],

  async refresh(tier = null, mediaType = null, sortBy = 'added_at_desc') {
    const data = await API.getWatchlist(tier, mediaType, sortBy);
    this.items = data.items || [];
    this.notify();
    return this.items;
  },

  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  },

  notify() {
    this.listeners.forEach(cb => cb(this.items));
  },

  async toggleWatchlist(item, tier = 'must_watch') {
    const status = await API.getWatchlistStatus(item.id, item.media_type || 'movie');
    if (status.in_watchlist) {
      await API.removeFromWatchlist(item.id, item.media_type || 'movie');
      await this.refresh();
      return false;
    } else {
      item.tier = tier;
      await API.addToWatchlist(item);
      await this.refresh();
      return true;
    }
  }
};
