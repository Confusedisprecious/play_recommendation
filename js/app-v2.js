(function () {
  'use strict';

  const iconPath = 'assets/tabler-icons.svg';
  const pageSize = 9;
  const favoriteKey = 'wuhan-weekend-favorites-v2';
  const tweakKey = 'wuhan-weekend-tweaks-v2';
  const today = new Date();

  const state = {
    data: null,
    spots: [],
    filtered: [],
    visibleLimit: pageSize,
    favorites: new Set(),
    scene: 'weekend',
    query: '',
    filters: { age: 'all', category: 'all', district: 'all', price: 'all' },
    sort: 'recommended',
    favoritesOnly: false,
    activePlaceId: null,
    toastTimer: null
  };

  const sceneCopy = {
    weekend: '周末首选：综合热度、评分、活动与当前季节推荐。',
    indoor: '高温室内：以场馆、商场与室内乐园为主。',
    free: '几乎免费：优先筛选明确标注免费开放的场所。',
    toddler: '低龄友好：适合 0–6 岁家庭，减少高门槛项目。',
    outdoor: '户外放电：公园、绿道、骑行与自然体验。',
    niche: '小众宝藏：优先展示新开放、社区型和容易被忽略的亲子地点。'
  };

  const categoryLabels = { park: '公园自然', playground: '场馆乐园', mall: '商场街区', event: '活动' };
  const platformLabels = { xiaohongshu: '小红书', douyin: '抖音', weibo: '微博' };
  const platformMarks = { xiaohongshu: 'XHS', douyin: 'DY', weibo: 'WB' };

  const elements = {};

  function cacheElements() {
    [
      'loading-screen', 'hero-date', 'hero-search', 'hero-search-input', 'search-helper', 'data-status',
      'scene-rail', 'scene-description', 'hot-feature', 'hot-ranking', 'result-summary', 'filter-search',
      'filter-drawer-button', 'filter-groups', 'district-filters', 'sort-select', 'favorite-filter',
      'place-grid', 'empty-state', 'reset-filters', 'load-more', 'deal-grid', 'social-list',
      'pipeline-status', 'favorite-count', 'nav-favorite', 'mobile-favorite', 'mobile-menu-button',
      'mobile-menu', 'place-dialog', 'dialog-close', 'dialog-content', 'toast', 'footer-update',
      'tweaks-toggle', 'tweaks-panel', 'tweaks-close', 'density-select', 'photo-select'
    ].forEach((id) => { elements[toCamel(id)] = document.getElementById(id); });
  }

  function toCamel(value) {
    return value.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
  }

  function icon(name, className = '') {
    return `<svg class="icon ${className}" aria-hidden="true"><use href="${iconPath}#icon-${name}"></use></svg>`;
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function safeText(value, fallback = '待确认') {
    const text = String(value ?? '').trim();
    return text || fallback;
  }

  function normalize(value) {
    return String(value ?? '').toLocaleLowerCase('zh-CN').replace(/\s+/g, '');
  }

  function parseDate(value) {
    if (!value) return null;
    const normalized = String(value).replace(' ', 'T');
    const parsed = new Date(normalized);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function daysBetween(from, to = today) {
    if (!from) return null;
    return Math.max(0, Math.floor((to.getTime() - from.getTime()) / 86400000));
  }

  function formatDate(value, options = {}) {
    const date = value instanceof Date ? value : parseDate(value);
    if (!date) return '时间待确认';
    return new Intl.DateTimeFormat('zh-CN', options).format(date);
  }

  function relativeDate(value) {
    const date = parseDate(value);
    const days = daysBetween(date);
    if (days === null) return '发布时间待确认';
    if (days === 0) return '今天发布';
    if (days === 1) return '昨天发布';
    return `${days} 天前发布`;
  }

  function currentSeason() {
    const month = today.getMonth() + 1;
    if ([3, 4, 5].includes(month)) return 'spring';
    if ([6, 7, 8].includes(month)) return 'summer';
    if ([9, 10, 11].includes(month)) return 'autumn';
    return 'winter';
  }

  function loadPreferences() {
    try {
      const saved = JSON.parse(localStorage.getItem(favoriteKey) || '[]');
      state.favorites = new Set(saved.map(Number).filter(Number.isFinite));
      const tweaks = JSON.parse(localStorage.getItem(tweakKey) || '{}');
      applyTweaks(tweaks.density || 'airy', tweaks.photo || 'natural', false);
    } catch (_) {
      state.favorites = new Set();
    }
  }

  function saveFavorites() {
    try { localStorage.setItem(favoriteKey, JSON.stringify([...state.favorites])); } catch (_) { /* storage can be disabled */ }
  }

  function saveTweaks() {
    try {
      localStorage.setItem(tweakKey, JSON.stringify({ density: elements.densitySelect.value, photo: elements.photoSelect.value }));
    } catch (_) { /* storage can be disabled */ }
  }

  function enrichData(data) {
    const hotById = new Map(data.hot.map((item) => [Number(item.place_id), item]));
    const socialByPlace = new Map();
    data.social.items.forEach((item) => {
      const key = normalize(item.place_name);
      if (key) socialByPlace.set(key, (socialByPlace.get(key) || 0) + 1);
    });

    state.spots = data.spots.map((spot) => {
      const socialMentions = [...socialByPlace.entries()].reduce((total, [name, count]) => {
        const spotName = normalize(spot.name);
        return total + (spotName.includes(name) || name.includes(spotName) ? count : 0);
      }, 0);
      return { ...spot, hot: hotById.get(Number(spot.id)) || null, socialMentions };
    });
  }

  function bindEvents() {
    elements.heroSearch.addEventListener('submit', handleHeroSearch);
    elements.filterSearch.addEventListener('input', (event) => {
      state.query = event.target.value.trim();
      state.visibleLimit = pageSize;
      renderPlaces();
    });
    elements.sceneRail.addEventListener('click', handleSceneClick);
    elements.filterGroups.addEventListener('click', handleFilterChip);
    elements.sortSelect.addEventListener('change', (event) => {
      state.sort = event.target.value;
      state.visibleLimit = pageSize;
      renderPlaces();
    });
    elements.favoriteFilter.addEventListener('click', toggleFavoriteFilter);
    elements.navFavorite.addEventListener('click', showFavorites);
    elements.mobileFavorite.addEventListener('click', showFavorites);
    elements.placeGrid.addEventListener('click', handlePlaceGridClick);
    elements.placeGrid.addEventListener('keydown', handlePlaceGridKeydown);
    elements.hotFeature.addEventListener('click', openFromDataset);
    elements.hotRanking.addEventListener('click', openFromDataset);
    elements.dealGrid.addEventListener('click', openFromDataset);
    elements.loadMore.addEventListener('click', () => { state.visibleLimit += pageSize; renderPlaces(); });
    elements.resetFilters.addEventListener('click', resetFilters);
    elements.filterDrawerButton.addEventListener('click', toggleFilterDrawer);
    elements.mobileMenuButton.addEventListener('click', toggleMobileMenu);
    elements.mobileMenu.addEventListener('click', (event) => { if (event.target.matches('a')) closeMobileMenu(); });
    elements.dialogClose.addEventListener('click', closeDialog);
    elements.placeDialog.addEventListener('cancel', closeDialog);
    elements.placeDialog.addEventListener('click', (event) => { if (event.target === elements.placeDialog) closeDialog(); });
    elements.dialogContent.addEventListener('click', handleDialogClick);
    elements.tweaksToggle.addEventListener('click', () => toggleTweaks(true));
    elements.tweaksClose.addEventListener('click', () => toggleTweaks(false));
    elements.densitySelect.addEventListener('change', () => applyTweaks(elements.densitySelect.value, elements.photoSelect.value));
    elements.photoSelect.addEventListener('change', () => applyTweaks(elements.densitySelect.value, elements.photoSelect.value));
    window.addEventListener('keydown', (event) => { if (event.key === 'Escape' && elements.tweaksPanel.classList.contains('open')) toggleTweaks(false); });
  }

  function handleHeroSearch(event) {
    event.preventDefault();
    const value = elements.heroSearchInput.value.trim();
    if (!value) {
      elements.searchHelper.textContent = '先输入一个场景、区域或地点。';
      elements.heroSearchInput.focus();
      return;
    }
    state.query = value;
    elements.filterSearch.value = value;
    state.visibleLimit = pageSize;
    renderPlaces();
    elements.searchHelper.textContent = `正在查看“${value}”的匹配结果`;
    const targetTop = document.getElementById('discover').offsetTop - 78;
    window.scrollTo({ top: targetTop, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }

  function handleSceneClick(event) {
    const button = event.target.closest('.scene-button');
    if (!button) return;
    state.scene = button.dataset.scene;
    state.visibleLimit = pageSize;
    elements.sceneRail.querySelectorAll('.scene-button').forEach((item) => item.classList.toggle('active', item === button));
    elements.sceneDescription.textContent = sceneCopy[state.scene];
    renderPlaces();
  }

  function handleFilterChip(event) {
    const chip = event.target.closest('.filter-chip');
    if (!chip) return;
    const row = chip.closest('[data-filter]');
    const filter = row.dataset.filter;
    state.filters[filter] = chip.dataset.value;
    row.querySelectorAll('.filter-chip').forEach((item) => item.classList.toggle('active', item === chip));
    state.visibleLimit = pageSize;
    renderPlaces();
  }

  function toggleFavoriteFilter() {
    state.favoritesOnly = !state.favoritesOnly;
    elements.favoriteFilter.classList.toggle('active', state.favoritesOnly);
    elements.favoriteFilter.setAttribute('aria-pressed', String(state.favoritesOnly));
    elements.navFavorite.classList.toggle('active', state.favoritesOnly);
    state.visibleLimit = pageSize;
    renderPlaces();
  }

  function showFavorites() {
    if (!state.favoritesOnly) toggleFavoriteFilter();
    closeMobileMenu();
    const targetTop = document.getElementById('discover').offsetTop - 78;
    window.scrollTo({ top: targetTop, behavior: 'smooth' });
  }

  function handlePlaceGridClick(event) {
    const favorite = event.target.closest('[data-action="favorite"]');
    if (favorite) {
      event.stopPropagation();
      toggleFavorite(Number(favorite.dataset.placeId));
      return;
    }
    const card = event.target.closest('[data-place-id]');
    if (card) openPlace(Number(card.dataset.placeId));
  }

  function handlePlaceGridKeydown(event) {
    if (!['Enter', ' '].includes(event.key) || event.target.closest('button')) return;
    const card = event.target.closest('[data-place-id]');
    if (card) { event.preventDefault(); openPlace(Number(card.dataset.placeId)); }
  }

  function openFromDataset(event) {
    const target = event.target.closest('[data-place-id]');
    if (target) openPlace(Number(target.dataset.placeId));
  }

  function toggleFavorite(placeId) {
    const place = state.spots.find((item) => Number(item.id) === placeId);
    if (!place) return;
    if (state.favorites.has(placeId)) {
      state.favorites.delete(placeId);
      showToast(`已取消收藏：${place.name}`);
    } else {
      state.favorites.add(placeId);
      showToast(`已收藏：${place.name}`);
    }
    saveFavorites();
    updateFavoriteCount();
    renderPlaces();
    if (state.activePlaceId === placeId && elements.placeDialog.open) renderDialog(place);
  }

  function updateFavoriteCount() {
    elements.favoriteCount.textContent = String(state.favorites.size);
  }

  function matchesScene(place) {
    if (state.scene === 'indoor') return Boolean(place.indoor);
    if (state.scene === 'free') return Boolean(place.free);
    if (state.scene === 'toddler') return Number(place.age_min ?? 0) <= 3 && Number(place.age_max ?? 12) >= 3;
    if (state.scene === 'outdoor') return !place.indoor;
    if (state.scene === 'niche') return Boolean(place.niche);
    return true;
  }

  function matchesAge(place) {
    if (state.filters.age === 'all') return true;
    const [min, max] = state.filters.age.split('-').map(Number);
    return Number(place.age_min ?? 0) <= max && Number(place.age_max ?? 12) >= min;
  }

  function matchesPrice(place) {
    const priceFilter = state.filters.price;
    if (priceFilter === 'all') return true;
    if (priceFilter === 'free') return Boolean(place.free);
    return Number(place.price || 0) <= Number(priceFilter);
  }

  function searchHaystack(place) {
    return normalize([place.name, place.description, place.district, place.address, ...(place.tags || [])].join(' '));
  }

  function recommendationScore(place) {
    const rankPoints = place.hot ? Math.max(0, 12 - Number(place.hot.rank)) * 10 : 0;
    const seasonPoints = (place.seasons || []).includes(currentSeason()) ? 14 : 0;
    const activityPoints = (place.events || []).length * 3 + (place.deals || []).length * 4;
    return rankPoints + Number(place.rating || 0) * 10 + seasonPoints + activityPoints + place.socialMentions * 2;
  }

  function getFilteredSpots() {
    const query = normalize(state.query);
    const items = state.spots.filter((place) => {
      if (!matchesScene(place) || !matchesAge(place) || !matchesPrice(place)) return false;
      if (state.filters.category !== 'all' && place.category !== state.filters.category) return false;
      if (state.filters.district !== 'all' && place.district !== state.filters.district) return false;
      if (state.favoritesOnly && !state.favorites.has(Number(place.id))) return false;
      return !query || searchHaystack(place).includes(query);
    });

    return items.sort((a, b) => {
      if (state.sort === 'rating') return Number(b.rating || 0) - Number(a.rating || 0);
      if (state.sort === 'price') return Number(a.price || 0) - Number(b.price || 0) || Number(b.rating || 0) - Number(a.rating || 0);
      return recommendationScore(b) - recommendationScore(a);
    });
  }

  function renderPlaces() {
    state.filtered = getFilteredSpots();
    const visible = state.filtered.slice(0, state.visibleLimit);
    elements.resultSummary.textContent = state.favoritesOnly
      ? `收藏中找到 ${state.filtered.length} 个去处`
      : `找到 ${state.filtered.length} 个去处`;
    elements.searchHelper.textContent = state.query ? `当前关键词：${state.query}` : `${state.spots.length} 个本地场所，图片均保存在项目中`;
    elements.placeGrid.innerHTML = visible.map((place, index) => placeCard(place, index)).join('');
    attachImageFallbacks(elements.placeGrid);
    elements.emptyState.classList.toggle('hidden', state.filtered.length !== 0);
    elements.loadMore.parentElement.classList.toggle('hidden', state.filtered.length === 0 || state.visibleLimit >= state.filtered.length);
  }

  function placeCard(place, index) {
    const isFavorite = state.favorites.has(Number(place.id));
    const priceLabel = place.free ? '免费' : Number(place.price || 0) > 0 ? `¥${Number(place.price)}` : '价格待核实';
    const indoorLabel = place.indoor ? '室内' : '户外';
    const badge = place.niche ? '<span class="rating-badge niche">小众宝藏</span>' : `<span class="rating-badge">${Number(place.rating || 0).toFixed(1)} / 5</span>`;
    const galleryCount = placeGallery(place).length;
    const galleryBadge = galleryCount > 1 ? `<span class="gallery-count-badge">${galleryCount} 张实景</span>` : '';
    const delay = Math.min(index, 8) * 45;
    return `
      <article class="place-card" data-place-id="${Number(place.id)}" tabindex="0" role="button" aria-label="查看${escapeHtml(place.name)}详情" style="animation-delay:${delay}ms">
        <div class="place-image">
          <img src="${escapeHtml(place.image)}" data-fallback="images/media/wuhan-skyline.jpg" loading="lazy" decoding="async" alt="${escapeHtml(place.name)}">
          <button class="favorite-button ${isFavorite ? 'active' : ''}" data-action="favorite" data-place-id="${Number(place.id)}" type="button" aria-label="${isFavorite ? '取消收藏' : '收藏'}${escapeHtml(place.name)}" aria-pressed="${isFavorite}">${icon('heart')}</button>
          ${badge}
          ${galleryBadge}
        </div>
        <div class="place-card-body">
          <div class="place-meta"><span>${escapeHtml(place.district)}</span><span>${escapeHtml(categoryLabels[place.category] || place.category)}</span></div>
          <h3>${escapeHtml(place.name)}</h3>
          <p class="place-card-description">${escapeHtml(safeText(place.description, '详细介绍待补充'))}</p>
          <div class="place-facts">
            <span class="fact-chip">${icon(place.indoor ? 'building' : 'trees')}${indoorLabel}</span>
            <span class="fact-chip">${icon('ticket')}${priceLabel}</span>
            <span class="fact-chip">${icon('stroller')}${Number(place.age_min ?? 0)}–${Number(place.age_max ?? 12)} 岁</span>
          </div>
        </div>
      </article>`;
  }

  function attachImageFallbacks(scope) {
    scope.querySelectorAll('img[data-fallback]').forEach((image) => {
      image.addEventListener('error', () => {
        if (image.src.endsWith(image.dataset.fallback)) return;
        image.src = image.dataset.fallback;
      }, { once: true });
    });
  }

  function renderStatus() {
    const updateDate = parseDate(state.data.update.last_update);
    const staleDays = daysBetween(updateDate);
    const dataCopy = staleDays === null ? '更新时间待确认' : staleDays <= 2 ? '数据保持更新' : `数据已 ${staleDays} 天未刷新`;
    const dateLabel = formatDate(today, { month: 'long', day: 'numeric', weekday: 'long' });
    elements.heroDate.textContent = `武汉 · ${dateLabel}`;
    elements.dataStatus.innerHTML = [
      ['01', `今天 · ${dateLabel}`, '按本地日期生成推荐'],
      ['02', `最近数据：${formatDate(updateDate, { year: 'numeric', month: 'long', day: 'numeric' })}`, safeText(state.data.update.data_version, '版本待确认') === '待确认' ? '版本待确认' : `数据版本 ${state.data.update.data_version}`],
      ['03', dataCopy, '票价、预约和活动档期出发前核实']
    ].map(([index, title, note]) => `<div class="status-item"><span class="status-index">${index}</span><span><strong>${escapeHtml(title)}</strong><small>${escapeHtml(note)}</small></span></div>`).join('');
    elements.footerUpdate.textContent = `最近更新：${formatDate(updateDate, { year: 'numeric', month: 'long', day: 'numeric' })}`;
  }

  function placeImage(place) {
    return place.image;
  }

  function placeGallery(place) {
    const images = [place.image, ...(Array.isArray(place.gallery) ? place.gallery : [])]
      .filter((image) => typeof image === 'string' && /^images\//.test(image));
    return [...new Set(images)].slice(0, 5);
  }

  function imageSource(place, image) {
    return state.data.media.find((item) => Number(item.place_id) === Number(place.id) && item.image === image);
  }

  function galleryMarkup(place) {
    const gallery = placeGallery(place);
    if (gallery.length <= 1) return '';
    return `<div class="dialog-gallery" role="group" aria-label="${escapeHtml(place.name)}实景图">
      ${gallery.map((image, index) => `<button class="dialog-thumb ${index === 0 ? 'active' : ''}" type="button" data-gallery-image="${escapeHtml(image)}" aria-label="查看第 ${index + 1} 张实景图" aria-pressed="${index === 0}"><img src="${escapeHtml(image)}" data-fallback="${escapeHtml(place.image)}" loading="lazy" decoding="async" alt=""></button>`).join('')}
    </div>`;
  }

  function renderHot() {
    const hotPlaces = state.data.hot
      .map((hot) => ({ hot, place: state.spots.find((spot) => Number(spot.id) === Number(hot.place_id)) }))
      .filter((item) => item.place);
    const fallback = state.spots.slice().sort((a, b) => recommendationScore(b) - recommendationScore(a)).slice(0, 6).map((place, index) => ({ hot: { rank: index + 1, reason: '评分与季节综合推荐' }, place }));
    const items = hotPlaces.length ? hotPlaces : fallback;
    const feature = items[0];
    if (!feature) return;
    elements.hotFeature.dataset.placeId = String(feature.place.id);
    elements.hotFeature.innerHTML = `
      <img src="${escapeHtml(placeImage(feature.place))}" data-fallback="${escapeHtml(feature.place.image)}" alt="${escapeHtml(feature.place.name)}">
      <div class="hot-feature-content"><div class="hot-badges"><span class="image-badge">热选第 ${Number(feature.hot.rank || 1)} 名</span><span class="image-badge">${escapeHtml(feature.place.district)}</span><span class="image-badge">${feature.place.indoor ? '室内' : '户外'}</span></div><h3>${escapeHtml(feature.place.name)}</h3><p>${escapeHtml(feature.hot.reason || feature.place.description)}</p></div>`;
    elements.hotRanking.innerHTML = items.slice(1, 6).map(({ hot, place }, index) => `
      <div class="rank-item" data-place-id="${Number(place.id)}" role="button" tabindex="0">
        <span class="rank-no">${String(index + 2).padStart(2, '0')}</span><span class="rank-copy"><strong>${escapeHtml(place.name)}</strong><small>${escapeHtml(hot.reason || place.district)}</small></span>${icon('arrow-up-right')}
      </div>`).join('');
    attachImageFallbacks(elements.hotFeature);
    elements.hotRanking.querySelectorAll('[data-place-id]').forEach((item) => item.addEventListener('keydown', (event) => { if (['Enter', ' '].includes(event.key)) { event.preventDefault(); openPlace(Number(item.dataset.placeId)); } }));
  }

  function renderDistricts() {
    const counts = new Map();
    state.spots.forEach((place) => counts.set(place.district, (counts.get(place.district) || 0) + 1));
    const districts = [...counts.entries()].sort((a, b) => b[1] - a[1]);
    elements.districtFilters.innerHTML = `<button class="filter-chip active" data-value="all" type="button">全部</button>` +
      districts.map(([district]) => `<button class="filter-chip" data-value="${escapeHtml(district)}" type="button">${escapeHtml(district.replace('区', ''))}</button>`).join('');
  }

  function renderDeals() {
    const validDeals = state.data.promotions.filter((deal) => {
      const end = parseDate(deal.end_date);
      return !end || end.getTime() + 86400000 > today.getTime();
    }).slice(0, 6);

    if (!validDeals.length) {
      elements.dealGrid.innerHTML = `<div class="error-panel"><h3>暂无仍在有效期内的优惠</h3><p>新的活动需要核验后才会显示。</p></div>`;
      return;
    }

    elements.dealGrid.innerHTML = validDeals.map((deal, index) => {
      const place = state.spots.find((item) => Number(item.id) === Number(deal.place_id));
      const price = Number(deal.price || 0);
      return `<article class="deal-card" ${place ? `data-place-id="${Number(place.id)}" role="button" tabindex="0"` : ''}>
        <div class="deal-card-head"><span class="deal-number">${String(index + 1).padStart(2, '0')} / Offer</span><span class="verify-badge">需复核</span></div>
        <h3>${escapeHtml(deal.title)}</h3><p>${escapeHtml(safeText(deal.desc, deal.location))}</p>
        <div class="deal-card-footer"><span>${escapeHtml(deal.location || '地点待确认')}</span><strong>${price > 0 ? `¥${price}` : '价格以官方为准'}</strong></div>
      </article>`;
    }).join('');
    elements.dealGrid.querySelectorAll('[data-place-id]').forEach((item) => item.addEventListener('keydown', (event) => { if (['Enter', ' '].includes(event.key)) { event.preventDefault(); openPlace(Number(item.dataset.placeId)); } }));
  }

  function renderSocial() {
    const items = state.data.social.items
      .filter((item) => {
        const expires = parseDate(item.expires_at);
        return !expires || expires.getTime() > today.getTime();
      })
      .sort((a, b) => (parseDate(b.published_at)?.getTime() || 0) - (parseDate(a.published_at)?.getTime() || 0))
      .slice(0, 6);

    const health = state.data.social.source_health || {};
    const connector = health.connectors?.xiaohongshu;
    elements.pipelineStatus.innerHTML = `
      <div class="pipeline-item"><span class="pipeline-dot"></span><span>公开来源：${health.status === 'healthy' ? '上次检查正常' : '状态待确认'}</span></div>
      <div class="pipeline-item"><span class="pipeline-dot"></span><span>授权导入：${connector?.status === 'connected' ? '连接器已配置' : '本地连接器待配置'}</span></div>
      <div class="pipeline-item muted"><span class="pipeline-dot"></span><span>待审核：${Number(health.pending_review || 0)} 条</span></div>`;

    if (!items.length) {
      elements.socialList.innerHTML = `<div class="social-card"><div class="social-platform">00</div><div class="social-copy"><h3>暂无仍在时效范围内的社交内容</h3><p>新的授权导出内容经人工核验后才会显示。</p></div></div>`;
      return;
    }

    elements.socialList.innerHTML = items.map((item) => `
      <article class="social-card">
        <span class="social-platform">${escapeHtml(platformMarks[item.platform] || 'WEB')}</span>
        <div class="social-copy"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(safeText(item.summary, '摘要待补充'))}</p><div class="social-meta"><span>${escapeHtml(platformLabels[item.platform] || item.platform)}</span><span>${escapeHtml(item.author || '作者未标注')}</span><span>${escapeHtml(relativeDate(item.published_at))}</span>${daysBetween(parseDate(item.published_at)) > 7 ? '<span>历史参考</span>' : '<span>近期内容</span>'}</div></div>
        <a class="social-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer" aria-label="查看原内容">${icon('external')}</a>
      </article>`).join('');
  }

  function openPlace(placeId) {
    const place = state.spots.find((item) => Number(item.id) === Number(placeId));
    if (!place) return;
    state.activePlaceId = Number(place.id);
    renderDialog(place);
    if (!elements.placeDialog.open) elements.placeDialog.showModal();
    document.body.classList.add('dialog-open');
  }

  function renderDialog(place) {
    const isFavorite = state.favorites.has(Number(place.id));
    const mapQuery = encodeURIComponent(`${place.name} ${place.address || ''}`);
    const mapUrl = `https://uri.amap.com/search?keyword=${mapQuery}&city=武汉&callnative=1`;
    const tags = (place.tags || []).slice(0, 8).map((tag) => `<span class="dialog-tag">${escapeHtml(tag)}</span>`).join('');
    const price = place.free ? '免费开放' : Number(place.price || 0) > 0 ? `参考 ¥${Number(place.price)}` : '价格待核实';
    const sourceUrl = /^https?:\/\//.test(place.source_url || '') ? place.source_url : '';
    const primarySource = imageSource(place, place.image);
    const imageSourceUrl = /^https?:\/\//.test(primarySource?.source_url || '') ? primarySource.source_url : '';
    const imageCredit = primarySource?.credit || primarySource?.author || place.image_credit || '';
    const sourceBlock = sourceUrl || imageSourceUrl ? `<div class="dialog-research">
      ${place.travel_note ? `<p><strong>出行提醒：</strong>${escapeHtml(place.travel_note)}</p>` : ''}
      ${imageCredit ? `<p><strong>主图：</strong>${escapeHtml(imageCredit)}</p>` : ''}
      ${imageSourceUrl ? `<a class="dialog-source" href="${escapeHtml(imageSourceUrl)}" target="_blank" rel="noopener noreferrer">${icon('external')}查看图片来源</a>` : ''}
      ${sourceUrl && sourceUrl !== imageSourceUrl ? `<a class="dialog-source" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">${icon('external')}查看${escapeHtml(place.source || '资料来源')}</a>` : ''}
      ${place.verified_at ? `<p>资料核验：${escapeHtml(place.verified_at)}</p>` : ''}
    </div>` : '';
    elements.dialogContent.innerHTML = `
      <div class="dialog-hero"><img class="dialog-main-image" src="${escapeHtml(placeImage(place))}" data-fallback="${escapeHtml(place.image)}" alt="${escapeHtml(place.name)}实景"><div class="dialog-title-block"><span>${escapeHtml(place.district)} · ${escapeHtml(categoryLabels[place.category] || place.category)}</span><h2 id="dialog-title">${escapeHtml(place.name)}</h2></div></div>
      ${galleryMarkup(place)}
      <div class="dialog-body">
        <div><p class="dialog-description">${escapeHtml(safeText(place.description, '详细介绍待补充'))}</p><div class="dialog-tags">${tags}</div>${sourceBlock}</div>
        <aside><div class="detail-list">
          ${detailRow('clock', '开放时间', safeText(place.hours))}
          ${detailRow('map-pin', '地址', safeText(place.address))}
          ${detailRow('train', '公共交通', safeText(place.transport))}
          ${detailRow('parking', '停车', safeText(place.parking))}
          ${detailRow('ticket', '价格', `${price} · 出发前核实`)}
          ${detailRow('stroller', '适合年龄', `${Number(place.age_min ?? 0)}–${Number(place.age_max ?? 12)} 岁`)}
        </div><div class="dialog-actions"><a href="${mapUrl}" target="_blank" rel="noopener noreferrer">${icon('map-pin')}地图导航</a><button type="button" data-dialog-favorite="${Number(place.id)}" aria-pressed="${isFavorite}">${icon('heart')}${isFavorite ? '取消收藏' : '收藏去处'}</button></div></aside>
      </div>`;
    attachImageFallbacks(elements.dialogContent);
  }

  function detailRow(iconName, label, value) {
    return `<div class="detail-row">${icon(iconName)}<span><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></span></div>`;
  }

  function handleDialogClick(event) {
    const thumbnail = event.target.closest('[data-gallery-image]');
    if (thumbnail) {
      const mainImage = elements.dialogContent.querySelector('.dialog-main-image');
      if (mainImage) mainImage.src = thumbnail.dataset.galleryImage;
      elements.dialogContent.querySelectorAll('[data-gallery-image]').forEach((item) => {
        const isActive = item === thumbnail;
        item.classList.toggle('active', isActive);
        item.setAttribute('aria-pressed', String(isActive));
      });
      return;
    }
    const button = event.target.closest('[data-dialog-favorite]');
    if (button) toggleFavorite(Number(button.dataset.dialogFavorite));
  }

  function closeDialog() {
    if (elements.placeDialog.open) elements.placeDialog.close();
    document.body.classList.remove('dialog-open');
    state.activePlaceId = null;
  }

  function resetFilters() {
    state.query = '';
    state.scene = 'weekend';
    state.filters = { age: 'all', category: 'all', district: 'all', price: 'all' };
    state.sort = 'recommended';
    state.favoritesOnly = false;
    state.visibleLimit = pageSize;
    elements.filterSearch.value = '';
    elements.heroSearchInput.value = '';
    elements.sortSelect.value = 'recommended';
    elements.favoriteFilter.classList.remove('active');
    elements.favoriteFilter.setAttribute('aria-pressed', 'false');
    elements.navFavorite.classList.remove('active');
    elements.sceneRail.querySelectorAll('.scene-button').forEach((item) => item.classList.toggle('active', item.dataset.scene === 'weekend'));
    elements.filterGroups.querySelectorAll('[data-filter]').forEach((row) => row.querySelectorAll('.filter-chip').forEach((chip) => chip.classList.toggle('active', chip.dataset.value === 'all')));
    elements.sceneDescription.textContent = sceneCopy.weekend;
    renderPlaces();
  }

  function toggleFilterDrawer() {
    const open = !elements.filterGroups.classList.contains('open');
    elements.filterGroups.classList.toggle('open', open);
    elements.filterDrawerButton.setAttribute('aria-expanded', String(open));
  }

  function toggleMobileMenu() {
    const open = !elements.mobileMenu.classList.contains('open');
    elements.mobileMenu.classList.toggle('open', open);
    elements.mobileMenuButton.setAttribute('aria-expanded', String(open));
    elements.mobileMenuButton.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
    document.body.classList.toggle('menu-open', open);
  }

  function closeMobileMenu() {
    elements.mobileMenu.classList.remove('open');
    elements.mobileMenuButton.setAttribute('aria-expanded', 'false');
    elements.mobileMenuButton.setAttribute('aria-label', '打开导航');
    document.body.classList.remove('menu-open');
  }

  function toggleTweaks(open) {
    elements.tweaksPanel.classList.toggle('open', open);
    elements.tweaksToggle.setAttribute('aria-expanded', String(open));
  }

  function applyTweaks(density, photo, persist = true) {
    document.body.classList.toggle('density-compact', density === 'compact');
    document.body.classList.toggle('photo-warm', photo === 'warm');
    document.body.classList.toggle('photo-quiet', photo === 'quiet');
    if (elements.densitySelect) elements.densitySelect.value = density;
    if (elements.photoSelect) elements.photoSelect.value = photo;
    if (persist) saveTweaks();
  }

  function showToast(message) {
    clearTimeout(state.toastTimer);
    elements.toast.textContent = message;
    elements.toast.classList.add('show');
    state.toastTimer = setTimeout(() => elements.toast.classList.remove('show'), 2200);
  }

  function showLoadingCards() {
    elements.placeGrid.innerHTML = Array.from({ length: 6 }, () => '<div class="skeleton-card" aria-hidden="true"></div>').join('');
  }

  function showFatalError(error) {
    console.error(error);
    elements.placeGrid.innerHTML = `<div class="error-panel"><h3>场所数据暂时没有加载成功</h3><p>${escapeHtml(error.message || '请检查本地 JSON 文件。')}</p><button type="button" id="retry-load">${icon('refresh')}重新加载</button></div>`;
    document.getElementById('retry-load')?.addEventListener('click', () => window.location.reload());
    elements.resultSummary.textContent = '数据加载失败';
    elements.loadingScreen.classList.add('is-hidden');
  }

  async function init() {
    cacheElements();
    loadPreferences();
    bindEvents();
    updateFavoriteCount();
    showLoadingCards();
    try {
      state.data = await window.WeekendDataService.loadAll();
      enrichData(state.data);
      renderDistricts();
      renderStatus();
      renderHot();
      renderPlaces();
      renderDeals();
      renderSocial();
      elements.loadingScreen.classList.add('is-hidden');
    } catch (error) {
      showFatalError(error);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
}());
