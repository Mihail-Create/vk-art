/* ============================================================
   DHA'T'ELLE — PIXEL MINI APP SCRIPT (V2)
   35+ Altar Prophecies, Equipment Categories, Free Item Names,
   Dual Currency (Ядра 🔮 & РНД 🪙), Multi-lot Builder & Storefronts
   ============================================================ */

// --- 8-BIT RETRO AUDIO SYNTHESIZER ---
let soundEnabled = true;
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
  return audioCtx;
}

function playRetroSound(type) {
  if (!soundEnabled) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;

    if (type === 'click') {
      osc.type = 'square';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.05);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === 'tab') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(587, now);
      osc.frequency.setValueAtTime(880, now + 0.04);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    } else if (type === 'success') {
      osc.type = 'square';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.08);
      osc.frequency.setValueAtTime(783.99, now + 0.16);
      osc.frequency.setValueAtTime(1046.50, now + 0.24);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.start(now);
      osc.stop(now + 0.4);
    } else if (type === 'dark') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(130, now);
      osc.frequency.exponentialRampToValueAtTime(55, now + 0.45);
      gain.gain.setValueAtTime(0.16, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc.start(now);
      osc.stop(now + 0.5);
    }
  } catch (err) {}
}

// Sound toggle
document.getElementById('sound-toggle')?.addEventListener('click', () => {
  soundEnabled = !soundEnabled;
  const icon = document.getElementById('sound-icon');
  if (icon) {
    icon.textContent = soundEnabled ? '🔊' : '🔇';
  }
  showToast(soundEnabled ? 'Звук включён' : 'Звук выключен', '🔔');
  if (soundEnabled) playRetroSound('click');
});

// --- TAB NAVIGATION ---
function switchTab(tabId) {
  if (tabId === 'tab-admin' && !isUserAdmin(currentUserId)) {
    playRetroSound('click');
    showToast('Доступ запрещен: только для Администратора!', '⛔');
    return;
  }
  playRetroSound('tab');
  
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === tabId);
  });

  if (tabId === 'tab-admin') {
    renderAdminPanel();
  }

  const content = document.querySelector('.app-content');
  if (content) content.scrollTop = 0;
}

// --- FORM: RACE, GENDER, STYLE, MOOD TOGGLES ---
function initChoiceButtons() {
  document.querySelectorAll('.pixel-choice-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      playRetroSound('click');
      const groupName = btn.dataset.name;
      document.querySelectorAll(`.pixel-choice-btn[data-name="${groupName}"]`).forEach(sibling => {
        sibling.classList.remove('active');
      });
      btn.classList.add('active');
    });
  });
}

function updateCharCount() {
  const textarea = document.getElementById('order-desc');
  const counter = document.getElementById('desc-counter');
  const hint = document.getElementById('desc-hint');
  if (!textarea || !counter) return;

  const len = textarea.value.trim().length;
  counter.textContent = `${len} / 1000`;

  if (len < 50) {
    counter.style.color = '#ff4455';
    if (hint) hint.textContent = `Осталось ещё минимум ${50 - len} симв.`;
  } else {
    counter.style.color = '#3cd070';
    if (hint) hint.textContent = 'Отличная детализация для художника!';
  }
}

let refCount = 0;
function toggleRefStatus() {
  playRetroSound('click');
  refCount = (refCount + 1) % 4;
  const btnText = document.getElementById('ref-status-text');
  if (btnText) {
    btnText.textContent = refCount === 0 ? 'В ЛС бота (0)' : `Прикреплю в ЛС (${refCount})`;
  }
  showToast(`Количество референсов: ${refCount}`, '🖼');
}

