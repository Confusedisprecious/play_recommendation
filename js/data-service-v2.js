(function () {
  'use strict';

  const paths = {
    spots: 'data/spots.json',
    promotions: 'data/promotions.json',
    hot: 'data/hot_events.json',
    social: 'data/social_feed.json',
    update: 'data/last_update.json',
    media: 'data/media_gallery.json',
    weather: 'data/weather.json'
  };

  async function fetchJson(path, required) {
    try {
      // no-cache：保留协商缓存（ETag/Last-Modified），数据未变时命中 304，回访流量大幅降低
      const response = await fetch(path, { cache: 'no-cache' });
      if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      if (required) throw error;
      console.warn(`Optional data unavailable: ${path}`);
      return null;
    }
  }

  function isLocalImage(value) {
    return typeof value === 'string' && /^images\//.test(value);
  }

  function sanitizeGallery(item) {
    const gallery = Array.isArray(item.gallery) ? item.gallery.filter(isLocalImage) : [];
    return [...new Set([item.image, ...gallery].filter(isLocalImage))].slice(0, 5);
  }

  function normalizeSocial(payload) {
    if (!payload || !Array.isArray(payload.items)) return { items: [], platforms: [], source_health: {}, policy: {} };
    return {
      ...payload,
      items: payload.items.filter((item) => item && ['reviewed', 'auto_trusted'].includes(item.review_status) && /^https?:\/\//.test(item.url || ''))
    };
  }

  async function loadAll() {
    const entries = await Promise.all([
      fetchJson(paths.spots, true),
      fetchJson(paths.promotions, false),
      fetchJson(paths.hot, false),
      fetchJson(paths.social, false),
      fetchJson(paths.update, false),
      fetchJson(paths.media, false),
      fetchJson(paths.weather, false)
    ]);

    const [spots, promotions, hot, social, update, media, weather] = entries;
    if (!Array.isArray(spots) || spots.length === 0) throw new Error('场所数据为空');

    return {
      spots: spots
        .filter((item) => item && item.id && item.name && isLocalImage(item.image))
        .map((item) => ({ ...item, gallery: sanitizeGallery(item) })),
      promotions: Array.isArray(promotions) ? promotions : [],
      hot: Array.isArray(hot) ? hot : [],
      social: normalizeSocial(social),
      update: update || {},
      media: media && Array.isArray(media.items) ? media.items : [],
      weather: weather && weather.current ? weather : null,
      loadedAt: new Date().toISOString()
    };
  }

  window.WeekendDataService = { loadAll };
}());
