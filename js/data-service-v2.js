(function () {
  'use strict';

  const paths = {
    spots: 'data/spots.json',
    events: 'data/events.json',
    promotions: 'data/promotions.json',
    hot: 'data/hot_events.json',
    social: 'data/social_feed.json',
    update: 'data/last_update.json',
    media: 'data/media_gallery.json'
  };

  async function fetchJson(path, required) {
    try {
      const response = await fetch(path, { cache: 'no-store' });
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

  function qualityEvent(event) {
    const rejectedWords = /公告|公示|旅行社|保证金|责令改正|许可信息|注销/;
    return event &&
      typeof event.name === 'string' &&
      event.name.length >= 4 &&
      !rejectedWords.test(event.name) &&
      typeof event.description === 'string' &&
      event.description.length >= 12 &&
      !/^https?:\/\//.test(event.description) &&
      isLocalImage(event.image);
  }

  function normalizeSocial(payload) {
    if (!payload || !Array.isArray(payload.items)) return { items: [], platforms: [], source_health: {}, policy: {} };
    return {
      ...payload,
      items: payload.items.filter((item) => item && item.review_status === 'reviewed' && /^https?:\/\//.test(item.url || ''))
    };
  }

  async function loadAll() {
    const entries = await Promise.all([
      fetchJson(paths.spots, true),
      fetchJson(paths.events, false),
      fetchJson(paths.promotions, false),
      fetchJson(paths.hot, false),
      fetchJson(paths.social, false),
      fetchJson(paths.update, false),
      fetchJson(paths.media, false)
    ]);

    const [spots, events, promotions, hot, social, update, media] = entries;
    if (!Array.isArray(spots) || spots.length === 0) throw new Error('场所数据为空');

    return {
      spots: spots
        .filter((item) => item && item.id && item.name && isLocalImage(item.image))
        .map((item) => ({ ...item, gallery: sanitizeGallery(item) })),
      events: Array.isArray(events) ? events.filter(qualityEvent) : [],
      promotions: Array.isArray(promotions) ? promotions : [],
      hot: Array.isArray(hot) ? hot : [],
      social: normalizeSocial(social),
      update: update || {},
      media: media && Array.isArray(media.items) ? media.items : [],
      loadedAt: new Date().toISOString()
    };
  }

  window.WeekendDataService = { loadAll };
}());
