/**
 * DHA'T'ELLE MINI APP — PHASE 2 VERIFICATION TEST SUITE
 * Tests:
 * 1. Multi-lot builder fixes (BUG-05, BUG-06, BUG-07)
 * 2. Storefront subscription access & market prioritization
 * 3. ToR payment log parsing & anti-replay verification
 * 4. Admin panel access control, tariff configuration & manual grant/revoke
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

console.log('====================================================');
console.log('🚀 RUNNING MINI APP PHASE 2 VERIFICATION SUITE');
console.log('====================================================\n');

// 1. Mock Browser Environment
const localStorageData = {};
const mockLocalStorage = {
  getItem: (key) => localStorageData[key] || null,
  setItem: (key, val) => { localStorageData[key] = String(val); },
  removeItem: (key) => { delete localStorageData[key]; },
  clear: () => { Object.keys(localStorageData).forEach(k => delete localStorageData[k]); }
};

class MockElement {
  constructor(id = '', tag = 'div') {
    this.id = id;
    this.tagName = tag.toUpperCase();
    this.className = '';
    this.classList = {
      _classes: new Set(),
      add: (...cls) => cls.forEach(c => this.classList._classes.add(c)),
      remove: (...cls) => cls.forEach(c => this.classList._classes.delete(c)),
      toggle: (cls, force) => {
        if (force === undefined) {
          if (this.classList._classes.has(cls)) this.classList._classes.delete(cls);
          else this.classList._classes.add(cls);
        } else if (force) {
          this.classList._classes.add(cls);
        } else {
          this.classList._classes.delete(cls);
        }
      },
      contains: (cls) => this.classList._classes.has(cls)
    };
    this.style = {};
    this.dataset = {};
    this._value = '';
    this._innerHTML = '';
    this._textContent = '';
    this.children = [];
    this.parentNode = null;
  }

  get value() { return this._value; }
  set value(v) { this._value = String(v); }

  get textContent() { return this._textContent || this._innerHTML.replace(/<[^>]*>/g, '').trim(); }
  set textContent(v) { this._textContent = String(v); }

  get innerHTML() { return this._innerHTML; }
  set innerHTML(v) {
    this._innerHTML = String(v);
    this.children = [];
  }

  addEventListener(event, fn) {}
  remove() {
    if (this.parentNode) {
      this.parentNode.children = this.parentNode.children.filter(c => c !== this);
    }
    delete mockElements[this.id];
  }

  insertAdjacentHTML(position, html) {
    this._innerHTML += html;
    
    // Specifically handle lot-builder cards
    const rowMatch = html.match(/id=["']row-(\d+)["']/);
    if (rowMatch) {
      const rowId = rowMatch[1];
      const card = new MockElement(`row-${rowId}`);
      card.classList.add('lot-builder-card');
      card.parentNode = this;

      const header = new MockElement('', 'div');
      header.classList.add('builder-header');
      header.parentNode = card;

      const badge = new MockElement('', 'span');
      badge.classList.add('card-num-badge');
      badge.textContent = `ПРЕДМЕТ #${this.children.length + 1}`;
      badge.parentNode = header;
      header.children.push(badge);

      const removeBtn = new MockElement('', 'button');
      removeBtn.classList.add('remove-row-btn');
      removeBtn.parentNode = header;
      header.children.push(removeBtn);

      const titleInput = new MockElement('', 'input');
      titleInput.classList.add('row-title');
      titleInput.value = 'Катана Солнца +15';
      titleInput.parentNode = card;

      const catSelect = new MockElement('', 'select');
      catSelect.classList.add('row-cat');
      catSelect.value = 'weapon';
      catSelect.parentNode = card;

      const coresInput = new MockElement('', 'input');
      coresInput.classList.add('row-cores');
      coresInput.value = '45000';
      coresInput.parentNode = card;

      const rndInput = new MockElement('', 'input');
      rndInput.classList.add('row-rnd');
      rndInput.value = '200';
      rndInput.parentNode = card;

      card.children = [header, titleInput, catSelect, coresInput, rndInput];
      this.children.push(card);
      mockElements[`row-${rowId}`] = card;
    }
  }

  querySelector(sel) {
    if (sel.startsWith('#')) return mockElements[sel.slice(1)] || null;
    if (sel.startsWith('.')) {
      const cls = sel.slice(1);
      const search = (el) => {
        if (el.classList && el.classList.contains(cls)) return el;
        for (const ch of el.children) {
          const res = search(ch);
          if (res) return res;
        }
        return null;
      };
      return search(this);
    }
    return null;
  }

  querySelectorAll(sel) {
    const res = [];
    const search = (el) => {
      if (sel.startsWith('.')) {
        if (el.classList && el.classList.contains(sel.slice(1))) res.push(el);
      }
      el.children.forEach(search);
    };
    search(this);
    return res;
  }
}

const mockElements = {
  'lots-builder-list': new MockElement('lots-builder-list'),
  'lot-modal': new MockElement('lot-modal'),
  'market-list': new MockElement('market-list'),
  'market-search': new MockElement('market-search'),
  'seller-global-contact': new MockElement('seller-global-contact'),
  'player-nick': new MockElement('player-nick'),
  'my-lots-count': new MockElement('my-lots-count'),
  'rent-store-modal': new MockElement('rent-store-modal'),
  'rent-log-input': new MockElement('rent-log-input'),
  'rent-days-label': new MockElement('rent-days-label'),
  'rent-cores-val': new MockElement('rent-cores-val'),
  'rent-rnd-val': new MockElement('rent-rnd-val'),
  'rent-recipient-label': new MockElement('rent-recipient-label'),
  'tab-admin': new MockElement('tab-admin'),
  'nav-admin': new MockElement('nav-admin'),
  'cfg-cores-price': new MockElement('cfg-cores-price'),
  'cfg-rnd-price': new MockElement('cfg-rnd-price'),
  'cfg-rent-days': new MockElement('cfg-rent-days'),
  'cfg-recipient-name': new MockElement('cfg-recipient-name'),
  'new-admin-input': new MockElement('new-admin-input'),
  'admins-list-container': new MockElement('admins-list-container'),
  'manual-store-user': new MockElement('manual-store-user'),
  'active-stores-list': new MockElement('active-stores-list'),
  'active-stores-count': new MockElement('active-stores-count'),
  'market-store-action-box': new MockElement('market-store-action-box'),
  'user-orders-list': new MockElement('user-orders-list'),
  'user-orders-count': new MockElement('user-orders-count'),
  'clear-orders-btn': new MockElement('clear-orders-btn'),
  'pixel-toast': new MockElement('pixel-toast'),
  'toast-message': new MockElement('toast-message'),
  'toast-icon': new MockElement('toast-icon'),
  'admin-proposals-badge': new MockElement('admin-proposals-badge'),
  'proposals-container': new MockElement('proposals-container'),
  'proposals-count': new MockElement('proposals-count'),
  'proposals-count-badge': new MockElement('proposals-count-badge'),
  'total-oracle-count': new MockElement('total-oracle-count'),
  'suggest-modal': new MockElement('suggest-modal'),
  'suggest-author': new MockElement('suggest-author'),
  'suggest-text': new MockElement('suggest-text'),
  'oracle-text': new MockElement('oracle-text'),
  'altar-btn': new MockElement('altar-btn'),
  'altar-rank-badge': new MockElement('altar-rank-badge'),
  'altar-clicks-count': new MockElement('altar-clicks-count')
};

const context = {
  URLSearchParams: global.URLSearchParams,
  window: {
    location: { search: '' },
    AudioContext: function() {
      return {
        createOscillator: () => ({ connect: () => {}, start: () => {}, stop: () => {}, frequency: { setValueAtTime: () => {}, exponentialRampToValueAtTime: () => {} } }),
        createGain: () => ({ connect: () => {}, gain: { setValueAtTime: () => {}, exponentialRampToValueAtTime: () => {} } }),
        destination: {},
        currentTime: 0
      };
    }
  },
  document: {
    getElementById: (id) => mockElements[id] || null,
    querySelector: (sel) => {
      if (sel.startsWith('#')) return mockElements[sel.slice(1)] || null;
      return new MockElement();
    },
    querySelectorAll: (sel) => {
      if (sel.includes('.lot-builder-card')) {
        return mockElements['lots-builder-list'].children;
      }
      return [];
    },
    addEventListener: () => {}
  },
  localStorage: mockLocalStorage,
  setTimeout: (fn) => fn(),
  clearTimeout: () => {},
  console: console
};

vm.createContext(context);
const appJsCode = fs.readFileSync(path.join(__dirname, 'miniapp', 'app.js'), 'utf-8');
vm.runInContext(appJsCode, context);

function evalIn(expr) {
  return vm.runInContext(expr, context);
}

let passCount = 0;
let failCount = 0;

function assert(desc, condition) {
  if (condition) {
    console.log(`  ✅ PASS: ${desc}`);
    passCount++;
  } else {
    console.error(`  ❌ FAIL: ${desc}`);
    failCount++;
  }
}

// ==========================================
// TEST SUITE 1: LOT BUILDER BUGS
// ==========================================
console.log('--- TEST SUITE 1: Multi-Lot Builder Fixes ---');

// Test 1.1: Container clearing on openCreateLotModal (BUG-05)
mockElements['lots-builder-list'].innerHTML = '<div class="lot-builder-card" id="row-999">STUCK ROW</div>';
evalIn('lotBuilderRows = [999];');
evalIn('openCreateLotModal();');

assert(
  'BUG-05 Fix: openCreateLotModal clears old DOM cards from #lots-builder-list',
  !mockElements['lots-builder-list'].innerHTML.includes('STUCK ROW') &&
  evalIn('lotBuilderRows.length') === 1
);

// Test 1.2: Add rows & check that multiple rows can be removed (BUG-06)
evalIn('addLotRow();');
evalIn('addLotRow();');
assert(
  'BUG-06 Fix: When multiple rows exist (3), all 3 rows are tracked in lotBuilderRows',
  evalIn('lotBuilderRows.length') === 3
);

// Test 1.3: Removing row 1
const firstRowId = evalIn('lotBuilderRows[0]');
evalIn(`removeLotRow(${firstRowId});`);
assert(
  'BUG-06 Fix: Row 1 can be successfully removed from builder',
  !evalIn('lotBuilderRows').includes(firstRowId) && evalIn('lotBuilderRows.length') === 2
);

// Test 1.4: publishAllLots clears form and resets builder (BUG-07)
const lotsBefore = evalIn('marketItems.length');
evalIn('publishAllLots();');
assert(
  'BUG-07 Fix: publishAllLots adds items, resets builder rows, and closes modal',
  evalIn('marketItems.length') > lotsBefore &&
  evalIn('lotBuilderRows.length') === 0 &&
  mockElements['lot-modal'].classList.contains('hidden')
);

// ==========================================
// TEST SUITE 2: STOREFRONT SUBSCRIPTION
// ==========================================
console.log('\n--- TEST SUITE 2: Storefront Subscription & Access ---');

// Test 2.1: geek_mann is always subscribed (Super Admin)
assert(
  'geek_mann / 208825850 has perpetual active storefront subscription',
  evalIn('hasStorefrontSubscription(208825850)') === true &&
  evalIn('hasStorefrontSubscription("geek_mann")') === true &&
  evalIn('hasStorefrontSubscription("Ярость всегда рядом")') === true
);

// Test 2.2: Random player is not subscribed by default
assert(
  'Random player without subscription returns false',
  evalIn('hasStorefrontSubscription("random_player_999")') === false
);

// Test 2.3: openMyStorefront behavior for unsubscribed user
evalIn('applyUserIdentity(99999999, "unsub_player");');
evalIn('openMyStorefront();');
assert(
  'Unsubscribed user calling openMyStorefront triggers #rent-store-modal',
  !mockElements['rent-store-modal'].classList.contains('hidden')
);

// Reset modal
evalIn('closeRentStoreModal();');
assert(
  'closeRentStoreModal hides the rent modal',
  mockElements['rent-store-modal'].classList.contains('hidden')
);

// ==========================================
// TEST SUITE 3: ToR PAYMENT LOG VERIFICATION
// ==========================================
console.log('\n--- TEST SUITE 3: ToR Payment Log Verification ---');

// Test 3.1: Valid Cores transfer log parsing
const validCoresLog = `Tower Of Random (Текстовая MMORPG)
✅ Вы успешно передали 27000 ядер игроку Ярость всегда рядом.
🔮 Ваш баланс: 21810 ядер`;

const parsedCores = evalIn(`parseToRTransferLog(\`${validCoresLog}\`)`);
assert(
  'parseToRTransferLog correctly parses 27000 cores to Ярость всегда рядом',
  parsedCores.ok === true &&
  parsedCores.amount === 27000 &&
  parsedCores.currencyType === 'cores' &&
  parsedCores.recipient === 'Ярость всегда рядом'
);

// Test 3.2: Valid RND transfer log parsing
const validRndLog = `✅ Вы успешно передали 1000 RND игроку Ярость всегда рядом.`;
const parsedRnd = evalIn(`parseToRTransferLog(\`${validRndLog}\`)`);
assert(
  'parseToRTransferLog correctly parses 1000 RND to Ярость всегда рядом',
  parsedRnd.ok === true &&
  parsedRnd.amount === 1000 &&
  parsedRnd.currencyType === 'rnd' &&
  parsedRnd.recipient === 'Ярость всегда рядом'
);

// Test 3.3: Submit valid payment log grants subscription
evalIn('applyUserIdentity(12345678, "test_payer");');
mockElements['rent-log-input'].value = validCoresLog;
evalIn('submitRentPaymentLog();');

assert(
  'submitRentPaymentLog activates 30-day storefront subscription for test_payer',
  evalIn('hasStorefrontSubscription(12345678)') === true &&
  evalIn('hasStorefrontSubscription("test_payer")') === true
);

// Test 3.4: Anti-replay protection (cannot reuse the same log)
mockElements['rent-log-input'].value = validCoresLog;
evalIn('submitRentPaymentLog();');
assert(
  'Anti-Replay: Submitting the same transfer log again is rejected',
  mockElements['toast-message'].textContent.includes('уже был использован')
);

// Test 3.5: Reject log with wrong recipient
const wrongRecipientLog = `✅ Вы успешно передали 27000 ядер игроку Карп.`;
mockElements['rent-log-input'].value = wrongRecipientLog;
evalIn('submitRentPaymentLog();');
assert(
  'Wrong Recipient: Transfer to non-admin player is rejected',
  mockElements['toast-message'].textContent.includes('должен быть адресован')
);

// Test 3.6: Reject insufficient amount
const lowAmountLog = `✅ Вы успешно передали 500 ядер игроку Ярость всегда рядом.`;
mockElements['rent-log-input'].value = lowAmountLog;
evalIn('submitRentPaymentLog();');
assert(
  'Insufficient Amount: Transfer under configured price is rejected',
  mockElements['toast-message'].textContent.includes('Недостаточно')
);

// ==========================================
// TEST SUITE 4: MARKET PRIORITIZATION
// ==========================================
console.log('\n--- TEST SUITE 4: Market VIP Prioritization ---');

// Populate market with 2 items: 1 unsubscribed, 1 subscribed (test_payer has active sub!)
evalIn(`
marketItems = [
  {
    id: 1,
    title: 'Обычный Меч Новичка',
    category: 'weapon',
    seller: 'random_player_unsub',
    sellerContact: '@random_player_unsub',
    priceCores: '500 🔮',
    date: 'Вчера'
  },
  {
    id: 2,
    title: 'Катана Тьмы +15 VIP',
    category: 'weapon',
    seller: 'test_payer',
    sellerContact: '@test_payer',
    priceCores: '90000 🔮',
    date: 'Сегодня'
  }
];
renderMarketList();
`);

const marketHtml = mockElements['market-list'].innerHTML;

// Find indexes of items in generated HTML
const vipItemPos = marketHtml.indexOf('Катана Тьмы +15 VIP');
const regularItemPos = marketHtml.indexOf('Обычный Меч Новичка');

assert(
  'VIP Priority: Subscribed storefront lot appears BEFORE unsubscribed lot on the market',
  vipItemPos >= 0 && regularItemPos >= 0 && vipItemPos < regularItemPos
);

// Card markup checks
const vipCard = evalIn('renderItemCard(marketItems.find(i => i.id === 2), false)');
const regCard = evalIn('renderItemCard(marketItems.find(i => i.id === 1), false)');

assert(
  'VIP lot card contains 🔥 В ЛАВКЕ badge and 🏪 В лавку button',
  vipCard.includes('vip-store-badge') && vipCard.includes('store-btn')
);

assert(
  'Unsubscribed lot card DOES NOT have 🏪 В лавку button (direct trade only)',
  !regCard.includes('store-btn') && !regCard.includes('vip-store-badge')
);

// ==========================================
// TEST SUITE 5: ADMIN PANEL ACCESS & MANAGEMENT
// ==========================================
console.log('\n--- TEST SUITE 5: Admin Panel & Settings ---');

// Test 5.1: Super Admin check
assert(
  'geek_mann (208825850) is Super Admin',
  evalIn('isUserAdmin(208825850)') === true
);

// Test 5.2: Regular user is not admin
assert(
  'Random user is not admin',
  evalIn('isUserAdmin(99999999)') === false
);

// Test 5.3: Add admin user
mockElements['new-admin-input'].value = 'https://vk.com/id777888';
evalIn('addAdminUser();');
assert(
  'addAdminUser parsed vk.com/id777888 and added 777888 to admins',
  evalIn('isUserAdmin(777888)') === true
);

// Test 5.4: Cannot remove root admin
evalIn('removeAdminUser(208825850);');
assert(
  'Super Admin 208825850 cannot be removed from admin list',
  evalIn('isUserAdmin(208825850)') === true
);

// Test 5.5: Manual storefront grant & revoke
mockElements['manual-store-user'].value = 'lucky_winner';
evalIn('grantManualStorefront();');
assert(
  'grantManualStorefront activated storefront for lucky_winner',
  evalIn('hasStorefrontSubscription("lucky_winner")') === true
);

evalIn('revokeStorefront("lucky_winner");');
assert(
  'revokeStorefront successfully deactivated storefront for lucky_winner',
  evalIn('hasStorefrontSubscription("lucky_winner")') === false
);

// ==========================================
// TEST SUITE 6: USER ORDERS & DYNAMIC MARKET BUTTON & ADMIN ACTIONS
// ==========================================
console.log('\n--- TEST SUITE 6: User Orders & Dynamic Controls ---');

// Test 6.1: User Order History Deletion
evalIn(`
  saveUserOrderRecord({ order_id: 'ord_123', race: 'Человек', style: 'Аниме', date: '26.10.2026' });
  saveUserOrderRecord({ order_id: 'ord_456', race: 'Эльф', style: 'Реализм', date: '26.10.2026' });
`);
let ordersList = evalIn('loadUserOrders()');
assert(
  'User orders saved and retrievable (2 orders)',
  ordersList.length === 2
);

evalIn('removeUserOrder("ord_123")');
ordersList = evalIn('loadUserOrders()');
assert(
  'removeUserOrder successfully removed specific order ord_123',
  ordersList.length === 1 && ordersList[0].order_id === 'ord_456'
);

// Test 6.2: Dynamic Market Button (Rent vs My Storefront)
// Unsubscribed user:
evalIn(`
  currentUserId = 1234567;
  currentUserName = 'UnsubscribedPlayer';
  updateMarketStoreActionButton();
`);
let btnHtml = mockElements['market-store-action-box'].innerHTML;
assert(
  'Unsubscribed user sees ONLY "🔥 Аренда лавки" button',
  btnHtml.includes('Аренда лавки') && !btnHtml.includes('МОЯ ЛАВКА')
);

// Subscribed user:
evalIn(`
  currentUserId = 208825850;
  currentUserName = 'geek_mann';
  updateMarketStoreActionButton();
`);
btnHtml = mockElements['market-store-action-box'].innerHTML;
assert(
  'Subscribed user (geek_mann) sees ONLY "🏪 МОЯ ЛАВКА" button',
  btnHtml.includes('МОЯ ЛАВКА') && !btnHtml.includes('Аренда лавки')
);

// Test 6.3: Clean Expired Subscriptions
evalIn(`
  const testSubs = [
    { userId: 208825850, userNick: 'geek_mann', expiresAt: 253402300799000 },
    { userId: 111111, userNick: 'OldPlayer', expiresAt: Date.now() - 100000 },
    { userId: 222222, userNick: 'FreshPlayer', expiresAt: Date.now() + 1000000 }
  ];
  saveSubscriptions(testSubs);
  cleanExpiredSubscriptions();
`);
const cleanedSubs = evalIn('loadSubscriptions()');
assert(
  'cleanExpiredSubscriptions removed expired OldPlayer while keeping geek_mann and FreshPlayer',
  cleanedSubs.length === 2 && cleanedSubs.some(s => s.userId === 208825850) && cleanedSubs.some(s => s.userId === 222222)
);

// ==========================================
// TEST SUITE 7: ALTAR PROPOSALS IN ADMIN TAB
// ==========================================
console.log('\n--- TEST SUITE 7: Altar Proposals in Admin Tab ---');

// Test 7.1: Submit proposal
mockElements['suggest-author'].value = 'Тазир';
mockElements['suggest-text'].value = 'Знамение: удача ждет того, кто не боится Бездны!';
evalIn(`
  oracleProposals = [];
  submitOracleProposal();
`);
const pendingProps = evalIn('oracleProposals');
assert(
  'submitOracleProposal adds proposal to queue',
  pendingProps.length === 1 && pendingProps[0].author === 'Тазир'
);

// Test 7.2: Proposal badge and Admin Tab rendering
evalIn(`
  currentUserId = 208825850;
  renderAdminPanel();
`);
const badgeEl = mockElements['admin-proposals-badge'];
const propContainerHtml = mockElements['proposals-container'].innerHTML;
assert(
  'Admin proposals badge shows count and container renders proposal card',
  badgeEl.textContent === '1' && !badgeEl.classList.contains('hidden') && propContainerHtml.includes('Тазир')
);

// Test 7.3: Accept proposal
const propId = pendingProps[0].id;
const initialOracleCount = evalIn('oracleMessages.length');
evalIn(`acceptProposal(${propId});`);
const remainingProps = evalIn('oracleProposals');
const newOracleCount = evalIn('oracleMessages.length');
const oracleContainsText = evalIn('oracleMessages.includes("Знамение: удача ждет того, кто не боится Бездны!")');
assert(
  'acceptProposal removes proposal from queue and adds text to oracleMessages pool',
  remainingProps.length === 0 && newOracleCount === initialOracleCount + 1 && oracleContainsText
);

// Test 7.4: Reject proposal
evalIn(`
  oracleProposals = [{ id: 999, author: 'Спамер', text: 'Спам-предсказание', date: '26.10' }];
  renderAdminPanel();
  rejectProposal(999);
`);
const rejectedRemaining = evalIn('oracleProposals');
assert(
  'rejectProposal removes proposal without adding to oracleMessages',
  rejectedRemaining.length === 0 && !evalIn('oracleMessages.includes("Спам-предсказание")')
);

// ==========================================
// SUMMARY
// ==========================================
console.log('\n====================================================');
console.log(`TEST RESULTS: ${passCount} PASSED, ${failCount} FAILED`);
console.log('====================================================');

if (failCount > 0) {
  process.exit(1);
} else {
  process.exit(0);
}
