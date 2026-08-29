// Trova Live Omarchy System Theme Store

const ThemeStore = {
  currentTheme: null,

  init() {
    this.connectEventStream();
    this.pollTheme();
  },

  connectEventStream() {
    try {
      const eventSource = new EventSource('/api/events');
      eventSource.onmessage = (event) => {
        try {
          const themeData = JSON.parse(event.data);
          this.applyTheme(themeData);
        } catch (e) {
          console.error('[Theme Parse Error]', e);
        }
      };
      eventSource.onerror = () => {
        setTimeout(() => this.pollTheme(), 3000);
      };
    } catch (e) {
      this.pollTheme();
    }
  },

  async pollTheme() {
    const data = await API.getTheme();
    if (data) {
      this.applyTheme(data);
    }
  },

  applyTheme(themeData) {
    if (!themeData || !themeData.colors) return;
    this.currentTheme = themeData;
    const { colors, name, mode } = themeData;
    const root = document.documentElement;

    // Apply all synthesized Omarchy color variables
    root.style.setProperty('--om-bg-root', colors.bg_root);
    root.style.setProperty('--om-bg-base', colors.bg_base);
    root.style.setProperty('--om-bg-surface', colors.bg_surface);
    root.style.setProperty('--om-bg-card', colors.bg_card);
    root.style.setProperty('--om-bg-hover', colors.bg_hover);
    root.style.setProperty('--om-bg-selected', colors.bg_selected);
    root.style.setProperty('--om-bg-glass', colors.bg_glass);
    root.style.setProperty('--om-bg-modal', colors.bg_modal);

    root.style.setProperty('--om-text-title', colors.text_title);
    root.style.setProperty('--om-text-primary', colors.text_primary);
    root.style.setProperty('--om-text-secondary', colors.text_secondary);
    root.style.setProperty('--om-text-muted', colors.text_muted);
    root.style.setProperty('--om-text-on-accent', colors.text_on_accent || '#ffffff');

    root.style.setProperty('--om-border', colors.border);
    root.style.setProperty('--om-border-light', colors.border_light);
    root.style.setProperty('--om-border-focus', colors.border_focus || colors.accent);

    root.style.setProperty('--om-accent', colors.accent);
    root.style.setProperty('--om-accent-hover', colors.accent_hover);
    root.style.setProperty('--om-accent-dim', colors.accent_dim);
    root.style.setProperty('--om-accent-glow', colors.accent_glow);

    root.style.setProperty('--om-gold', colors.gold || '#d4a853');
    root.style.setProperty('--om-badge-imdb', colors.badge_imdb);
    root.style.setProperty('--om-badge-rt', colors.badge_rt);
    root.style.setProperty('--om-badge-meta', colors.badge_meta);
    root.style.setProperty('--om-badge-tmdb', colors.badge_tmdb);

    // Update root dataset mode & theme name
    root.dataset.themeMode = mode || 'dark';
    root.dataset.themeName = name || 'Omarchy';

    const indicator = document.getElementById('themeNameDisplay');
    if (indicator) {
      indicator.textContent = `${name || 'Omarchy'} (${mode})`;
    }
  }
};
