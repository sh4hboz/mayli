/* Mayli — savat (cart) + buyurtma (OTP) logikasi.
   Savat localStorage'da ('mayli_cart'). Backend narx/summani DB'dan qayta hisoblaydi. */
(function () {
  'use strict';

  var CART_KEY = 'mayli_cart';
  var LANG = (document.documentElement.lang || 'uz').slice(0, 2);
  var MSG = window.CART_MESSAGES || {};

  function t(key) {
    var m = MSG[key];
    if (!m) return '';
    return m[LANG] || m.uz || '';
  }

  function fmt(n) {
    return Math.round(n).toLocaleString('ru-RU').replace(/[ ,]/g, ' ');
  }

  // ── localStorage savat ────────────────────────────────────────────────
  function getCart() {
    try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
    catch (e) { return []; }
  }
  function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateBadge();
  }
  function clearCart() {
    localStorage.removeItem(CART_KEY);
    updateBadge();
  }
  function totalQty(cart) {
    return (cart || getCart()).reduce(function (s, it) { return s + it.qty; }, 0);
  }
  function totalSum(cart) {
    return (cart || getCart()).reduce(function (s, it) { return s + it.price * it.qty; }, 0);
  }

  function addToCart(id, name, price, img) {
    var cart = getCart();
    var found = null;
    for (var i = 0; i < cart.length; i++) { if (cart[i].id === id) { found = cart[i]; break; } }
    if (found) { found.qty += 1; }
    else { cart.push({ id: id, name: name, price: price, img: img || '', qty: 1 }); }
    saveCart(cart);
  }
  function changeQty(id, delta) {
    var cart = getCart();
    for (var i = 0; i < cart.length; i++) {
      if (cart[i].id === id) {
        cart[i].qty += delta;
        if (cart[i].qty <= 0) { cart.splice(i, 1); }
        break;
      }
    }
    saveCart(cart);
  }
  function removeItem(id) {
    saveCart(getCart().filter(function (x) { return x.id !== id; }));
  }

  // ── Floating cart badge ───────────────────────────────────────────────
  function updateBadge() {
    var n = totalQty();
    var badges = document.querySelectorAll('[data-cart-count]');
    for (var i = 0; i < badges.length; i++) {
      badges[i].textContent = n;
      badges[i].classList.toggle('cart-count--hidden', n === 0);
    }
    if (document.getElementById('cart-page')) { renderCart(); }
  }

  // Header "Buyurtma" linki — faqat mijoz kamida bir marta buyurtma bergach
  // ko'rinadi (OTP'dan o'tib mayli_phone saqlangan bo'lsa).
  function revealOrdersLink() {
    var has = false;
    try { has = !!localStorage.getItem('mayli_phone'); } catch (e) {}
    if (!has) return;
    var links = document.querySelectorAll('[data-orders-link]');
    for (var i = 0; i < links.length; i++) { links[i].classList.add('orders-link--visible'); }
  }

  // ── Toast (3 soniya) ──────────────────────────────────────────────────
  function showToast(name) {
    var prev = document.querySelector('.cart-toast');
    if (prev) prev.remove();
    var toast = document.createElement('div');
    toast.className = 'cart-toast';
    toast.innerHTML =
      '<div class="cart-toast__icon">✓</div>' +
      '<div class="cart-toast__body">' +
        '<div class="cart-toast__name"></div>' +
        '<div class="cart-toast__sub"></div>' +
      '</div>' +
      '<div class="cart-toast__progress"><span></span></div>';
    toast.querySelector('.cart-toast__name').textContent = name;
    toast.querySelector('.cart-toast__sub').textContent = t('added');
    document.body.appendChild(toast);
    requestAnimationFrame(function () { toast.classList.add('cart-toast--in'); });
    setTimeout(function () {
      toast.classList.add('cart-toast--out');
      setTimeout(function () { toast.remove(); }, 300);
    }, 3000);
  }

  // ── "Savatga qo'shish" (delegatsiya — barcha sahifalarda) ─────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.add-to-cart') : null;
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    var id = parseInt(btn.getAttribute('data-id'), 10);
    if (!id) return;
    var name = btn.getAttribute('data-name') || '';
    var price = parseFloat(btn.getAttribute('data-price')) || 0;
    var img = btn.getAttribute('data-img') || '';
    addToCart(id, name, price, img);
    showToast(name);
  });

  // ── Savat sahifasi ────────────────────────────────────────────────────
  var page = document.getElementById('cart-page');

  function getCsrf() {
    var name = 'csrftoken=';
    var parts = (document.cookie || '').split(';');
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf(name) === 0) return decodeURIComponent(c.substring(name.length));
    }
    return '';
  }

  function postJSON(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data)
    }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, data: j }; })
        .catch(function () { return { ok: r.ok, data: {} }; });
    });
  }

  function renderCart() {
    if (!page) return;
    var cart = getCart();
    var empty = document.getElementById('cart-empty');
    var content = document.getElementById('cart-content');
    var success = document.getElementById('cart-success');
    // Muvaffaqiyat ekrani ko'rinib turgan bo'lsa — tegmaymiz.
    if (success && !success.classList.contains('hidden')) return;

    if (!cart.length) {
      if (empty) empty.classList.remove('hidden');
      if (content) content.classList.add('hidden');
      return;
    }
    if (empty) empty.classList.add('hidden');
    if (content) content.classList.remove('hidden');

    var box = document.getElementById('cart-items');
    box.innerHTML = '';
    cart.forEach(function (it) {
      var row = document.createElement('div');
      row.className = 'cart-item';
      row.innerHTML =
        (it.img ? '<div class="cart-item-img"><img src="' + it.img + '" alt="" loading="lazy"></div>'
                : '<div class="cart-item-img cart-item-noimg"><i class="fa fa-cutlery"></i></div>') +
        '<div class="cart-item-info">' +
          '<div class="cart-item-name"></div>' +
          '<div class="cart-item-price">' + fmt(it.price) + ' ' + unitLabel() + '</div>' +
        '</div>' +
        '<div class="cart-item-qty">' +
          '<button type="button" class="qty-btn" data-act="dec" data-id="' + it.id + '">−</button>' +
          '<span class="qty-val">' + it.qty + '</span>' +
          '<button type="button" class="qty-btn" data-act="inc" data-id="' + it.id + '">+</button>' +
        '</div>' +
        '<div class="cart-item-total">' + fmt(it.price * it.qty) + '</div>' +
        '<button type="button" class="cart-item-remove" data-act="rm" data-id="' + it.id + '" aria-label="x"><i class="fa fa-trash-o"></i></button>';
      row.querySelector('.cart-item-name').textContent = it.name;
      box.appendChild(row);
    });

    var total = totalSum(cart);
    document.getElementById('cart-total').textContent = fmt(total);

    // Minimum summa ogohlantirishi
    var minAmount = parseFloat(page.getAttribute('data-min-amount')) || 0;
    var warn = document.getElementById('cart-min-warning');
    var checkoutBtn = document.getElementById('checkout-btn');
    if (minAmount && total < minAmount) {
      warn.textContent = t('min_order') + ' ' + fmt(minAmount) + ' ' + unitLabel();
      warn.classList.remove('hidden');
      if (checkoutBtn) checkoutBtn.disabled = true;
    } else {
      warn.classList.add('hidden');
      if (checkoutBtn) checkoutBtn.disabled = false;
    }
  }

  function unitLabel() {
    return LANG === 'ru' ? 'сум' : (LANG === 'en' ? 'UZS' : "so'm");
  }

  if (page) {
    // Qty / o'chirish (delegatsiya)
    document.getElementById('cart-items').addEventListener('click', function (e) {
      var b = e.target.closest('[data-act]');
      if (!b) return;
      var id = parseInt(b.getAttribute('data-id'), 10);
      var act = b.getAttribute('data-act');
      if (act === 'inc') changeQty(id, 1);
      else if (act === 'dec') changeQty(id, -1);
      else if (act === 'rm') removeItem(id);
    });

    var form = document.getElementById('checkout-form');
    var otpStep = document.getElementById('otp-step');
    var checkoutMsg = document.getElementById('checkout-msg');
    var otpMsg = document.getElementById('otp-msg');
    var verifiedPhone = '';

    function digits(s) { return (s || '').replace(/\D/g, ''); }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      checkoutMsg.textContent = '';
      checkoutMsg.className = 'cart-msg';

      // Honeypot to'lsa — jim to'xtatamiz.
      if (form.querySelector('.hp-field').value.trim()) return;

      if (page.getAttribute('data-order-open') === '0') return;
      if (!getCart().length) { setMsg(checkoutMsg, t('empty'), true); return; }

      var name = document.getElementById('co-name').value.trim();
      var phone = document.getElementById('co-phone').value.trim();
      if (!name) { setMsg(checkoutMsg, t('name_required'), true); return; }
      if (digits(phone).length < 9) { setMsg(checkoutMsg, t('phone_required'), true); return; }

      var btn = document.getElementById('checkout-btn');
      btn.disabled = true;
      setMsg(checkoutMsg, t('sending'), false);

      postJSON(page.getAttribute('data-otp-request-url'), { phone: phone, website: '' })
        .then(function (res) {
          btn.disabled = false;
          if (res.data && res.data.success) {
            verifiedPhone = phone;
            checkoutMsg.textContent = '';
            form.classList.add('hidden');
            otpStep.classList.remove('hidden');
            setMsg(otpMsg, t('code_sent'), false);
            if (res.data.dev_code) {
              document.getElementById('otp-code').value = res.data.dev_code;
            }
          } else {
            setMsg(checkoutMsg, (res.data && res.data.error) || t('network'), true);
          }
        })
        .catch(function () { btn.disabled = false; setMsg(checkoutMsg, t('network'), true); });
    });

    document.getElementById('otp-back-btn').addEventListener('click', function () {
      otpStep.classList.add('hidden');
      form.classList.remove('hidden');
      otpMsg.textContent = '';
    });

    document.getElementById('otp-verify-btn').addEventListener('click', function () {
      var code = document.getElementById('otp-code').value.trim();
      if (!code) { setMsg(otpMsg, t('code_required'), true); return; }
      var btn = this;
      btn.disabled = true;
      setMsg(otpMsg, t('sending'), false);

      postJSON(page.getAttribute('data-otp-verify-url'), { phone: verifiedPhone, code: code })
        .then(function (res) {
          if (!(res.data && res.data.verified)) {
            btn.disabled = false;
            setMsg(otpMsg, (res.data && res.data.error) || t('network'), true);
            return;
          }
          // Tasdiqlandi — buyurtmani yaratamiz.
          var items = getCart().map(function (it) { return { id: it.id, qty: it.qty }; });
          var payEl = form.querySelector('input[name="payment_method"]:checked');
          postJSON(page.getAttribute('data-create-url'), {
            name: document.getElementById('co-name').value.trim(),
            phone: verifiedPhone,
            comment: document.getElementById('co-comment').value.trim(),
            payment_method: payEl ? payEl.value : 'cash',
            items: items,
            website: ''
          }).then(function (r2) {
            btn.disabled = false;
            if (r2.data && r2.data.success) {
              try { localStorage.setItem('mayli_phone', (r2.data.phone || verifiedPhone)); } catch (e) {}
              clearCart();
              var myUrl = page.getAttribute('data-my-orders-url');
              if (myUrl) { window.location.href = myUrl; return; }
              document.getElementById('cart-content').classList.add('hidden');
              document.getElementById('cart-success').classList.remove('hidden');
            } else {
              setMsg(otpMsg, (r2.data && r2.data.error) || t('network'), true);
            }
          }).catch(function () { btn.disabled = false; setMsg(otpMsg, t('network'), true); });
        })
        .catch(function () { btn.disabled = false; setMsg(otpMsg, t('network'), true); });
    });

    function setMsg(el, text, isError) {
      el.textContent = text;
      el.className = 'cart-msg' + (isError ? ' cart-msg--error' : ' cart-msg--info');
    }

    renderCart();
  }

  // ── Buyurtmalarim sahifasi ────────────────────────────────────────────
  function esc(s) {
    var d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  }

  var ordersPage = document.getElementById('orders-page');
  if (ordersPage) {
    (function () {
      var phone = '';
      try { phone = localStorage.getItem('mayli_phone') || ''; } catch (e) {}
      var loading = document.getElementById('orders-loading');
      var none = document.getElementById('orders-none');
      var listEl = document.getElementById('orders-list');
      var tabs = ordersPage.querySelectorAll('.orders-tab');
      var allOrders = [];
      var currentTab = 'all';

      function statusClass(s) {
        if (s === 'completed') return 'ord-badge ord-badge--done';
        if (s === 'rejected') return 'ord-badge ord-badge--cancel';
        if (s === 'accepted') return 'ord-badge ord-badge--accepted';
        return 'ord-badge ord-badge--new';
      }

      function cardHtml(o) {
        var items = o.items.map(function (it) {
          return '<div class="ord-line"><span>' + esc(it.name) + ' × ' + it.qty +
                 '</span><span>' + fmt(it.total) + '</span></div>';
        }).join('');
        var reason = o.reject_reason
          ? '<div class="ord-reason">' + esc(o.reject_reason) + '</div>' : '';
        return '<div class="ord-card">' +
          '<div class="ord-head"><span class="ord-id">#' + o.id + '</span>' +
          '<span class="' + statusClass(o.status) + '">' + esc(o.status_label) + '</span></div>' +
          '<div class="ord-date">' + esc(o.created_at) + '</div>' +
          '<div class="ord-items">' + items + '</div>' +
          '<div class="ord-total">' + (LANG === 'ru' ? 'Итого' : (LANG === 'en' ? 'Total' : 'Jami')) +
          ': <strong>' + fmt(o.total) + ' ' + unitLabel() + '</strong></div>' +
          reason + '</div>';
      }

      function render() {
        var rows = currentTab === 'active'
          ? allOrders.filter(function (o) { return o.is_active; }) : allOrders;
        if (!rows.length) {
          listEl.innerHTML = '<div class="orders-empty"><p>' +
            (currentTab === 'active'
              ? (LANG === 'ru' ? 'Нет активных заказов.' : (LANG === 'en' ? 'No active orders.' : 'Faol buyurtma yo‘q.'))
              : (LANG === 'ru' ? 'Заказов нет.' : (LANG === 'en' ? 'No orders.' : 'Buyurtma yo‘q.'))) +
            '</p></div>';
          return;
        }
        listEl.innerHTML = rows.map(cardHtml).join('');
      }

      tabs.forEach(function (tb) {
        tb.addEventListener('click', function () {
          tabs.forEach(function (x) { x.classList.remove('active'); });
          tb.classList.add('active');
          currentTab = tb.getAttribute('data-tab');
          render();
        });
      });

      if (!phone) {
        loading.classList.add('hidden');
        none.classList.remove('hidden');
      } else {
        fetch(ordersPage.getAttribute('data-url') + '?phone=' + encodeURIComponent(phone), {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            allOrders = (d && d.orders) || [];
            loading.classList.add('hidden');
            if (!allOrders.length) { none.classList.remove('hidden'); return; }
            listEl.classList.remove('hidden');
            render();
          })
          .catch(function () { loading.classList.add('hidden'); none.classList.remove('hidden'); });
      }
    })();
  }

  updateBadge();
  revealOrdersLink();
})();