function submitArtOrder() {
  const descInput = document.getElementById('order-desc');
  const desc = descInput ? descInput.value.trim() : '';

  if (desc.length < 50) {
    playRetroSound('click');
    showToast('Минимум 50 символов в описании!', '⚠️');
    descInput?.focus();
    return;
  }

  const race = document.querySelector('.pixel-choice-btn[data-name="race"].active')?.dataset.val || 'Человек';
  const gender = document.querySelector('.pixel-choice-btn[data-name="gender"].active')?.dataset.val || 'Мужской';
  const style = document.querySelector('.pixel-choice-btn[data-name="style"].active')?.dataset.val || 'Аниме';
  const mood = document.querySelector('.pixel-choice-btn[data-name="mood"].active')?.dataset.val || 'Мрачное/Дарк';

  playRetroSound('success');

  const shortId = Math.random().toString(16).substring(2, 10);
  const fullOrderId = `ord_${shortId}`;

  const orderMsg = `🎨 ЗАКАЗ НА АРТ ИЗ ПРИЛОЖЕНИЯ DHA'T'ELLE\n` +
    `🔖 Номер заказа: ${fullOrderId}\n` +
    `👤 Заказчик: @id${currentUserId} (${currentUserName})\n` +
    `⚔️ Раса: ${race} | Пол: ${gender}\n` +
    `🎭 Стиль: ${style} | Настроение: ${mood}\n` +
    `🖼 Референсы: ${refCount} шт.\n` +
    `📝 Описание персонажа:\n${desc}`;

  saveUserOrderRecord({
    order_id: fullOrderId,
    race,
    gender,
    style,
    mood,
    description: desc,
    references_count: refCount,
    status: 'waiting',
    date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  const botDmUrl = `https://vk.com/im?sel=-241412610&message=` + encodeURIComponent(orderMsg);

  showToast('Заказ сформирован! Переходим в диалог с ботом...', '🎨');

  setTimeout(() => {
    window.open(botDmUrl, '_blank');
  }, 1000);

  if (descInput) descInput.value = '';
  updateCharCount();
  refCount = 0;
  const btnText = document.getElementById('ref-status-text');
  if (btnText) btnText.textContent = 'В ЛС бота (0)';
}

function loadUserOrders() {
  try {
    const saved = localStorage.getItem('dhatelle_user_orders');
    if (saved) return JSON.parse(saved);
  } catch (e) {}
  return [];
}

function saveUserOrderRecord(order) {
  const list = loadUserOrders();
  list.unshift(order);
  try {
    localStorage.setItem('dhatelle_user_orders', JSON.stringify(list));
  } catch (e) {}
  renderUserOrders();
}

function removeUserOrder(orderId) {
  playRetroSound('click');
  let orders = loadUserOrders();
  orders = orders.filter(o => o.order_id !== orderId);
  try {
    localStorage.setItem('dhatelle_user_orders', JSON.stringify(orders));
  } catch (e) {}
  renderUserOrders();
  showToast(`Заказ #${orderId} удален из истории.`, '🗑️');
}

function clearAllUserOrders() {
  playRetroSound('click');
  if (confirm('Очистить всю историю ваших заказов артов?')) {
    try {
      localStorage.removeItem('dhatelle_user_orders');
    } catch (e) {}
    renderUserOrders();
    showToast('История заказов очищена.', '🗑️');
  }
}

function renderUserOrders() {
  const container = document.getElementById('user-orders-list');
  const countElem = document.getElementById('user-orders-count');
  const clearBtn = document.getElementById('clear-orders-btn');
  const orders = loadUserOrders();
  if (countElem) countElem.textContent = orders.length;
  if (clearBtn) {
    if (orders.length > 0) clearBtn.classList.remove('hidden');
    else clearBtn.classList.add('hidden');
  }
  if (!container) return;

  if (orders.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 12px; color: var(--text-dim); font-size: 10px;">
        У вас пока нет активных заказов. Заполните форму выше и отправьте заявку!
      </div>
    `;
    return;
  }

  container.innerHTML = orders.map(ord => `
    <div class="store-row-card">
      <div class="store-row-info">
        <b class="store-row-nick">🎨 Заказ #${escapeHtml(ord.order_id)} (${escapeHtml(ord.style)} / ${escapeHtml(ord.race)})</b>
        <span class="store-row-time">Создан: ${escapeHtml(ord.date)} • Референсов: ${ord.references_count || 0} шт.</span>
      </div>
      <div style="display: flex; gap: 6px; align-items: center;">
        <span class="pixel-badge gold-badge" style="font-size:7px;">В ОЧЕРЕДИ</span>
        <button type="button" class="pixel-btn sm-btn reject-btn" onclick="removeUserOrder('${escapeHtml(ord.order_id)}')" title="Удалить этот заказ из истории" style="padding: 2px 6px; font-size: 8px;">✕</button>
      </div>
    </div>
  `).join('');
}

// ============================================================
// MARKETPLACE & STOREFRONTS (РЫНОК С ПРЕДМЕТАМИ И ЛАВКАМИ)
// ============================================================

// Категории:
// weapon (Оружие), shield (Щиты), head (Голова), body (Тело),
// pants (Штанишки), legs (Ноги), mod (Моды), limit (Коллекционки), misc (Разное)

function loadMarketItems() {
  try {
    const saved = localStorage.getItem('dhatelle_market_items');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return [];
}

function saveMarketItems() {
  try {
    localStorage.setItem('dhatelle_market_items', JSON.stringify(marketItems));
  } catch (e) {}
}

let marketItems = loadMarketItems();

let activeCategoryFilter = 'all';
let currentStoreSeller = null; // null = общий рынок, string = фильтр лавки конкретного продавца

const categoryLabels = {
  'weapon': '⚔️ Оружие',
  'shield': '🛡️ Щиты',
  'head': '🧢 Голова',
  'body': '🥋 Тело',
  'pants': '👖 Штанишки',
  'legs': '🦿 Ноги',
  'mod': '⚙️ Моды',
  'limit': '🏆 Коллекционка',
  'misc': '📦 Разное'
};

function renderMarketList() {
  const container = document.getElementById('market-list');
  const searchInput = document.getElementById('market-search');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  if (!container) return;

  const filtered = marketItems.filter(item => {
    const matchesCategory = (activeCategoryFilter === 'all') || (item.category === activeCategoryFilter);
    const matchesQuery = (item.title || '').toLowerCase().includes(query) || 
                         (item.seller || '').toLowerCase().includes(query) || 
                         (item.priceCores && item.priceCores.toLowerCase().includes(query)) ||
                         (item.priceRnd && item.priceRnd.toLowerCase().includes(query));
    return matchesCategory && matchesQuery;
  });

  // Приоритетная сортировка:
  // 1. Лоты продавцов с оплаченной активной лавкой (VIP) идут на самом верху!
  // 2. Лоты обычных продавцов без лавки идут внизу.
  // 3. Внутри категории более новые лоты сверху.
  filtered.sort((a, b) => {
    const aSub = hasStorefrontSubscription(a.sellerContact || a.seller);
    const bSub = hasStorefrontSubscription(b.sellerContact || b.seller);
    if (aSub && !bSub) return -1;
    if (!aSub && bSub) return 1;
    return (b.id || 0) - (a.id || 0);
  });

  updateMyLotsCount();

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 36px 10px; color: var(--text-dim); font-size: 11px; line-height: 1.6;">
        📦 На рынке пока нет активных лотов.<br>
        Нажмите <b style="color: var(--crimson-primary)">«+ Выставить предметы на рынок»</b>, чтобы предложить снаряжение!
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => renderItemCard(item, false)).join('');
}

function renderItemCard(item, isInsideStorefront = false) {
  const catName = categoryLabels[item.category] || '📦 Предмет';

  // Проверяем подписку на лавку у продавца
  const hasSub = hasStorefrontSubscription(item.sellerContact || item.seller);

  // Форматирование двойной цены
  let pricesHtml = '';
  if (item.priceCores) {
    pricesHtml += `<span class="lot-price price-cores">${escapeHtml(item.priceCores)}</span>`;
  }
  if (item.priceRnd) {
    pricesHtml += `<span class="lot-price price-rnd">${escapeHtml(item.priceRnd)}</span>`;
  }
  if (!pricesHtml) {
    pricesHtml = `<span class="lot-price">Договорная</span>`;
  }

  // Кнопка перехода в витрину лавки: ТОЛЬКО для продавцов с активной лавкой!
  const storeActionBtn = (isInsideStorefront || !hasSub)
    ? ''
    : `<button class="pixel-btn sm-btn store-btn" onclick="openStorefront('${escapeHtml(item.seller)}', '${escapeHtml(item.sellerContact || '')}', '${escapeHtml(item.guild || '')}')">🏪 В лавку</button>`;

  // Бейдж лавки (VIP)
  const vipBadge = hasSub
    ? `<span class="pixel-badge vip-store-badge">🔥 В ЛАВКЕ</span>`
    : '';

  const isOwner = (item.seller === currentUserName || 
                   item.sellerContact === `@${currentUserName}` || 
                   item.sellerContact === `@id${currentUserId}` || 
                   (currentUserId === 208825850 && item.seller === 'geek_mann'));

  const deleteBtn = isOwner
    ? `<button class="pixel-btn sm-btn reject-btn" onclick="removeMarketItem(${item.id})">✕ Снять</button>`
    : '';

  return `
    <div class="market-card ${hasSub ? 'vip-market-card' : ''}">
      <div class="lot-header-row">
        <div class="lot-title-box">
          <span class="item-cat-badge">${catName}</span>
          ${vipBadge}
          <span class="lot-title">${escapeHtml(item.title)}</span>
        </div>
      </div>

      <div class="lot-bottom-row">
        <div class="seller-info-box">
          <span>Продавец:</span>
          <span class="lot-seller">${escapeHtml(item.seller)}</span>
          <span class="dot-sep">•</span>
          <span class="lot-date">${escapeHtml(item.date)}</span>
        </div>

        <div class="lot-right">
          <div class="prices-stack">
            ${pricesHtml}
          </div>
          <div class="lot-actions">
            ${storeActionBtn}
            ${deleteBtn}
            <button class="pixel-btn sm-btn primary-btn" onclick="contactSeller('${escapeHtml(item.title)}', '${escapeHtml(item.seller)}', '${escapeHtml(item.sellerContact || '')}')">
              Купить
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function removeMarketItem(itemId) {
  playRetroSound('click');
  marketItems = marketItems.filter(item => item.id !== itemId);
  saveMarketItems();
  renderMarketList();
  if (currentStoreSeller) {
    const sellerItems = marketItems.filter(item => item.seller.toLowerCase() === currentStoreSeller.toLowerCase());
    const countElem = document.getElementById('store-items-count');
    if (countElem) countElem.textContent = sellerItems.length;
    const storeList = document.getElementById('storefront-list');
    if (storeList) {
      if (sellerItems.length === 0) {
        storeList.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--text-dim); font-size: 11px;">В этой лавке пока нет активных товаров.</div>`;
      } else {
        storeList.innerHTML = sellerItems.map(item => renderItemCard(item, true)).join('');
      }
    }
  }
  showToast('Предмет снят с продажи.', '🗑️');
}

function setCategoryFilter(category) {
  playRetroSound('click');
  activeCategoryFilter = category;

  document.querySelectorAll('#category-filters .pill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.cat === category);
  });

  renderMarketList();
}

function filterMarketItems() {
  renderMarketList();
}

function contactSeller(itemTitle, seller, contact) {
  playRetroSound('click');
  const target = contact || seller;
  
  let clean = target.replace('@', '').trim();
  let dmUrl = `https://vk.com/im?sel=${clean}`;
  if (/^\d+$/.test(clean)) {
    dmUrl = `https://vk.com/im?sel=${clean}`;
  } else if (clean.startsWith('id') && /^\d+$/.test(clean.slice(2))) {
    dmUrl = `https://vk.com/im?sel=${clean.slice(2)}`;
  } else {
    dmUrl = `https://vk.com/${clean}`;
  }

  showToast(`Открываем диалог с продавцом ${seller}...`, '💬');
  window.open(dmUrl, '_blank');
}

// ============================================================
// STOREFRONTS (ПЕРСОНАЛЬНЫЕ ТОРГОВЫЕ ЛАВКИ)
// ============================================================

function openStorefront(sellerName, sellerContact, sellerGuild) {
  playRetroSound('tab');
  currentStoreSeller = sellerName;

  const mainView = document.getElementById('market-main-view');
  const storeView = document.getElementById('market-storefront-view');

  const nameElem = document.getElementById('store-seller-name');
  const contactElem = document.getElementById('store-seller-contact');
  const guildElem = document.getElementById('store-seller-guild');

  if (nameElem) nameElem.textContent = `Лавка игрока ${sellerName}`;
  if (contactElem) contactElem.textContent = sellerContact || sellerName;
  if (guildElem) guildElem.textContent = sellerGuild ? `Гильдия: ${sellerGuild}` : 'Гильдия: Dha’t’elle';

  const sellerItems = marketItems.filter(item => item.seller.toLowerCase() === sellerName.toLowerCase());
  const countElem = document.getElementById('store-items-count');
  if (countElem) countElem.textContent = sellerItems.length;

  const storeList = document.getElementById('storefront-list');
  if (storeList) {
    if (sellerItems.length === 0) {
      storeList.innerHTML = `
        <div style="text-align: center; padding: 30px; color: var(--text-dim); font-size: 11px;">
          В этой лавке пока нет активных товаров.
        </div>
      `;
    } else {
      storeList.innerHTML = sellerItems.map(item => renderItemCard(item, true)).join('');
    }
  }

  mainView?.classList.add('hidden');
  storeView?.classList.remove('hidden');

  const content = document.querySelector('.app-content');
  if (content) content.scrollTop = 0;
}

function closeStorefront() {
  playRetroSound('click');
  currentStoreSeller = null;

  document.getElementById('market-storefront-view')?.classList.add('hidden');
  document.getElementById('market-main-view')?.classList.remove('hidden');
}

function openMyStorefront() {
  const currentNick = document.getElementById('player-nick')?.textContent || currentUserName;
  if (!isCurrentUserSubscribed()) {
    playRetroSound('click');
    openRentStoreModal();
    return;
  }
  openStorefront(currentNick, `@id${currentUserId}`, 'Dha’t’elle');
}

function updateMyLotsCount() {
  const currentNick = (document.getElementById('player-nick')?.textContent || currentUserName).toLowerCase();
  const count = marketItems.filter(i => (i.seller || '').toLowerCase() === currentNick).length;
  const countElem = document.getElementById('my-lots-count');
  if (countElem) countElem.textContent = count;
  updateMarketStoreActionButton();
}

function updateMarketStoreActionButton() {
  const container = document.getElementById('market-store-action-box');
  if (!container) return;

  const isSubscribed = isCurrentUserSubscribed();
  const currentNick = (document.getElementById('player-nick')?.textContent || currentUserName).toLowerCase();
  const count = marketItems.filter(i => (i.seller || '').toLowerCase() === currentNick).length;

  if (isSubscribed) {
    container.innerHTML = `
      <button type="button" class="pixel-btn my-store-btn" onclick="openMyStorefront()" title="Открыть мою персональную лавку">
        🏪 МОЯ ЛАВКА (<span id="my-lots-count">${count}</span>)
      </button>
    `;
  } else {
    container.innerHTML = `
      <button type="button" class="pixel-btn sm-btn tariff-btn" onclick="openRentStoreModal()" title="Аренда торговой лавки">
        🔥 Аренда лавки
      </button>
    `;
  }
}

// ============================================================
// MULTI-LOT CREATION MODAL (ДОБАВЛЕНИЕ СРАЗУ НЕСКОЛЬКИХ ЛОТОВ)
// ============================================================

let lotBuilderRows = [];

function openCreateLotModal() {
  playRetroSound('click');
  const container = document.getElementById('lots-builder-list');
  if (container) {
    container.innerHTML = ''; // Обязательно очищаем старые карточки!
  }
  lotBuilderRows = [];
  addLotRow(); // Добавляем первую чистую строку по умолчанию
  document.getElementById('lot-modal')?.classList.remove('hidden');
}

function closeCreateLotModal() {
  playRetroSound('click');
  document.getElementById('lot-modal')?.classList.add('hidden');
}

function addLotRow() {
  playRetroSound('click');
  const container = document.getElementById('lots-builder-list');
  if (!container) return;

  const rowId = Date.now() + Math.floor(Math.random() * 1000);
  lotBuilderRows.push(rowId);

  const cardHtml = `
    <div class="lot-builder-card" id="row-${rowId}">
      <div class="builder-header">
        <span class="card-num-badge">ПРЕДМЕТ #${lotBuilderRows.length}</span>
        <button type="button" class="remove-row-btn" onclick="removeLotRow(${rowId})">✕</button>
      </div>

      <div class="form-group" style="margin-bottom: 6px;">
        <label class="pixel-label">КАТЕГОРИЯ</label>
        <select class="pixel-select row-cat" style="padding: 6px 8px; font-size: 11px;">
          <option value="weapon">⚔️ Оружие</option>
          <option value="shield">🛡️ Щит</option>
          <option value="head">🧢 Голова</option>
          <option value="body">🥋 Тело / Доспех</option>
          <option value="pants">👖 Штанишки</option>
          <option value="legs">🦿 Ноги / Ботинки</option>
          <option value="mod">⚙️ Модификация / Имплант</option>
          <option value="limit">🏆 Коллекционка (Лимитка)</option>
          <option value="misc">📦 Разное</option>
        </select>
      </div>

      <div class="form-group" style="margin-bottom: 6px;">
        <label class="pixel-label">НАЗВАНИЕ И ХАРАКТЕРИСТИКИ (СВОБОДНЫЙ ВВОД / СКОПИРУЙТЕ ИЗ ИГРЫ)</label>
        <input type="text" class="pixel-input row-title" placeholder="Напр: Катана разящая солнце +15 [🗡 240-452 🌀 80]...">
      </div>

      <div class="pixel-grid grid-2" style="margin-bottom: 4px;">
        <div class="form-group" style="margin-bottom: 0;">
          <label class="pixel-label">ЦЕНА В ЯДРАХ 🔮</label>
          <input type="text" class="pixel-input row-cores" placeholder="Напр: 45,000">
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label class="pixel-label">ЦЕНА В РНД 🪙 (ОПЦИОНАЛЬНО)</label>
          <input type="text" class="pixel-input row-rnd" placeholder="Напр: 200 RND">
        </div>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', cardHtml);
  refreshLotRowsControls();
}

function removeLotRow(rowId) {
  playRetroSound('click');
  lotBuilderRows = lotBuilderRows.filter(id => id !== rowId);
  const elem = document.getElementById(`row-${rowId}`);
  if (elem) elem.remove();

  if (lotBuilderRows.length === 0) {
    addLotRow();
    return;
  }

  refreshLotRowsControls();
}

function refreshLotRowsControls() {
  const cards = document.querySelectorAll('#lots-builder-list .lot-builder-card');
  const total = cards.length;

  cards.forEach((card, idx) => {
    const badge = card.querySelector('.card-num-badge');
    if (badge) badge.textContent = `ПРЕДМЕТ #${idx + 1}`;

    let header = card.querySelector('.builder-header');
    let btn = card.querySelector('.remove-row-btn');
    const rowId = card.id ? card.id.replace('row-', '') : '';

    if (total > 1) {
      if (!btn && header) {
        header.insertAdjacentHTML('beforeend', `<button type="button" class="remove-row-btn" onclick="removeLotRow(${rowId})">✕</button>`);
      } else if (btn) {
        btn.style.display = '';
      }
    } else {
      if (btn) btn.style.display = 'none';
    }
  });
}

