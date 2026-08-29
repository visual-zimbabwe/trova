// Recent Searches Persistent Storage (Backend-Backed + Multi-Instance Sync)
const RecentSearches = {
  DEFAULT_ITEMS: ['Interstellar', 'Stranger Things', 'Dune: Part Two', 'Succession', 'The Dark Knight'],

  async get() {
    try {
      const res = await API.getRecentSearches();
      if (res && Array.isArray(res.results) && res.results.length > 0) {
        return res.results.slice(0, 5);
      }
    } catch (e) {
      console.warn('Failed to load recent searches from backend', e);
    }
    return [...this.DEFAULT_ITEMS];
  },

  async add(query) {
    if (!query || typeof query !== 'string') return;
    const clean = query.trim();
    if (!clean) return;

    try {
      await API.addRecentSearch(clean);
    } catch (e) {
      console.warn('Failed to save recent search to backend', e);
    }
  }
};

const App = {
  searchTimer: null,
  selectedIndex: -1,
  searchResults: [],
  currentDetails: null,
  currentFilter: 'all',
  cachedSettings: null,

  async init() {
    ThemeStore.init();
    this.bindEvents();
    // Launch all initial data queries concurrently without blocking UI render
    Promise.all([
      this.loadSettings(),
      this.renderRecentSearches(),
      this.renderFavoritesShelf(),
      this.loadFavoriteIds()
    ]);
  },

  async loadSettings() {
    try {
      this.cachedSettings = await API.getSettings();
    } catch (e) {
      console.warn('Failed to load settings', e);
    }
  },

  async openSettings() {
    const modal = document.getElementById('settingsModal');
    if (!modal) return;

    await this.loadSettings();
    this.renderSettingsServices();
    modal.style.display = 'flex';
  },

  closeSettings() {
    const modal = document.getElementById('settingsModal');
    if (modal) modal.style.display = 'none';
  },

  toggleSettings() {
    const modal = document.getElementById('settingsModal');
    if (!modal) return;
    if (modal.style.display === 'none' || !modal.style.display) {
      this.openSettings();
    } else {
      this.closeSettings();
    }
  },

  handleSettingsBackdropClick(e) {
    if (e.target.id === 'settingsModal') {
      this.closeSettings();
    }
  },

  renderSettingsServices() {
    const container = document.getElementById('settingsServicesList');
    if (!container || !this.cachedSettings) return;

    const allServices = this.cachedSettings.services || [];
    const enabledSet = new Set(this.cachedSettings.enabled_services || []);

    const groups = {};
    allServices.forEach(s => {
      const g = s.group || 'Other';
      if (!groups[g]) groups[g] = [];
      groups[g].push(s);
    });

    container.innerHTML = Object.entries(groups).map(([groupName, services]) => {
      const cardsHtml = services.map(s => {
        const isChecked = enabledSet.has(s.id);
        const activeCls = isChecked ? 'active' : '';
        const checkIcon = isChecked ? '✓' : '';

        return `
          <div class="service-toggle-card ${activeCls}" onclick="App.toggleServiceSetting('${s.id}')">
            <div class="service-toggle-left">
              <img src="${s.logo_url}" class="service-toggle-logo" alt="${this.escapeHtml(s.name)}" />
              <div>
                <span class="service-toggle-name">${this.escapeHtml(s.name)}</span>
                ${s.region_badge ? `<span class="service-toggle-badge">${this.escapeHtml(s.region_badge)}</span>` : ''}
              </div>
            </div>
            <div class="service-toggle-checkbox">${checkIcon}</div>
          </div>
        `;
      }).join('');

      return `
        <div class="settings-group">
          <span class="settings-group-title">${this.escapeHtml(groupName)}</span>
          <div class="settings-services-grid">${cardsHtml}</div>
        </div>
      `;
    }).join('');
  },

  async toggleServiceSetting(serviceId) {
    if (!this.cachedSettings) return;
    const enabled = new Set(this.cachedSettings.enabled_services || []);
    if (enabled.has(serviceId)) {
      enabled.delete(serviceId);
    } else {
      enabled.add(serviceId);
    }

    const updated = await API.updateSettings(Array.from(enabled));
    if (updated) {
      this.cachedSettings = updated;
      this.renderSettingsServices();
    }
  },

  async resetSettingsToDefaults() {
    const updated = await API.resetSettings();
    if (updated) {
      this.cachedSettings = updated;
      this.renderSettingsServices();
    }
  },

  async renderRecentSearches() {
    const container = document.getElementById('recentSearchesChips');
    if (!container) return;

    const data = await API.getRecentSearches();
    const items = data.results || [];
    if (items.length === 0) {
      container.innerHTML = '';
      return;
    }

    container.innerHTML = items.map(item => {
      const escaped = this.escapeHtml(item);
      const paramStr = escaped.replace(/'/g, "\\'");
      return `<span class="chip" onclick="App.quickSearch('${paramStr}')">${escaped}</span>`;
    }).join('');
  },

  cachedFavSet: new Set(),
  currentFavMediaTypeFilter: 'all',
  favCurrentOffset: 0,
  favPageSize: 48,

  async loadFavoriteIds() {
    try {
      const ids = await API.getFavoriteIds();
      this.cachedFavSet = new Set(ids);
    } catch (e) {
      this.cachedFavSet = new Set();
    }
  },

  async renderFavoritesShelf() {
    const section = document.getElementById('favoritesSection');
    const moviesGroup = document.getElementById('favMoviesGroup');
    const moviesChips = document.getElementById('favMoviesChips');
    const tvGroup = document.getElementById('favTvGroup');
    const tvChips = document.getElementById('favTvChips');
    const btnViewAll = document.getElementById('btnViewAllFavs');
    if (!section) return;

    try {
      const [summary, shelf] = await Promise.all([
        API.getFavoritesSummary(),
        API.getFavoritesShelf()
      ]);
      const total = summary.total || 0;
      
      if (total === 0) {
        section.style.display = 'none';
        return;
      }
      section.style.display = 'flex';

      const movies = shelf.movies || [];
      const tvShows = shelf.tv || [];

      if (moviesGroup && moviesChips) {
        if (movies.length > 0) {
          moviesGroup.style.display = 'flex';
          moviesChips.innerHTML = movies.map(m => {
            const titleEsc = this.escapeHtml(m.title);
            return `<span class="chip" onclick="App.loadTitleAvailability('movie', ${m.tmdb_id})">${titleEsc}</span>`;
          }).join('');
        } else {
          moviesGroup.style.display = 'none';
        }
      }

      if (tvGroup && tvChips) {
        if (tvShows.length > 0) {
          tvGroup.style.display = 'flex';
          tvChips.innerHTML = tvShows.map(t => {
            const titleEsc = this.escapeHtml(t.title);
            return `<span class="chip" onclick="App.loadTitleAvailability('tv', ${t.tmdb_id})">${titleEsc}</span>`;
          }).join('');
        } else {
          tvGroup.style.display = 'none';
        }
      }

      // Show View All button with total count
      if (btnViewAll) {
        btnViewAll.style.display = 'inline-block';
        btnViewAll.textContent = `· View all (${total}) →`;
      }
    } catch (e) {
      section.style.display = 'none';
    }
  },

  setFavMediaTypeFilter(type) {
    this.currentFavMediaTypeFilter = type;
    this.favCurrentOffset = 0;
    const tabAll = document.getElementById('favTabAll');
    const tabMovies = document.getElementById('favTabMovies');
    const tabTv = document.getElementById('favTabTv');

    if (tabAll) tabAll.classList.toggle('active', type === 'all');
    if (tabMovies) tabMovies.classList.toggle('active', type === 'movie');
    if (tabTv) tabTv.classList.toggle('active', type === 'tv');

    const filterInput = document.getElementById('favFilterInput');
    const q = filterInput ? filterInput.value : '';
    this.renderAllFavoritesGrid(q);
  },

  loadMoreFavorites() {
    this.favCurrentOffset += this.favPageSize;
    const filterInput = document.getElementById('favFilterInput');
    const q = filterInput ? filterInput.value : '';
    this.renderAllFavoritesGrid(q, true);
  },

  async showAllFavorites() {
    const emptyState = document.getElementById('emptyState');
    const availabilityView = document.getElementById('availabilityView');
    const loadingState = document.getElementById('loadingState');
    const allFavView = document.getElementById('allFavoritesView');
    const filterInput = document.getElementById('favFilterInput');

    if (emptyState) emptyState.style.display = 'none';
    if (availabilityView) availabilityView.style.display = 'none';
    if (loadingState) loadingState.style.display = 'none';
    if (allFavView) allFavView.style.display = 'flex';

    this.currentFavMediaTypeFilter = 'all';
    this.favCurrentOffset = 0;

    const tabAll = document.getElementById('favTabAll');
    const tabMovies = document.getElementById('favTabMovies');
    const tabTv = document.getElementById('favTabTv');
    if (tabAll) tabAll.classList.add('active');
    if (tabMovies) tabMovies.classList.remove('active');
    if (tabTv) tabTv.classList.remove('active');

    if (filterInput) {
      filterInput.value = '';
      filterInput.focus();
    }
    await this.renderAllFavoritesGrid('');
  },

  async renderAllFavoritesGrid(query = '', append = false) {
    const container = document.getElementById('favGridContainer');
    const countAllEl = document.getElementById('favCountAll');
    const countMoviesEl = document.getElementById('favCountMovies');
    const countTvEl = document.getElementById('favCountTv');
    if (!container) return;

    if (!append) {
      this.favCurrentOffset = 0;
    }

    try {
      const [summaryRes, itemsRes] = await Promise.all([
        API.getFavoritesSummary(),
        API.getFavorites(
          this.currentFavMediaTypeFilter,
          'added_at_desc',
          this.favCurrentOffset,
          this.favPageSize,
          query
        )
      ]);

      const totalGlobal = summaryRes.total || 0;
      const totalMovies = summaryRes.movies || 0;
      const totalTv = summaryRes.tv || 0;
      const items = itemsRes.favorites || [];
      const pageCount = items.length;

      // Update Type Tab Counts accurately
      if (countAllEl) countAllEl.textContent = totalGlobal;
      if (countMoviesEl) countMoviesEl.textContent = totalMovies;
      if (countTvEl) countTvEl.textContent = totalTv;

      if (!append && items.length === 0) {
        container.innerHTML = `
          <div class="no-providers-card" style="grid-column: 1 / -1;">
            <p><strong>${query ? 'No Matching Favorites' : 'No Favorites Saved Yet'}</strong></p>
            <p style="margin-top:6px;">${query ? 'Try a different search term.' : 'Click the star icon ⭐ or press F on any title to save it.'}</p>
          </div>
        `;
        return;
      }

      const renderCard = (fav) => {
        const titleEsc = this.escapeHtml(fav.title);
        const yearText = fav.year ? `${fav.year} · ` : '';
        const typeText = fav.media_type === 'tv' ? 'TV Series' : 'Movie';

        return `
          <div class="fav-card" onclick="App.loadTitleAvailability('${fav.media_type}', ${fav.tmdb_id})">
            <div class="fav-card-meta">
              <span class="fav-card-title">${titleEsc}</span>
              <div style="display:flex; align-items:center; margin-top:2px;">
                <span class="fav-card-sub">${yearText}${typeText}</span>
              </div>
            </div>
            <button class="btn-star favorited" onclick="event.stopPropagation(); App.removeFavoriteFromGrid(${fav.tmdb_id}, '${fav.media_type}')" title="Remove from Favorites">
              <svg class="star-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" stroke="currentColor" stroke-width="1.6">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
              </svg>
            </button>
          </div>
        `;
      };

      const cardsHtml = items.map(renderCard).join('');

      let gridEl = document.getElementById('favCardsInnerGrid');
      let loadMoreBtn = document.getElementById('favLoadMoreContainer');

      if (!append || !gridEl) {
        container.innerHTML = `
          <div id="favCardsInnerGrid" class="fav-grid-container">
            ${cardsHtml}
          </div>
          <div id="favLoadMoreContainer" style="display:flex; justify-content:center; margin-top:16px; margin-bottom:8px;"></div>
        `;
        gridEl = document.getElementById('favCardsInnerGrid');
        loadMoreBtn = document.getElementById('favLoadMoreContainer');
      } else {
        gridEl.insertAdjacentHTML('beforeend', cardsHtml);
      }

      // If page is full (48 items), show Load More button
      if (pageCount >= this.favPageSize) {
        loadMoreBtn.innerHTML = `
          <button class="chip" onclick="App.loadMoreFavorites()" style="padding:8px 24px; font-weight:700; cursor:pointer;">
            Load More Titles →
          </button>
        `;
      } else {
        loadMoreBtn.innerHTML = '';
      }
    } catch (e) {
      console.error('Failed to render favorites grid:', e);
    }
  },

  async removeFavoriteFromGrid(tmdbId, mediaType) {
    try {
      await API.removeFavorite(tmdbId, mediaType);
      this.cachedFavSet.delete(`${mediaType}_${tmdbId}`);
      await this.loadFavoriteIds();
      const filterInput = document.getElementById('favFilterInput');
      const q = filterInput ? filterInput.value : '';
      await this.renderAllFavoritesGrid(q);
      await this.renderFavoritesShelf();
    } catch (e) {
      console.error('Failed to remove favorite:', e);
    }
  },

  async toggleFavoriteFromGrid(tmdbId, mediaType, title) {
    return this.removeFavoriteFromGrid(tmdbId, mediaType);
  },

  bindEvents() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    const dropdown = document.getElementById('searchDropdown');
    const favFilterInput = document.getElementById('favFilterInput');

    if (favFilterInput) {
      favFilterInput.addEventListener('input', (e) => {
        this.renderAllFavoritesGrid(e.target.value.trim());
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const q = e.target.value.trim();
        if (clearBtn) clearBtn.style.display = q ? 'flex' : 'none';

        clearTimeout(this.searchTimer);
        if (!q) {
          this.closeDropdown();
          return;
        }
        this.searchTimer = setTimeout(() => this.performAutocomplete(q), 180);
      });

      searchInput.addEventListener('keydown', (e) => this.handleSearchKeydown(e));
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.resetSearch());
    }

    // Global Hotkeys
    document.addEventListener('keydown', (e) => {
      const isInputFocused = document.activeElement === searchInput || document.activeElement === favFilterInput;

      if ((e.key === 'F' && e.shiftKey) || (e.key === 'f' && e.shiftKey)) {
        e.preventDefault();
        this.showAllFavorites();
      } else if (e.key === '/' && !isInputFocused) {
        e.preventDefault();
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      } else if (!isInputFocused && this.currentDetails) {
        if (e.key === '0') {
          this.setFilter('all');
        } else if (e.key >= '1' && e.key <= '9') {
          const idx = parseInt(e.key, 10) - 1;
          const enabledList = (this.cachedSettings && this.cachedSettings.enabled_services) || ['netflix', 'prime', 'max', 'paramount_plus'];
          if (idx < enabledList.length) {
            this.setFilter(enabledList[idx]);
          }
        } else if (e.key === 'f' || e.key === 'F') {
          e.preventDefault();
          this.toggleFavorite();
        } else if (e.key === ',' || e.key === 's' || e.key === 'S') {
          e.preventDefault();
          this.toggleSettings();
        }
      } else if (!isInputFocused && (e.key === ',' || e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        this.toggleSettings();
      } else if (e.key === 'Escape') {
        const settingsModal = document.getElementById('settingsModal');
        const allFavView = document.getElementById('allFavoritesView');
        if (settingsModal && settingsModal.style.display !== 'none') {
          this.closeSettings();
        } else if (dropdown && dropdown.style.display !== 'none') {
          this.closeDropdown();
        } else if (allFavView && allFavView.style.display !== 'none') {
          this.resetSearch();
        } else if (isInputFocused) {
          this.resetSearch();
        } else if (this.currentFilter !== 'all') {
          this.setFilter('all');
        }
      }
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
      const wrapper = document.querySelector('.search-section');
      if (wrapper && !wrapper.contains(e.target)) {
        this.closeDropdown();
      }
    });
  },

  async performAutocomplete(query) {
    try {
      // Direct favorites query support (* or @fav)
      if (query === '*' || query === '@fav') {
        const favRes = await API.getFavorites(null, null, 'added_at_desc', 0, 10);
        const favs = favRes.favorites || [];
        this.searchResults = favs.map(f => ({
          id: f.tmdb_id,
          media_type: f.media_type,
          title: f.title,
          year: f.year,
          is_favorite: true
        }));
        this.selectedIndex = -1;
        this.renderDropdown();
        return;
      }

      const data = await API.searchMulti(query);
      if (!data || !data.results) return;

      // Filter movies & tv and attach favorite priority flag instantly from in-memory set
      let filtered = data.results.filter(
        item => item.media_type === 'movie' || item.media_type === 'tv'
      ).map(item => ({
        ...item,
        is_favorite: this.cachedFavSet.has(`${item.media_type}_${item.id}`)
      }));

      // Sort favorites to the top
      filtered.sort((a, b) => (b.is_favorite ? 1 : 0) - (a.is_favorite ? 1 : 0));

      this.searchResults = filtered.slice(0, 8);
      this.selectedIndex = -1;
      this.renderDropdown();
    } catch (err) {
      console.error('Search error:', err);
    }
  },

  renderDropdown() {
    const dropdown = document.getElementById('searchDropdown');
    const list = document.getElementById('searchResultsList');
    if (!dropdown || !list) return;

    if (this.searchResults.length === 0) {
      this.closeDropdown();
      return;
    }

    list.innerHTML = this.searchResults.map((item, idx) => {
      const title = item.title || item.name || 'Untitled';
      const year = item.year ? `(${item.year})` : '';
      const typeLabel = item.media_type === 'tv' ? 'TV Series' : 'Movie';
      const isSelected = idx === this.selectedIndex ? 'active' : '';
      const favStar = item.is_favorite ? '<span class="fav-star-indicator">★</span>' : '';

      return `
        <li class="search-result-item ${isSelected}" data-index="${idx}">
          <div class="result-main">
            ${favStar}
            <span class="result-title">${this.escapeHtml(title)}</span>
            <span class="result-year">${year}</span>
          </div>
          <span class="result-badge">${typeLabel}</span>
        </li>
      `;
    }).join('');

    list.querySelectorAll('.search-result-item').forEach(el => {
      el.addEventListener('click', () => {
        const index = parseInt(el.dataset.index, 10);
        this.selectResultItem(index);
      });
    });

    dropdown.style.display = 'block';
  },

  closeDropdown() {
    const dropdown = document.getElementById('searchDropdown');
    if (dropdown) dropdown.style.display = 'none';
    this.selectedIndex = -1;
  },

  handleSearchKeydown(e) {
    const dropdown = document.getElementById('searchDropdown');
    const isOpen = dropdown && dropdown.style.display === 'block';

    if (!isOpen || this.searchResults.length === 0) {
      if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (val) this.performFullSearch(val);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex + 1) % this.searchResults.length;
      this.updateActiveDropdownItem();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex - 1 + this.searchResults.length) % this.searchResults.length;
      this.updateActiveDropdownItem();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (this.selectedIndex >= 0 && this.selectedIndex < this.searchResults.length) {
        this.selectResultItem(this.selectedIndex);
      } else {
        const val = e.target.value.trim();
        if (val) this.performFullSearch(val);
      }
    }
  },

  updateActiveDropdownItem() {
    const items = document.querySelectorAll('.search-result-item');
    items.forEach((el, idx) => {
      el.classList.toggle('active', idx === this.selectedIndex);
      if (idx === this.selectedIndex) {
        el.scrollIntoView({ block: 'nearest' });
      }
    });
  },

  async selectResultItem(index) {
    const item = this.searchResults[index];
    if (!item) return;

    this.closeDropdown();
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.value = item.title || item.name || '';
    }

    await this.loadTitleAvailability(item.media_type, item.id);
  },

  async quickSearch(title) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.value = title;
    }
    await this.performFullSearch(title);
  },

  async performFullSearch(query) {
    this.closeDropdown();
    this.setLoading(true);

    try {
      const data = await API.searchMulti(query);
      if (!data || !data.results || data.results.length === 0) {
        this.renderNoResults(query);
        return;
      }

      const match = data.results.find(i => i.media_type === 'movie' || i.media_type === 'tv');
      if (match) {
        await this.loadTitleAvailability(match.media_type, match.id);
      } else {
        this.renderNoResults(query);
      }
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      this.setLoading(false);
    }
  },

  async loadTitleAvailability(mediaType, id) {
    this.setLoading(true);
    try {
      const details = await API.getDetails(mediaType, id);
      this.currentDetails = details;
      this.currentFilter = 'all';

      const title = details ? (details.title || details.name) : null;
      if (title) {
        await RecentSearches.add(title);
      }

      this.renderAvailability(details);
    } catch (err) {
      console.error('Failed to load title details:', err);
    } finally {
      this.setLoading(false);
    }
  },

  setLoading(isLoading) {
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const availabilityView = document.getElementById('availabilityView');
    const allFavView = document.getElementById('allFavoritesView');

    if (isLoading) {
      if (emptyState) emptyState.style.display = 'none';
      if (availabilityView) availabilityView.style.display = 'none';
      if (allFavView) allFavView.style.display = 'none';
      if (loadingState) loadingState.style.display = 'flex';
    } else {
      if (loadingState) loadingState.style.display = 'none';
    }
  },

  setFilter(filterId) {
    this.currentFilter = filterId;
    if (this.currentDetails) {
      this.renderServiceFilterBar(this.currentDetails.service_counts || {});
      this.renderRegionalGrid(this.currentDetails.regions || [], this.currentFilter);
    }
  },

  renderAvailability(details) {
    const emptyState = document.getElementById('emptyState');
    const availabilityView = document.getElementById('availabilityView');
    const titleEl = document.getElementById('selectedTitle');
    const subtextEl = document.getElementById('titleSubtext');
    const trailerBtn = document.getElementById('btnWatchTrailer');

    if (!details || !availabilityView) return;

    if (emptyState) emptyState.style.display = 'none';
    availabilityView.style.display = 'flex';

    // Pure Unboxed Header Meta
    if (titleEl) titleEl.textContent = details.title || details.name || 'Untitled';
    if (subtextEl) {
      const yearText = details.year || '';
      const typeLabel = details.media_type === 'tv' ? 'TV Series' : 'Movie';
      subtextEl.textContent = yearText ? `${yearText} · ${typeLabel}` : typeLabel;
    }

    // Monoline Star Favorite State
    const starBtn = document.getElementById('btnFavStar');
    if (starBtn) {
      starBtn.classList.toggle('favorited', !!details.is_favorite);
      starBtn.title = details.is_favorite ? 'Remove from Favorites (Press F)' : 'Add to Favorites (Press F)';
    }

    // Trailer Button
    if (trailerBtn) {
      trailerBtn.style.display = (details.trailer && details.trailer.url) ? 'inline-flex' : 'none';
    }

    // Tier 1: Local Hero Card
    this.renderLocalHeroCard(details.local_country);

    // Tier 2: Interactive Service Filter Toolbar
    this.renderServiceFilterBar(details.service_counts || {});

    // Tier 3: Regional Bento Grid
    this.renderRegionalGrid(details.regions || [], this.currentFilter);
  },

  async toggleFavorite() {
    if (!this.currentDetails) return;
    const payload = {
      id: this.currentDetails.id,
      media_type: this.currentDetails.media_type || 'movie',
      title: this.currentDetails.title || this.currentDetails.name,
      year: this.currentDetails.year || '',
      poster_path: this.currentDetails.poster_path || ''
    };
    try {
      const res = await API.toggleFavorite(payload);
      this.currentDetails.is_favorite = !!res.is_favorite;
      if (res.is_favorite) {
        this.cachedFavSet.add(`${payload.media_type}_${payload.id}`);
      } else {
        this.cachedFavSet.delete(`${payload.media_type}_${payload.id}`);
      }
      const starBtn = document.getElementById('btnFavStar');
      if (starBtn) {
        starBtn.classList.toggle('favorited', !!res.is_favorite);
        starBtn.title = res.is_favorite ? 'Remove from Favorites (Press F)' : 'Add to Favorites (Press F)';
      }
      await this.loadFavoriteIds();
      await this.renderFavoritesShelf();
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  },

  async playTrailer() {
    if (!this.currentDetails || !this.currentDetails.trailer || !this.currentDetails.trailer.url) return;
    const title = this.currentDetails.title || this.currentDetails.name || 'Trailer';
    try {
      await API.playInMpv(this.currentDetails.trailer.url, title);
    } catch (e) {
      console.error('Failed to launch MPV trailer:', e);
    }
  },

  renderLocalHeroCard(localCountry) {
    const heroContainer = document.getElementById('localHeroCard');
    if (!heroContainer) return;

    if (!localCountry) {
      heroContainer.style.display = 'none';
      return;
    }

    heroContainer.style.display = 'flex';

    if (localCountry.available && localCountry.providers && localCountry.providers.length > 0) {
      const providerNames = localCountry.providers.map(p => p.name).join(', ');
      const logosHtml = localCountry.providers.map(p => `
        <img 
          class="hero-logo" 
          src="${p.logo_url || `/assets/logos/${p.id}.png`}" 
          alt="${this.escapeHtml(p.name)}" 
          title="${this.escapeHtml(p.name)}" 
        />
      `).join('');

      heroContainer.innerHTML = `
        <div class="hero-left">
          <span class="hero-flag">${localCountry.flag || '🇺🇸'}</span>
          <div class="hero-meta">
            <span class="hero-country-name">${this.escapeHtml(localCountry.name)}</span>
            <span class="hero-status-text">Available now on ${providerNames}</span>
          </div>
        </div>
        <div class="hero-providers">
          ${logosHtml}
        </div>
      `;
    } else {
      heroContainer.innerHTML = `
        <div class="hero-left">
          <span class="hero-flag">${localCountry.flag || '🇺🇸'}</span>
          <div class="hero-meta">
            <span class="hero-country-name">${this.escapeHtml(localCountry.name)}</span>
            <span class="hero-status-text">Not streaming locally — check international availability below</span>
          </div>
        </div>
      `;
    }
  },

  renderServiceFilterBar(counts) {
    const filterBar = document.getElementById('serviceFilterBar');
    if (!filterBar) return;

    const allServices = (this.cachedSettings && this.cachedSettings.services) || [];
    const enabledSet = new Set((this.cachedSettings && this.cachedSettings.enabled_services) || ['netflix', 'prime', 'max', 'paramount_plus']);

    const enabledServicesList = allServices.filter(s => enabledSet.has(s.id));

    const filters = [
      { id: 'all', name: 'All Services', count: counts.all || 0, logo: null, keyNum: '0' },
      ...enabledServicesList.map((s, idx) => ({
        id: s.id,
        name: s.name,
        count: counts[s.id] || 0,
        logo: s.logo_url,
        keyNum: String(idx + 1)
      }))
    ];

    filterBar.innerHTML = filters.map(f => {
      const isActive = this.currentFilter === f.id ? 'active' : '';
      const logoImg = f.logo ? `<img src="${f.logo}" class="pill-logo" alt="${f.name}" />` : '';

      return `
        <button 
          class="filter-pill ${isActive}" 
          onclick="App.setFilter('${f.id}')"
          title="Filter by ${f.name} (Press ${f.keyNum})"
        >
          ${logoImg}
          <span>${f.name}</span>
          <span class="pill-count">${f.count}</span>
        </button>
      `;
    }).join('');
  },

  renderRegionalGrid(regions, filter) {
    const container = document.getElementById('regionalGridContainer');
    if (!container) return;

    if (!regions || regions.length === 0) {
      container.innerHTML = `
        <div class="no-providers-card">
          <p><strong>Not Available to Stream</strong></p>
          <p style="margin-top:6px;">This title is not currently streaming on Netflix, Prime Video, Max, or Paramount+ (USA).</p>
        </div>
      `;
      return;
    }

    let renderedGroupsHtml = '';
    let totalMatchingCountries = 0;

    regions.forEach(region => {
      // Filter countries by service
      const matchingCountries = (region.countries || []).filter(c => {
        if (filter === 'all') return true;
        return (c.providers || []).some(p => p.id === filter);
      });

      if (matchingCountries.length === 0) return;

      totalMatchingCountries += matchingCountries.length;

      const cardsHtml = matchingCountries.map(country => {
        // Render provider logos for this country
        const providersHtml = (country.providers || []).map(p => {
          const logoUrl = p.logo_url || `/assets/logos/${p.id}.png`;
          const titleText = p.id === 'paramount_plus' ? 'Paramount+ (USA Only)' : p.name;
          const isDimmed = (filter !== 'all' && p.id !== filter) ? 'opacity: 0.35;' : '';

          return `
            <img 
              class="bento-logo" 
              src="${logoUrl}" 
              alt="${this.escapeHtml(p.name)}" 
              title="${this.escapeHtml(titleText)}" 
              style="${isDimmed}"
              loading="lazy"
            />
          `;
        }).join('');

        return `
          <div class="bento-card">
            <div class="bento-left">
              <span class="bento-flag">${country.flag || '🌐'}</span>
              <span class="bento-name" title="${this.escapeHtml(country.name)}">${this.escapeHtml(country.name)}</span>
            </div>
            <div class="bento-providers">
              ${providersHtml}
            </div>
          </div>
        `;
      }).join('');

      renderedGroupsHtml += `
        <div class="region-group">
          <div class="region-header">
            <span class="region-title">${region.emoji || '🌐'} ${this.escapeHtml(region.name)}</span>
            <span class="region-badge">${matchingCountries.length}</span>
          </div>
          <div class="bento-grid">
            ${cardsHtml}
          </div>
        </div>
      `;
    });

    if (totalMatchingCountries === 0) {
      container.innerHTML = `
        <div class="no-providers-card">
          <p><strong>No Matches for Selected Service</strong></p>
          <p style="margin-top:6px;">This title is not available on this platform in any country. Click "All Services" (or press 0) to view all.</p>
        </div>
      `;
    } else {
      container.innerHTML = renderedGroupsHtml;
    }
  },

  resetSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    const emptyState = document.getElementById('emptyState');
    const availabilityView = document.getElementById('availabilityView');
    const loadingState = document.getElementById('loadingState');
    const trailerBtn = document.getElementById('btnWatchTrailer');

    if (searchInput) {
      searchInput.value = '';
      searchInput.focus();
    }
    if (clearBtn) clearBtn.style.display = 'none';
    if (trailerBtn) trailerBtn.style.display = 'none';
    this.closeDropdown();
    this.searchResults = [];
    this.currentDetails = null;
    this.currentFilter = 'all';

    const starBtn = document.getElementById('btnFavStar');
    if (starBtn) {
      starBtn.classList.remove('favorited');
    }

    const allFavView = document.getElementById('allFavoritesView');
    if (allFavView) allFavView.style.display = 'none';

    if (loadingState) loadingState.style.display = 'none';
    if (availabilityView) availabilityView.style.display = 'none';
    if (emptyState) {
      emptyState.style.display = 'flex';
      this.renderRecentSearches();
      this.renderFavoritesShelf();
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};

// Bootstrap application on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
