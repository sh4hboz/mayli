/* Mayli — stol bron qilish (2D sxema + OTP oqimi).
   Stollar /booking/availability/ dan olinadi; holat: free/busy/small.
   Monoxrom (faqat oq/qora): holatlar shaffoflik/chiziq uslubi/belgi bilan ajraladi. */
(function () {
  'use strict';

  var page = document.getElementById('booking-page');
  if (!page) return;

  var SVGNS = 'http://www.w3.org/2000/svg';
  var LANG = (document.documentElement.lang || 'uz').slice(0, 2);
  var MSG = window.BOOKING_MESSAGES || {};

  function t(key) {
    var m = MSG[key];
    if (!m) return '';
    return m[LANG] || m.uz || '';
  }

  // ── HTTP yordamchilari (cart.js naqshi) ─────────────────────────────────
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
  function getJSON(url) {
    return fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); });
  }
  function digits(s) { return (s || '').replace(/\D/g, ''); }
  function setMsg(el, text, isError) {
    el.textContent = text;
    el.className = 'cart-msg' + (isError ? ' cart-msg--error' : ' cart-msg--info');
  }

  // ── Holat ───────────────────────────────────────────────────────────────
  var tablesByZone = {};
  var currentZone = null;
  var selected = null;       // tanlangan stol obyekti
  var verifiedPhone = '';

  // ── Elementlar ──────────────────────────────────────────────────────────
  var dateEl = document.getElementById('bk-date');
  var timeEl = document.getElementById('bk-time');
  var guestsEl = document.getElementById('bk-guests');
  var planEl = document.getElementById('booking-plan');
  var zoneTabs = page.querySelectorAll('.bk-zone-tab');
  var selectedBar = document.getElementById('bk-selected');
  var selectedInfo = document.getElementById('bk-selected-info');

  var stepPlan = document.getElementById('bk-step-plan');
  var stepForm = document.getElementById('bk-step-form');
  var summaryEl = document.getElementById('bk-summary');
  var formEl = document.getElementById('bk-form');
  var otpEl = document.getElementById('bk-otp');
  var msgEl = document.getElementById('bk-msg');
  var otpMsgEl = document.getElementById('bk-otp-msg');
  var successEl = document.getElementById('bk-success');

  var isOpen = page.getAttribute('data-booking-open') !== '0';

  // ── Boshlang'ich sozlash ────────────────────────────────────────────────
  function buildTimeOptions() {
    var open = (page.getAttribute('data-open-time') || '10:00').split(':');
    var close = (page.getAttribute('data-close-time') || '23:00').split(':');
    var from = parseInt(open[0], 10) * 60 + parseInt(open[1], 10);
    var to = parseInt(close[0], 10) * 60 + parseInt(close[1], 10);
    timeEl.innerHTML = '';
    for (var m = from; m <= to; m += 30) {
      var hh = ('0' + Math.floor(m / 60)).slice(-2);
      var mm = ('0' + (m % 60)).slice(-2);
      var opt = document.createElement('option');
      opt.value = hh + ':' + mm;
      opt.textContent = hh + ':' + mm;
      timeEl.appendChild(opt);
    }
    // Standart: 19:00 bo'lsa tanla
    if ([].slice.call(timeEl.options).some(function (o) { return o.value === '19:00'; })) {
      timeEl.value = '19:00';
    }
  }

  function initControls() {
    var today = page.getAttribute('data-today');
    var maxDate = page.getAttribute('data-max-date');
    if (today) { dateEl.min = today; dateEl.value = today; }
    if (maxDate) { dateEl.max = maxDate; }
    buildTimeOptions();
  }

  // ── Availability ──────────────────────────────────────────────────────
  function params() {
    return {
      date: dateEl.value,
      time: timeEl.value,
      guests: parseInt(guestsEl.value, 10) || 1
    };
  }

  function loadAvailability() {
    clearSelection();
    var p = params();
    if (!p.date || !p.time) { planEl.innerHTML = '<p class="bk-empty">' + t('choose_dt') + '</p>'; return; }
    planEl.innerHTML = '<p class="bk-empty">' + t('loading') + '</p>';
    var url = page.getAttribute('data-availability-url') +
      '?date=' + encodeURIComponent(p.date) +
      '&time=' + encodeURIComponent(p.time) +
      '&guests=' + encodeURIComponent(p.guests);
    getJSON(url).then(function (d) {
      tablesByZone = {};
      (d.tables || []).forEach(function (tb) {
        (tablesByZone[tb.zone_id] = tablesByZone[tb.zone_id] || []).push(tb);
      });
      if (!currentZone && zoneTabs.length) {
        currentZone = zoneTabs[0].getAttribute('data-zone');
      }
      renderPlan();
    }).catch(function () {
      planEl.innerHTML = '<p class="bk-empty">' + t('network') + '</p>';
    });
  }

  // ── SVG sxema ───────────────────────────────────────────────────────────
  function currentTables() {
    if (currentZone) return tablesByZone[currentZone] || [];
    // Zona tab bo'lmasa — hammasi
    var all = [];
    Object.keys(tablesByZone).forEach(function (k) { all = all.concat(tablesByZone[k]); });
    return all;
  }

  function el(name, attrs) {
    var node = document.createElementNS(SVGNS, name);
    for (var k in attrs) { if (attrs.hasOwnProperty(k)) node.setAttribute(k, attrs[k]); }
    return node;
  }

  function renderPlan() {
    var tables = currentTables();
    planEl.innerHTML = '';
    if (!tables.length) {
      planEl.innerHTML = '<p class="bk-empty">' + t('no_tables') + '</p>';
      return;
    }

    var maxX = 0, maxY = 0;
    tables.forEach(function (tb) {
      maxX = Math.max(maxX, tb.pos_x + tb.width);
      maxY = Math.max(maxY, tb.pos_y + tb.height);
    });
    var pad = 40;
    var svg = el('svg', {
      viewBox: '0 0 ' + (maxX + pad) + ' ' + (maxY + pad),
      class: 'bk-svg',
      preserveAspectRatio: 'xMidYMid meet'
    });

    tables.forEach(function (tb) {
      var isSel = selected && selected.id === tb.id;
      var state = isSel ? 'selected' : tb.state;
      var cx = tb.pos_x + tb.width / 2;
      var cy = tb.pos_y + tb.height / 2;

      var g = el('g', {
        class: 'bk-table bk-table--' + state,
        'data-id': tb.id,
        'data-state': tb.state,
        tabindex: tb.state === 'free' ? '0' : '-1',
        role: 'button'
      });

      if (tb.shape === 'round') {
        g.appendChild(el('circle', {
          cx: cx, cy: cy, r: Math.min(tb.width, tb.height) / 2, class: 'bk-shape'
        }));
      } else {
        g.appendChild(el('rect', {
          x: tb.pos_x, y: tb.pos_y, width: tb.width, height: tb.height,
          rx: 10, ry: 10, class: 'bk-shape'
        }));
      }

      var num = el('text', { x: cx, y: cy - 2, class: 'bk-num', 'text-anchor': 'middle' });
      num.textContent = tb.number;
      g.appendChild(num);

      var cap = el('text', { x: cx, y: cy + 16, class: 'bk-cap', 'text-anchor': 'middle' });
      cap.textContent = tb.capacity + ' ' + t('seat');
      g.appendChild(cap);

      // Band stolga ✕ belgisi (monoxromda ajratish uchun)
      if (tb.state === 'busy') {
        var x = el('text', { x: tb.pos_x + tb.width - 12, y: tb.pos_y + 18, class: 'bk-x', 'text-anchor': 'middle' });
        x.textContent = '✕';
        g.appendChild(x);
      }

      var title = el('title', {});
      title.textContent = tb.number + ' — ' + tb.capacity + ' ' + t('seat');
      g.appendChild(title);

      svg.appendChild(g);
    });

    planEl.appendChild(svg);
  }

  // ── Tanlash ───────────────────────────────────────────────────────────
  function selectTable(id) {
    var tables = currentTables();
    var tb = null;
    for (var i = 0; i < tables.length; i++) { if (String(tables[i].id) === String(id)) { tb = tables[i]; break; } }
    if (!tb || tb.state !== 'free') return;
    selected = tb;
    renderPlan();
    selectedInfo.textContent = t('table_label') + ' ' + tb.zone + ' — ' + tb.number +
      ' · ' + tb.capacity + ' ' + t('seat');
    selectedBar.classList.remove('hidden');
  }

  function clearSelection() {
    selected = null;
    if (selectedBar) selectedBar.classList.add('hidden');
  }

  // ── Hodisalar ───────────────────────────────────────────────────────────
  [dateEl, timeEl, guestsEl].forEach(function (e) {
    if (e) e.addEventListener('change', loadAvailability);
  });

  zoneTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      zoneTabs.forEach(function (x) { x.classList.remove('active'); });
      tab.classList.add('active');
      currentZone = tab.getAttribute('data-zone');
      clearSelection();
      renderPlan();
    });
  });

  planEl.addEventListener('click', function (e) {
    var g = e.target.closest ? e.target.closest('.bk-table') : null;
    if (!g) return;
    selectTable(g.getAttribute('data-id'));
  });
  planEl.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var g = e.target.closest ? e.target.closest('.bk-table') : null;
    if (!g) return;
    e.preventDefault();
    selectTable(g.getAttribute('data-id'));
  });

  // ── 1 → 2 qadam ─────────────────────────────────────────────────────────
  function buildSummary() {
    var p = params();
    var rows = [
      [t('table_label'), selected.zone + ' — ' + selected.number],
      [t('guests_label'), p.guests + ' ' + t('seat')],
      ['', p.date + ' · ' + p.time]
    ];
    summaryEl.innerHTML = '';
    rows.forEach(function (r) {
      var div = document.createElement('div');
      div.className = 'bk-summary-row';
      div.innerHTML = '<span></span><strong></strong>';
      div.querySelector('span').textContent = r[0];
      div.querySelector('strong').textContent = r[1];
      summaryEl.appendChild(div);
    });
  }

  document.getElementById('bk-continue').addEventListener('click', function () {
    if (!selected) return;
    buildSummary();
    stepPlan.classList.add('hidden');
    stepForm.classList.remove('hidden');
    formEl.classList.remove('hidden');
    otpEl.classList.add('hidden');
    msgEl.textContent = '';
    window.scrollTo({ top: page.offsetTop - 80, behavior: 'smooth' });
  });

  document.getElementById('bk-back').addEventListener('click', function () {
    stepForm.classList.add('hidden');
    stepPlan.classList.remove('hidden');
  });

  // ── Forma → OTP → yaratish ──────────────────────────────────────────────
  formEl.addEventListener('submit', function (e) {
    e.preventDefault();
    msgEl.textContent = '';
    if (formEl.querySelector('.hp-field').value.trim()) return; // honeypot
    if (!isOpen) return;
    if (!selected) { setMsg(msgEl, t('pick_table'), true); return; }

    var name = document.getElementById('bk-name').value.trim();
    var phone = document.getElementById('bk-phone').value.trim();
    if (!name) { setMsg(msgEl, t('name_required'), true); return; }
    if (digits(phone).length < 9) { setMsg(msgEl, t('phone_required'), true); return; }

    var btn = document.getElementById('bk-submit');
    btn.disabled = true;
    setMsg(msgEl, t('sending'), false);

    postJSON(page.getAttribute('data-otp-request-url'), { phone: phone, website: '' })
      .then(function (res) {
        btn.disabled = false;
        if (res.data && res.data.success) {
          verifiedPhone = phone;
          msgEl.textContent = '';
          formEl.classList.add('hidden');
          otpEl.classList.remove('hidden');
          setMsg(otpMsgEl, t('code_sent'), false);
          if (res.data.dev_code) { document.getElementById('bk-otp-code').value = res.data.dev_code; }
        } else {
          setMsg(msgEl, (res.data && res.data.error) || t('network'), true);
        }
      })
      .catch(function () { btn.disabled = false; setMsg(msgEl, t('network'), true); });
  });

  document.getElementById('bk-otp-back').addEventListener('click', function () {
    otpEl.classList.add('hidden');
    formEl.classList.remove('hidden');
    otpMsgEl.textContent = '';
  });

  document.getElementById('bk-otp-verify').addEventListener('click', function () {
    var code = document.getElementById('bk-otp-code').value.trim();
    if (!code) { setMsg(otpMsgEl, t('code_required'), true); return; }
    var btn = this;
    btn.disabled = true;
    setMsg(otpMsgEl, t('sending'), false);

    postJSON(page.getAttribute('data-otp-verify-url'), { phone: verifiedPhone, code: code })
      .then(function (res) {
        if (!(res.data && res.data.verified)) {
          btn.disabled = false;
          setMsg(otpMsgEl, (res.data && res.data.error) || t('network'), true);
          return;
        }
        var p = params();
        postJSON(page.getAttribute('data-create-url'), {
          name: document.getElementById('bk-name').value.trim(),
          phone: verifiedPhone,
          note: document.getElementById('bk-note').value.trim(),
          table_id: selected.id,
          date: p.date, time: p.time, guests: p.guests,
          website: ''
        }).then(function (r2) {
          btn.disabled = false;
          if (r2.data && r2.data.success) {
            try { localStorage.setItem('mayli_phone', verifiedPhone); } catch (e) {}
            stepForm.classList.add('hidden');
            stepPlan.classList.add('hidden');
            successEl.classList.remove('hidden');
            window.scrollTo({ top: page.offsetTop - 80, behavior: 'smooth' });
          } else {
            setMsg(otpMsgEl, (r2.data && r2.data.error) || t('network'), true);
          }
        }).catch(function () { btn.disabled = false; setMsg(otpMsgEl, t('network'), true); });
      })
      .catch(function () { btn.disabled = false; setMsg(otpMsgEl, t('network'), true); });
  });

  // ── Ishga tushirish ───────────────────────────────────────────────────
  initControls();
  if (isOpen) { loadAvailability(); }
})();