function publishAllLots() {
  const sellerContact = document.getElementById('seller-global-contact')?.value.trim() || currentUserName;
  const rows = document.querySelectorAll('#lots-builder-list .lot-builder-card');

  if (rows.length === 0) {
    showToast('Добавьте хотя бы один предмет!', '⚠️');
    return;
  }

  let addedCount = 0;

  rows.forEach(row => {
    const titleInput = row.querySelector('.row-title');
    const catSelect = row.querySelector('.row-cat');
    const coresInput = row.querySelector('.row-cores');
    const rndInput = row.querySelector('.row-rnd');

    const title = titleInput ? titleInput.value.trim() : '';
    const category = catSelect ? catSelect.value : 'misc';
    let cores = coresInput ? coresInput.value.trim() : '';
    let rnd = rndInput ? rndInput.value.trim() : '';

    if (!title) return; // Пропускаем пустые

    if (cores && !cores.includes('🔮')) cores = cores + ' 🔮';
    if (rnd && !rnd.includes('🪙')) rnd = rnd + ' 🪙';

    if (!cores && !rnd) {
      cores = 'Договорная 🔮';
    }

    const newLot = {
      id: Date.now() + Math.floor(Math.random() * 10000) + addedCount,
      category: category,
      title: title,
      priceCores: cores,
      priceRnd: rnd,
      seller: currentUserName,
      sellerContact: sellerContact.startsWith('@') ? sellerContact : `@${sellerContact}`,
      guild: 'Dha’t’elle',
      date: 'Только что'
    };

    marketItems.unshift(newLot);
    addedCount++;
  });

  if (addedCount === 0) {
    showToast('Заполните название предметов!', '⚠️');
    return;
  }

  saveMarketItems();
  playRetroSound('success');
  renderMarketList();

  const container = document.getElementById('lots-builder-list');
  if (container) container.innerHTML = '';
  lotBuilderRows = [];
  closeCreateLotModal();

  showToast(`Опубликовано предметов: ${addedCount}!`, '✨');
}

