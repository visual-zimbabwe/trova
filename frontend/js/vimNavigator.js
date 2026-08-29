// OmaTrova Vim & Desktop Spatial Keyboard Navigation Engine
// Supports pure vertical natural grid movement (j/k/h/l + Arrow keys)

const VimNavigator = {
  currentCardIndex: 0,
  focusedElement: null,

  init() {
    window.addEventListener('keydown', (e) => this.handleKeyDown(e));
  },

  handleKeyDown(e) {
    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    const isInput = activeTag === 'input' || activeTag === 'textarea';

    if (e.key === 'Escape') {
      if (isInput) document.activeElement.blur();
      App.closeModals();
      return;
    }

    if (isInput) return;

    // View Navigation (1-5)
    if (['1', '2', '3', '4', '5'].includes(e.key)) {
      const views = ['home', 'discover', 'watchlist', 'analytics', 'franchises'];
      const target = views[parseInt(e.key) - 1];
      if (target) App.switchView(target);
      return;
    }

    // Search trigger: / or Ctrl+K
    if (e.key === '/' || (e.ctrlKey && e.key.toLowerCase() === 'k')) {
      e.preventDefault();
      App.openSearchModal();
      return;
    }

    // Get all visible poster cards in current active view
    const visibleCards = this.getVisibleCards();
    if (!visibleCards.length) return;

    const cols = this.getGridColumns(visibleCards);

    if (e.key === 'j' || e.key === 'ArrowDown') {
      e.preventDefault();
      this.moveIndex(cols, visibleCards);
    } else if (e.key === 'k' || e.key === 'ArrowUp') {
      e.preventDefault();
      this.moveIndex(-cols, visibleCards);
    } else if (e.key === 'l' || e.key === 'ArrowRight') {
      e.preventDefault();
      this.moveIndex(1, visibleCards);
    } else if (e.key === 'h' || e.key === 'ArrowLeft') {
      e.preventDefault();
      this.moveIndex(-1, visibleCards);
    } else if (e.key === 'Enter') {
      this.activateFocused();
    } else if (e.key === ' ' || e.key === 't' || e.key === 'T') {
      e.preventDefault();
      App.playTrailerFocused();
    } else if (e.key === 'w' || e.key === 'W') {
      App.toggleWatchlistFocused();
    }
  },

  getVisibleCards() {
    // If a modal is open, search within modal
    const openModal = document.querySelector('.modal-overlay.open .modal-dialog');
    if (openModal) {
      return Array.from(openModal.querySelectorAll('.poster-card'));
    }

    // Otherwise find all visible cards in current view section
    const currentViewSection = document.querySelector('.view-section:not([style*="display: none"]):not([style*="display:none"])');
    if (!currentViewSection) return [];
    return Array.from(currentViewSection.querySelectorAll('.poster-card'));
  },

  getGridColumns(cards) {
    if (!cards.length || cards.length === 1) return 1;
    const firstTop = cards[0].getBoundingClientRect().top;
    let count = 0;
    for (let c of cards) {
      if (Math.abs(c.getBoundingClientRect().top - firstTop) < 20) {
        count++;
      } else {
        break;
      }
    }
    return Math.max(1, count);
  },

  moveIndex(delta, cards) {
    if (!cards.length) return;
    this.currentCardIndex = Math.max(0, Math.min(cards.length - 1, this.currentCardIndex + delta));
    this.updateFocus(cards);
  },

  updateFocus(cards) {
    document.querySelectorAll('.poster-card.vim-focused').forEach(c => c.classList.remove('vim-focused'));
    cards = cards || this.getVisibleCards();
    if (!cards.length) return;

    if (this.currentCardIndex >= cards.length) {
      this.currentCardIndex = 0;
    }

    const target = cards[this.currentCardIndex];
    if (target) {
      target.classList.add('vim-focused');
      target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      this.focusedElement = target;
    }
  },

  activateFocused() {
    if (this.focusedElement) {
      this.focusedElement.click();
    }
  }
};
