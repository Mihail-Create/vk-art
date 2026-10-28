// test_miniapp_phase1.js - Тестирование логики Mini App (Этап 1: До исправлений)
const fs = require('fs');
const vm = require('vm');

// Мокаем DOM-окружение в минимальном виде для Node
const domStore = {};
global.window = { location: { search: '', hostname: 'localhost' } };
global.document = {
  getElementById: (id) => {
    if (!domStore[id]) {
      domStore[id] = {
        id,
        value: '',
        textContent: '',
        innerHTML: '',
        classList: {
          contains: (cls) => (domStore[id]._classes || []).includes(cls),
          add: (cls) => {
            domStore[id]._classes = domStore[id]._classes || [];
            if (!domStore[id]._classes.includes(cls)) domStore[id]._classes.push(cls);
          },
          remove: (cls) => {
            domStore[id]._classes = (domStore[id]._classes || []).filter(c => c !== cls);
          },
          toggle: (cls, force) => {
            if (force !== undefined) {
              if (force) domStore[id].classList.add(cls);
              else domStore[id].classList.remove(cls);
            }
          }
        },
        querySelectorAll: (sel) => [],
        insertAdjacentHTML: (pos, html) => {
          domStore[id].innerHTML += html;
        },
        focus: () => {},
        addEventListener: () => {},
        style: {}
      };
    }
    return domStore[id];
  },
  querySelectorAll: (sel) => [],
  querySelector: (sel) => ({
    textContent: '',
    className: '',
    classList: {
      add: () => {},
      remove: () => {}
    }
  }),
  addEventListener: () => {}
};
global.localStorage = {
  _data: {},
  getItem: (k) => global.localStorage._data[k] || null,
  setItem: (k, v) => { global.localStorage._data[k] = String(v); },
  removeItem: (k) => { delete global.localStorage._data[k]; }
};

// Загружаем код app.js
const appCode = fs.readFileSync('C:/Users/user/Desktop/vk-art-bot/miniapp/app.js', 'utf8');

// Выполняем код в контексте
try {
  vm.runInThisContext(appCode);
  console.log('✅ app.js загружен без синтаксических ошибок');
} catch (e) {
  console.error('❌ Ошибка загрузки app.js:', e);
  process.exit(1);
}

const tests = [];
function runTest(name, fn) {
  try {
    fn();
    tests.push({ name, status: 'PASS' });
    console.log(`[PASS] ${name}`);
  } catch (err) {
    tests.push({ name, status: 'FAIL', error: err.message });
    console.error(`[FAIL] ${name} -> ${err.message}`);
  }
}

// ТЕСТ 1: Инициализация модалки лотов и проверка очистки контейнера
runTest('Тест 1: Конструктор лотов - повторное открытие оставляет старые элементы', () => {
  const container = document.getElementById('lots-builder-list');
  container.innerHTML = '<div class="lot-builder-card" id="row-old-1">Старый лот 1</div>';
  
  // Открываем модалку лотов
  openCreateLotModal();
  
  // Проверяем: очистился ли старый лот?
  if (container.innerHTML.includes('row-old-1')) {
    throw new Error('BUG DETECTED: container не был очищен! Старый лот остался в модалке!');
  }
});

// ТЕСТ 2: Удаление первой строки лота
runTest('Тест 2: Первая строка лота должна иметь кнопку удаления при нескольких лотах', () => {
  const container = document.getElementById('lots-builder-list');
  container.innerHTML = '';
  lotBuilderRows = [];
  
  addLotRow();
  addLotRow();
  
  // Проверяем, есть ли у первой строки кнопка удаления
  const firstCardHtml = container.innerHTML.split('lot-builder-card')[1];
  if (!firstCardHtml.includes('remove-row-btn')) {
    throw new Error('BUG DETECTED: Первая строка лота не имеет кнопки удаления remove-row-btn!');
  }
});

// ТЕСТ 3: Проверка прав ВОС
runTest('Тест 3: Проверка прав ВОС для geek_mann (208825850)', () => {
  if (!VOS_USER_IDS.includes(208825850)) {
    throw new Error('geek_mann (208825850) отсутствует в VOS_USER_IDS');
  }
});

// ТЕСТ 4: Доступ обычного игрока к предложениям
runTest('Тест 4: Блокировка вкладки предложений для обычного пользователя (11111)', () => {
  applyUserIdentity(11111, 'Обычный Игрок');
  if (isUserOfficer) {
    throw new Error('Обычный игрок определился как офицер!');
  }
});

console.log('\n--- ИТОГИ ТЕСТОВ ФАЗЫ 1 ---');
console.log(JSON.stringify(tests, null, 2));