// ============================================================
// STORE SUBSCRIPTIONS & TOR PAYMENT VERIFICATION
// ============================================================

const DEFAULT_ADMIN_SETTINGS = {
  coresPrice: 27000,
  rndPrice: 1000,
  rentDays: 30,
  recipientName: 'Ярость всегда рядом',
  recipientId: 208825850
};

function loadAdminSettings() {
  try {
    const saved = localStorage.getItem('dhatelle_admin_settings');
    if (saved) {
      return { ...DEFAULT_ADMIN_SETTINGS, ...JSON.parse(saved) };
    }
  } catch (e) {}
  return { ...DEFAULT_ADMIN_SETTINGS };
}

function saveAdminSettings() {
  const coresInput = document.getElementById('cfg-cores-price');
  const rndInput = document.getElementById('cfg-rnd-price');
  const daysInput = document.getElementById('cfg-rent-days');

  const settings = {
    coresPrice: coresInput ? parseInt(coresInput.value, 10) || 27000 : 27000,
    rndPrice: rndInput ? parseInt(rndInput.value, 10) || 1000 : 1000,
    rentDays: daysInput ? parseInt(daysInput.value, 10) || 30 : 30,
    recipientName: 'Ярость всегда рядом',
    recipientId: 208825850
  };

  try {
    localStorage.setItem('dhatelle_admin_settings', JSON.stringify(settings));
    playRetroSound('success');
    showToast('Настройки тарифов аренды сохранены!', '💾');
  } catch (e) {
    showToast('Ошибка сохранения настроек', '⚠️');
  }
}

function loadSubscriptions() {
  try {
    const saved = localStorage.getItem('dhatelle_store_subscriptions');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return [];
}

function saveSubscriptions(subs) {
  try {
    localStorage.setItem('dhatelle_store_subscriptions', JSON.stringify(subs));
  } catch (e) {}
}

function hasStorefrontSubscription(sellerIdentity) {
  if (!sellerIdentity) return false;
  const str = String(sellerIdentity).toLowerCase().replace('@', '').trim();

  // geek_mann (208825850) / Ярость всегда рядом — создатель и супер-админ, лавка активна бессрочно
  if (str === '208825850' || str === 'id208825850' || str === 'geek_mann' || str === 'ярость всегда рядом' || str === 'тразир') {
    return true;
  }

  const subs = loadSubscriptions();
  const now = Date.now();

  return subs.some(sub => {
    if (sub.expiresAt && sub.expiresAt < now) return false;
    const subUid = String(sub.userId || '').toLowerCase();
    const subNick = String(sub.userNick || '').toLowerCase().replace('@', '');
    return str === subUid || str === `id${subUid}` || str === subNick;
  });
}

function isCurrentUserSubscribed() {
  return hasStorefrontSubscription(currentUserId) || hasStorefrontSubscription(currentUserName);
}

function openRentStoreModal() {
  playRetroSound('click');
  const settings = loadAdminSettings();

  const daysLabel = document.getElementById('rent-days-label');
  const coresVal = document.getElementById('rent-cores-val');
  const rndVal = document.getElementById('rent-rnd-val');
  const recipLabel = document.getElementById('rent-recipient-label');
  const input = document.getElementById('rent-log-input');

  if (daysLabel) daysLabel.textContent = settings.rentDays;
  if (coresVal) coresVal.textContent = settings.coresPrice.toLocaleString();
  if (rndVal) rndVal.textContent = settings.rndPrice.toLocaleString();
  if (recipLabel) recipLabel.textContent = settings.recipientName;
  if (input) input.value = '';

  document.getElementById('rent-store-modal')?.classList.remove('hidden');
}

function closeRentStoreModal() {
  playRetroSound('click');
  document.getElementById('rent-store-modal')?.classList.add('hidden');
}

function loadUsedLogs() {
  try {
    const saved = localStorage.getItem('dhatelle_used_tor_logs');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return [];
}

function saveUsedLog(logKey) {
  try {
    const list = loadUsedLogs();
    if (!list.includes(logKey)) {
      list.push(logKey);
      localStorage.setItem('dhatelle_used_tor_logs', JSON.stringify(list));
    }
  } catch (e) {}
}

function parseToRTransferLog(rawText) {
  if (!rawText || typeof rawText !== 'string') {
    return { ok: false, error: 'Вставьте текст сообщения о переводе из ToR!' };
  }

  const text = rawText.trim();
  const transferRegex = /(?:✅\s*)?Вы успешно передали\s+([\d\s,.]+)\s*(ядер|ядра|ядро|rnd|рнд)\s+игроку\s+([^.\r\n]+)/i;
  const match = text.match(transferRegex);

  if (!match) {
    return {
      ok: false,
      error: 'Не найден лог передачи ToR! Формат: "Вы успешно передали 27000 ядер игроку Ярость всегда рядом."'
    };
  }

  const rawAmountStr = match[1].replace(/[\s,.]+/g, '');
  const amount = parseInt(rawAmountStr, 10);
  if (isNaN(amount) || amount <= 0) {
    return { ok: false, error: 'Не удалось определить сумму передачи.' };
  }

  const rawCurrency = match[2].toLowerCase();
  const currencyType = (rawCurrency.includes('rnd') || rawCurrency.includes('рнд')) ? 'rnd' : 'cores';
  const recipient = match[3].trim();

  return {
    ok: true,
    amount,
    currencyType,
    recipient,
    rawMatch: match[0]
  };
}

function submitRentPaymentLog() {
  const input = document.getElementById('rent-log-input');
  const rawText = input ? input.value.trim() : '';

  if (!rawText) {
    playRetroSound('click');
    showToast('Вставьте скопированный лог передачи ToR!', '⚠️');
    return;
  }

  const parsed = parseToRTransferLog(rawText);
  if (!parsed.ok) {
    playRetroSound('click');
    showToast(parsed.error, '⚠️');
    return;
  }

  const settings = loadAdminSettings();

  // 1. Проверка получателя: должен быть Ярость всегда рядом / geek_mann / 208825850 / cfg.recipientName
  const cleanRecipient = parsed.recipient.toLowerCase();
  const validRecipients = [
    '208825850',
    'id208825850',
    'geek_mann',
    'ярость всегда рядом',
    'тразир',
    (settings.recipientName || '').toLowerCase().trim()
  ].filter(Boolean);

  const isRecipientValid = validRecipients.some(vr => cleanRecipient.includes(vr));
  if (!isRecipientValid) {
    playRetroSound('click');
    showToast(`Ошибка: перевод должен быть адресован ${settings.recipientName} (id208825850)!`, '⛔');
    return;
  }

  // 2. Проверка достаточной суммы
  const requiredAmount = parsed.currencyType === 'rnd' ? settings.rndPrice : settings.coresPrice;
  if (parsed.amount < requiredAmount) {
    const currName = parsed.currencyType === 'rnd' ? 'RND 🪙' : 'ядер 🔮';
    playRetroSound('click');
    showToast(`Недостаточно: передано ${parsed.amount} ${currName}, требуется ${requiredAmount} ${currName}!`, '⚠️');
    return;
  }

  // 3. Защита от повторного использования лога (Anti-Replay)
  const balanceMatch = rawText.match(/(?:Ваш баланс|баланс):\s*([\d\s,.]+)/i);
  const balancePart = balanceMatch ? balanceMatch[1].replace(/\s+/g, '') : '';
  const logKey = `${parsed.currencyType}_${parsed.amount}_${cleanRecipient}_${balancePart || parsed.rawMatch}`.toLowerCase();

  const usedLogs = loadUsedLogs();
  if (usedLogs.includes(logKey)) {
    playRetroSound('click');
    showToast('Этот лог перевода уже был использован ранее!', '⛔');
    return;
  }

  // 4. Успешная активация подписки на лавку
  saveUsedLog(logKey);

  const durationMs = settings.rentDays * 24 * 60 * 60 * 1000;
  const subs = loadSubscriptions();
  const existingSubIndex = subs.findIndex(s => 
    String(s.userId) === String(currentUserId) || 
    (s.userNick && s.userNick.toLowerCase() === currentUserName.toLowerCase())
  );

  let newExpiresAt = Date.now() + durationMs;
  if (existingSubIndex >= 0 && subs[existingSubIndex].expiresAt > Date.now()) {
    newExpiresAt = subs[existingSubIndex].expiresAt + durationMs;
    subs[existingSubIndex].expiresAt = newExpiresAt;
    subs[existingSubIndex].lastPayment = Date.now();
  } else if (existingSubIndex >= 0) {
    subs[existingSubIndex].expiresAt = newExpiresAt;
    subs[existingSubIndex].lastPayment = Date.now();
  } else {
    subs.push({
      userId: currentUserId,
      userNick: currentUserName,
      expiresAt: newExpiresAt,
      lastPayment: Date.now(),
      grantedBy: 'payment_log',
      amount: parsed.amount,
      currency: parsed.currencyType
    });
  }

  saveSubscriptions(subs);
  playRetroSound('success');
  closeRentStoreModal();
  renderMarketList();

  const daysWord = `${settings.rentDays} дн.`;
  showToast(`Торговая лавка активирована на ${daysWord}! VIP-статус получен 🏪`, '✨');
}

// ============================================================
// ADMIN PANEL (УПРАВЛЕНИЕ ПРИЛОЖЕНИЕМ И ДОСТУПОМ)
// ============================================================

const SUPER_ADMIN_ID = 208825850; // geek_mann (Вы / Создатель)

function loadAdminUsers() {
  try {
    const saved = localStorage.getItem('dhatelle_admin_users');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return [SUPER_ADMIN_ID];
}

function saveAdminUsers(users) {
  try {
    if (!users.includes(SUPER_ADMIN_ID)) users.unshift(SUPER_ADMIN_ID);
    localStorage.setItem('dhatelle_admin_users', JSON.stringify(users));
  } catch (e) {}
}

async function syncRemoteAdminConfig() {
  try {
    const res = await fetch('admin_config.json?t=' + Date.now());
    if (res.ok) {
      const config = await res.json();
      if (config && Array.isArray(config.adminIds)) {
        const localAdmins = loadAdminUsers();
        let changed = false;
        config.adminIds.forEach(id => {
          const numId = Number(id);
          if (!localAdmins.some(a => Number(a) === numId || String(a) === String(id))) {
            localAdmins.push(numId || id);
            changed = true;
          }
        });
        if (changed) {
          saveAdminUsers(localAdmins);
          checkAdminAccess();
        }
      }
    }
  } catch (e) {}
}

function isUserAdmin(userId) {
  const uid = Number(userId);
  if (uid === SUPER_ADMIN_ID) return true;
  if (typeof VOS_USER_IDS !== 'undefined' && VOS_USER_IDS.includes(uid)) return true;
  const list = loadAdminUsers();
  return list.some(item => Number(item) === uid || String(item).toLowerCase() === String(userId).toLowerCase());
}

function checkAdminAccess() {
  const navBtn = document.getElementById('nav-admin');
  const adminSection = document.getElementById('tab-admin');
  const isAdmin = isUserAdmin(currentUserId);

  if (isAdmin) {
    if (navBtn) navBtn.classList.remove('hidden');
    if (adminSection) adminSection.style.display = '';
  } else {
    if (navBtn) navBtn.classList.add('hidden');
    if (adminSection) adminSection.style.display = 'none';
    const activeNav = document.querySelector('.nav-btn.active');
    if (activeNav && activeNav.id === 'nav-admin') {
      switchTab('tab-market');
    }
  }
}

function renderAdminPanel() {
  if (!isUserAdmin(currentUserId)) return;

  // 1. Тарифы
  const settings = loadAdminSettings();
  const coresInput = document.getElementById('cfg-cores-price');
  const rndInput = document.getElementById('cfg-rnd-price');
  const daysInput = document.getElementById('cfg-rent-days');

  if (coresInput) coresInput.value = settings.coresPrice;
  if (rndInput) rndInput.value = settings.rndPrice;
  if (daysInput) daysInput.value = settings.rentDays;

  // 2. Список администраторов
  const adminList = loadAdminUsers();
  const adminsContainer = document.getElementById('admins-list-container');
  if (adminsContainer) {
    adminsContainer.innerHTML = adminList.map(adm => {
      const isRoot = Number(adm) === SUPER_ADMIN_ID;
      const removeBtn = isRoot
        ? `<span class="pixel-badge gold-badge" style="font-size:7px;">ROOT</span>`
        : `<button type="button" class="remove-admin-btn" onclick="removeAdminUser('${adm}')">✕</button>`;
      return `
        <div class="admin-user-pill">
          <span class="admin-user-name">${isRoot ? '👑 ' : '👤 '}${escapeHtml(String(adm))}</span>
          ${removeBtn}
        </div>
      `;
    }).join('');
  }

  // 3. Активные лавки игроков
  const subs = loadSubscriptions();
  const now = Date.now();
  const activeSubs = subs.filter(s => s.expiresAt > now);

  const countElem = document.getElementById('active-stores-count');
  if (countElem) countElem.textContent = activeSubs.length + 1; // +1 geek_mann (бессрочно)

  const storesContainer = document.getElementById('active-stores-list');
  if (storesContainer) {
    let html = `
      <div class="store-row-card vip-permanent">
        <div class="store-row-info">
          <b class="store-row-nick">👑 geek_mann / Ярость всегда рядом (id208825850)</b>
          <span class="store-row-time">Статус: Бессрочно (Создатель)</span>
        </div>
        <span class="pixel-badge gold-badge">SUPER ROOT</span>
      </div>
    `;

    if (activeSubs.length === 0) {
      html += `
        <div style="text-align: center; padding: 14px; color: var(--text-dim); font-size: 10px;">
          Нет других арендованных лавок на данный момент.
        </div>
      `;
    } else {
      html += activeSubs.map(s => {
        const remainingDays = Math.max(1, Math.ceil((s.expiresAt - now) / (1000 * 60 * 60 * 24)));
        const targetId = s.userId || s.userNick;
        return `
          <div class="store-row-card">
            <div class="store-row-info">
              <b class="store-row-nick">🏪 ${escapeHtml(s.userNick || 'Игрок')} (id${s.userId || '?'})</b>
              <span class="store-row-time">Осталось: ${remainingDays} дн. (до ${new Date(s.expiresAt).toLocaleDateString()})</span>
            </div>
            <button type="button" class="pixel-btn sm-btn reject-btn" onclick="revokeStorefront('${escapeHtml(String(targetId))}')">
              ✕ Отозвать
            </button>
          </div>
        `;
      }).join('');
    }

    storesContainer.innerHTML = html;
  }

  // 4. Модерация знамений Алтаря Бездны
  renderProposals();
  updateProposalsBadge();
}

function addAdminUser() {
  const input = document.getElementById('new-admin-input');
  let raw = input ? input.value.trim() : '';

  if (!raw) {
    showToast('Введите ID или ссылку VK!', '⚠️');
    return;
  }

  let clean = raw.replace(/^https?:\/\//i, '').replace(/^vk\.com\//i, '').replace(/^@/, '').trim();
  if (clean.toLowerCase().startsWith('id') && /^\d+$/.test(clean.slice(2))) {
    clean = clean.slice(2);
  }

  const list = loadAdminUsers();
  if (list.includes(clean) || (Number(clean) && list.includes(Number(clean)))) {
    showToast('Этот пользователь уже является администратором!', 'ℹ️');
    return;
  }

  const finalVal = (/^\d+$/.test(clean)) ? Number(clean) : clean;
  list.push(finalVal);
  saveAdminUsers(list);

  if (input) input.value = '';
  playRetroSound('success');
  renderAdminPanel();
  showToast(`Администратор ${clean} успешно добавлен!`, '👑');
}

function removeAdminUser(target) {
  if (Number(target) === SUPER_ADMIN_ID || String(target) === String(SUPER_ADMIN_ID)) {
    showToast('Нельзя удалить главного администратора!', '⛔');
    return;
  }

  let list = loadAdminUsers();
  list = list.filter(item => String(item) !== String(target));
  saveAdminUsers(list);

  playRetroSound('click');
  renderAdminPanel();
  showToast(`Администратор ${target} удален.`, '🗑️');
}

function grantManualStorefront() {
  const userInput = document.getElementById('manual-store-user');
  let target = userInput ? userInput.value.trim() : '';

  if (!target) {
    showToast('Укажите ник или ID игрока!', '⚠️');
    return;
  }

  const settings = loadAdminSettings();
  let clean = target.replace(/^@/, '').trim();
  const isNumeric = /^\d+$/.test(clean);

  const durationMs = settings.rentDays * 24 * 60 * 60 * 1000;
  const subs = loadSubscriptions();

  const idx = subs.findIndex(s => 
    (isNumeric && Number(s.userId) === Number(clean)) || 
    (s.userNick && s.userNick.toLowerCase() === clean.toLowerCase())
  );

  const newExpiresAt = Date.now() + durationMs;
  if (idx >= 0) {
    subs[idx].expiresAt = (subs[idx].expiresAt > Date.now() ? subs[idx].expiresAt : Date.now()) + durationMs;
  } else {
    subs.push({
      userId: isNumeric ? Number(clean) : 0,
      userNick: clean,
      expiresAt: newExpiresAt,
      lastPayment: Date.now(),
      grantedBy: 'manual_admin'
    });
  }

  saveSubscriptions(subs);
  if (userInput) userInput.value = '';

  playRetroSound('success');
  renderAdminPanel();
  renderMarketList();
  showToast(`Лавка для ${clean} успешно активирована на ${settings.rentDays} дн.!`, '👑');
}

function revokeStorefront(target) {
  playRetroSound('click');
  let subs = loadSubscriptions();
  const clean = String(target).toLowerCase().replace('@', '');

  subs = subs.filter(s => {
    const sUid = String(s.userId || '').toLowerCase();
    const sNick = String(s.userNick || '').toLowerCase();
    return sUid !== clean && sNick !== clean;
  });

  saveSubscriptions(subs);
  renderAdminPanel();
  renderMarketList();
  updateMarketStoreActionButton();
  showToast(`Лавка игрока ${target} отозвана.`, '🗑️');
}

async function syncSubscriptionsNow() {
  playRetroSound('click');
  showToast('Синхронизация подписок с сервером...', '⏳');
  await syncRemoteSubscriptions();
  renderAdminPanel();
  renderMarketList();
  updateMarketStoreActionButton();
  showToast('Лавки успешно синхронизированы!', '✅');
}

function cleanExpiredSubscriptions() {
  playRetroSound('click');
  const subs = loadSubscriptions();
  const now = Date.now();
  const initialCount = subs.length;
  const activeSubs = subs.filter(s => s.expiresAt > now || Number(s.userId) === SUPER_ADMIN_ID);
  saveSubscriptions(activeSubs);
  renderAdminPanel();
  renderMarketList();
  updateMarketStoreActionButton();
  const removed = initialCount - activeSubs.length;
  showToast(`Очищено просроченных лавок: ${removed}`, '🧹');
}

function exportFullDataBackup() {
  playRetroSound('click');
  const backup = {
    exportDate: new Date().toISOString(),
    version: '2.3',
    marketItems: loadMarketItems(),
    subscriptions: loadSubscriptions(),
    adminSettings: loadAdminSettings(),
    adminUsers: loadAdminUsers()
  };
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(backup, null, 2));
  const a = document.createElement('a');
  a.setAttribute('href', dataStr);
  a.setAttribute('download', `dhatelle_backup_${Date.now()}.json`);
  document.body.appendChild(a);
  a.click();
  a.remove();
  showToast('Резервная копия (JSON) скачана!', '💾');
}

function triggerImportBackup() {
  playRetroSound('click');
  const input = document.getElementById('backup-file-input');
  if (input) input.click();
}

function handleBackupFile(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const data = JSON.parse(e.target.result);
      if (Array.isArray(data.marketItems)) {
        localStorage.setItem('dhatelle_market_items', JSON.stringify(data.marketItems));
        marketItems = data.marketItems;
      }
      if (Array.isArray(data.subscriptions)) {
        saveSubscriptions(data.subscriptions);
      }
      if (data.adminSettings) {
        localStorage.setItem('dhatelle_admin_settings', JSON.stringify(data.adminSettings));
      }
      if (Array.isArray(data.adminUsers)) {
        saveAdminUsers(data.adminUsers);
      }
      playRetroSound('success');
      renderAdminPanel();
      renderMarketList();
      updateMarketStoreActionButton();
      showToast('База успешно восстановлена из бэкапа!', '✅');
    } catch (err) {
      showToast('Ошибка чтения файла бэкапа (неверный JSON)', '⚠️');
    }
  };
  reader.readAsText(file);
  event.target.value = '';
}

function clearPendingProposals() {
  playRetroSound('click');
  if (confirm('Очистить все предложенные знамения на модерации?')) {
    localStorage.removeItem('dhatelle_proposals');
    renderProposals();
    showToast('Очередь знамений очищена.', '🔮');
  }
}

function resetUsedLogs() {
  playRetroSound('click');
  try {
    localStorage.removeItem('dhatelle_used_tor_logs');
    showToast('Кэш использованных логов ToR успешно сброшен!', '🔄');
  } catch (e) {}
}

function clearMarketData() {
  playRetroSound('click');
  if (confirm('Вы уверены, что хотите удалить ВСЕ лоты с рынка?')) {
    marketItems = [];
    saveMarketItems();
    renderMarketList();
    updateMarketStoreActionButton();
    showToast('Все лоты с рынка удалены.', '🗑️');
  }
}


// ============================================================
// 35+ ALTAR ORACLE PROPHECIES (ПЕЧЕНЬКИ С ПРЕДСКАЗАНИЯМИ)
// ============================================================

const defaultOracleMessages = [
  '👁 Бездна шепчет: Сегодня заточка на +15 пройдет успешно... но только если не смотреть на экран!',
  '⚔️ Кровавое знамение: На сегодняшнем гильд-боссе твой крит пробьет отметку в 1000%!',
  '🩸 Мудрость Dha’t’elle: Лучше потерять стамину в рейде, чем честь в клан-чате.',
  '🪙 Золотой дождь: В ближайшей вылазке тебя ждет редкий мод на скорость — не отдавай за бесценок!',
  '🐟 Оракул усмехается: Где-то в темноте тихо плачет один Карп, потерявший жилу железа.',
  '🔮 Кристалл пульсирует: Сегодня шанс выбить коллекционку повышен втрое!',
  '🦴 Древний шепот: Усиленные кости торса спасут тебя от фатального удара босса на последних секундах.',
  '🛡️ Завет праотцов: Кто не отбил гильд-босса до созыва — тот чистит обсидиановые залы клана!',
  '⚡ Энергия Бездны: Загляни на Рынок — кто-то по ошибке может выставить топовое оружие за бесценок.',
  '🎯 Пророчество ловкости: Твоя катана найдет слабое место в защите любого рейдового босса.',
  '✨ Рубиновое сияние: Художники Dha’t’elle подготовят для тебя аватар непревзойденной красоты!',
  '🌋 Огненный знак: Добытчики сегодня принесут удвоенную норму чистейшей серы.',
  '💀 Голос бездны: Остерегайся тех, кто просит скидку 90% и обещает отбить босса "завтра".',
  '☕ Совет оракула: Сделай чай с печеньками — РБ уже близко, пора собирать группу!',
  '👑 Великое предзнаменование: Твой вклад в клан оценен Высшим Офицерским Составом.',
  '🗝️ Тайна сундуков: Следующий сундук содержит не ржавый хлам, а концентрат TORия!',
  '🗡️ Звон клинков: Проклекалибур в твоих руках нанесет сокрушительный удар по рейтингу врагов.',
  '🏃 Скорость ветра: Твои ботинки наслаждения болью позволят убежать от любого возмездия.',
  '🔥 Искра ярости: Сегодня в PvP-арене твои победы будут сеять панику среди соперников.',
  '📦 Секрет торговца: Выставь лот в лавку прямо сейчас — покупатель уже ищет этот предмет!',
  '🌑 Темный щит: Ни одно заклинание вражеского мага не пробьет твою защиту Проклещитиуса.',
  '🎲 Счастливый бросок: Удача на твоей стороне, шанс крита максимален!',
  '🧟 Смех предков: "Мы фармили боссов вручную в снегу, а вам теперь даже созыв в ВК присылают!"',
  '💎 Алмазный блеск: Подписка ToR окупается сторицей, когда ты в сильнейшем клане сервера.',
  '🌪️ Вихрь Бездны: Сегодня отличный день, чтобы повысить свой ранг до Лейтенанта!',
  '📜 Запись в скрижалях: Твой ник навечно вписан в летопись величия Dha’t’elle.',
  '🛡️ Благословение танка: Агро босса удержится на тебе крепче, чем обещания сокланов.',
  '🏹 Меткий глаз: Ни один промах не омрачит твой победный раунд.',
  '🍷 Тост Бездны: За верность гильдии, за вовремя отбитых боссов и за жилы железа!',
  '🧙 Архимагический знак: Твой интеллект превзойдет мудрость древних архимагов.',
  '🪐 Сила TORия: Ядра энергии переполняют твой инвентарь — распредели их с умом.',
  '⚔️ Походный гимн: Подними знамя Dha’t’elle — победа уже предопределена судьбой!',
  '🖤 Око Бездны подмигивает: "Ты красавчик, и броня твоя сияет круче солнца."'
];

function loadOracleMessages() {
  try {
    const saved = localStorage.getItem('dhatelle_oracle_messages');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {}
  return [...defaultOracleMessages];
}

function saveOracleMessages() {
  try {
    localStorage.setItem('dhatelle_oracle_messages', JSON.stringify(oracleMessages));
  } catch (e) {}
}

let oracleMessages = loadOracleMessages();

function triggerAltarRitual() {
  playRetroSound('dark');
  const oracleBox = document.getElementById('altar-oracle-message');
  const oracleText = document.getElementById('oracle-text');
  if (!oracleBox || !oracleText) return;

  const randomMsg = oracleMessages[Math.floor(Math.random() * oracleMessages.length)];
  oracleText.textContent = randomMsg;
  oracleBox.classList.remove('hidden');

  showToast('Благословение Бездны получено!', '🔮');
}

// ============================================================
// SUGGESTIONS & PROPOSALS (ПРЕДЛОЖИТЬ СВОЁ ЗНАМЕНИЕ)
// ============================================================

function loadOracleProposals() {
  try {
    const saved = localStorage.getItem('dhatelle_oracle_proposals');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return [];
}

function saveOracleProposals() {
  try {
    localStorage.setItem('dhatelle_oracle_proposals', JSON.stringify(oracleProposals));
  } catch (e) {}
}

let oracleProposals = loadOracleProposals();

function openSuggestModal() {
  playRetroSound('click');
  const modal = document.getElementById('suggest-modal');
  const authorInput = document.getElementById('suggest-author');
  const textInput = document.getElementById('suggest-text');
  
  if (authorInput) {
    const playerNick = document.getElementById('player-nick')?.textContent || 'Бездна всегда рядом';
    authorInput.value = playerNick;
  }
  if (textInput) textInput.value = '';
  modal?.classList.remove('hidden');
}

function closeSuggestModal() {
  playRetroSound('click');
  document.getElementById('suggest-modal')?.classList.add('hidden');
}

function submitOracleProposal() {
  const authorInput = document.getElementById('suggest-author');
  const textInput = document.getElementById('suggest-text');
  const author = authorInput ? authorInput.value.trim() : 'Аноним Бездны';
  const text = textInput ? textInput.value.trim() : '';

  if (!text || text.length < 8) {
    playRetroSound('click');
    showToast('Напишите текст знамения (от 8 символов)!', '⚠️');
    textInput?.focus();
    return;
  }

  playRetroSound('success');

  const newProposal = {
    id: Date.now(),
    author: author || 'Бездна всегда рядом',
    text: text,
    date: 'Только что'
  };

  oracleProposals.unshift(newProposal);
  saveOracleProposals();

  closeSuggestModal();
  renderProposals();
  updateProposalsBadge();

  showToast('Предложение отправлено создателю и ВОС! 📜', '✨');
}

// ============================================================
// OFFICER MODERATION TAB (ВКЛАДКА МОДЕРАЦИИ ДЛЯ ВОС)
// ============================================================

// Высший офицерский состав (ВОС) гильдии Dha't'elle:
// 208825850: geek_mann (Вы / Разработчик)
// 706284129: morohrono (Глава гильдии / Заказчик)
// 31959523: motheroftor (Даша / Гарант)
// 629691481: pain_lolikox (Офицер ВОС)
const VOS_USER_IDS = [208825850, 706284129, 31959523, 629691481];

let currentUserId = 208825850; // geek_mann (Вы / Разработчик по умолчанию)
let currentUserName = 'geek_mann';
let isUserOfficer = true;

function initVkAuth() {
  // 1. Проверяем URL параметры VK (когда приложение запущено в iframe VK)
  const urlParams = new URLSearchParams(window.location.search);
  const vkUserIdFromUrl = urlParams.get('vk_user_id');

  // 2. Инициализация официального VK Bridge SDK
  if (window.vkBridge) {
    try {
      window.vkBridge.send('VKWebAppInit');
    } catch (e) {}

    window.vkBridge.send('VKWebAppGetUserInfo')
      .then(user => {
        if (user && user.id) {
          const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || `Игрок #${user.id}`;
          applyUserIdentity(user.id, fullName);
        }
      })
      .catch(() => {
        if (vkUserIdFromUrl) {
          applyUserIdentity(Number(vkUserIdFromUrl), `Игрок #${vkUserIdFromUrl}`);
        } else {
          fallbackDefaultAuth();
        }
      });
  } else if (vkUserIdFromUrl) {
    applyUserIdentity(Number(vkUserIdFromUrl), `Игрок #${vkUserIdFromUrl}`);
  } else {
    fallbackDefaultAuth();
  }
}

function fallbackDefaultAuth() {
  // Если запуск локальный (localhost), остаёмся в вашем профиле (geek_mann, id: 208825850)
  applyUserIdentity(208825850, 'geek_mann');
}

function applyUserIdentity(userId, userName) {
  currentUserId = Number(userId);
  currentUserName = userName;

  // Жесткая проверка: входит ли ID пользователя в белый список ВОС
  isUserOfficer = VOS_USER_IDS.includes(currentUserId);

  const nickElem = document.getElementById('player-nick');
  const rankBadge = document.querySelector('.clan-name-row .rank-badge');

  if (nickElem) nickElem.textContent = userName;

  if (isUserOfficer) {
    if (rankBadge) {
      rankBadge.textContent = 'ВОС';
      rankBadge.className = 'pixel-badge rank-badge';
    }
  } else {
    if (rankBadge) {
      rankBadge.textContent = 'СОКЛАН';
      rankBadge.className = 'pixel-badge';
    }
  }

  checkOfficerAccess();
  checkAdminAccess();
  updateMarketStoreActionButton();
}

function renderProposals() {
  const container = document.getElementById('proposals-container');
  const countElem = document.getElementById('proposals-count');
  const countBadge = document.getElementById('proposals-count-badge');
  const totalOracleElem = document.getElementById('total-oracle-count');

  if (countElem) countElem.textContent = oracleProposals.length;
  if (countBadge) countBadge.textContent = oracleProposals.length;
  if (totalOracleElem) totalOracleElem.textContent = oracleMessages.length;

  if (!container) return;

  if (oracleProposals.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 24px 12px; color: var(--text-dim); font-size: 11px; line-height: 1.6;">
        ✨ Все предложения рассмотрены!<br>
        Новые варианты знамений от игроков появятся здесь.
      </div>
    `;
    return;
  }

  container.innerHTML = oracleProposals.map(p => `
    <div class="proposal-card" id="proposal-${p.id}">
      <div class="proposal-header">
        <span class="proposal-author">👤 ${escapeHtml(p.author)}</span>
        <span class="proposal-date">${escapeHtml(p.date)}</span>
      </div>
      <div class="proposal-body">
        «${escapeHtml(p.text)}»
      </div>
      <div class="proposal-actions">
        <button type="button" class="pixel-btn accept-btn" onclick="acceptProposal(${p.id})">
          ✅ Принять в Алтарь
        </button>
        <button type="button" class="pixel-btn reject-btn" onclick="rejectProposal(${p.id})">
          ❌ Отклонить
        </button>
      </div>
    </div>
  `).join('');
}

function acceptProposal(propId) {
  playRetroSound('success');
  const found = oracleProposals.find(p => p.id === propId);
  if (!found) return;

  // Добавляем текст знамения в пул предсказаний Алтаря
  if (!oracleMessages.includes(found.text)) {
    oracleMessages.push(found.text);
    saveOracleMessages();
  }

  // Удаляем из списка предложений
  oracleProposals = oracleProposals.filter(p => p.id !== propId);
  saveOracleProposals();

  renderProposals();
  updateProposalsBadge();
  showToast('Знамение принято и добавлено в Алтарь Бездны! 🔮', '✨');
}

function rejectProposal(propId) {
  playRetroSound('click');
  oracleProposals = oracleProposals.filter(p => p.id !== propId);
  saveOracleProposals();

  renderProposals();
  updateProposalsBadge();
  showToast('Предложение отклонено.', '🗑️');
}

function updateProposalsBadge() {
  const badge = document.getElementById('admin-proposals-badge') || document.getElementById('proposals-badge');
  if (!badge) return;
  const count = oracleProposals.length;
  badge.textContent = count;
  const hasAccess = isUserAdmin(currentUserId) || isUserOfficer;
  if (count > 0 && hasAccess) {
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

function checkOfficerAccess() {
  updateProposalsBadge();
}

// ============================================================
// TOAST NOTIFICATIONS & UTILS
// ============================================================

let toastTimeout = null;

function showToast(message, icon = '⚔️') {
  const toast = document.getElementById('pixel-toast');
  const toastMsg = document.getElementById('toast-message');
  const toastIcon = document.getElementById('toast-icon');
  if (!toast) return;

  if (toastMsg) toastMsg.textContent = message;
  if (toastIcon) toastIcon.textContent = icon;

  toast.classList.remove('hidden');

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.add('hidden');
  }, 2800);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  initChoiceButtons();
  renderMarketList();
  updateCharCount();
  initVkAuth();
  renderProposals();
  checkAdminAccess();
  renderUserOrders();
  syncRemoteSubscriptions();
  syncRemoteAdminConfig();
  updateMarketStoreActionButton();
});

async function syncRemoteSubscriptions() {
  try {
    const res = await fetch('store_subscriptions.json?t=' + Date.now());
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        localStorage.setItem('dhatelle_store_subscriptions', JSON.stringify(data));
        renderMarketList();
        updateMarketStoreActionButton();
      }
    }
  } catch (e) {}
}
