/* ==========================================================================
   custom-management.js — Mayli Restobar boshqaruv paneli (dashboard) JS
   --------------------------------------------------------------------------
   - data-toggle-url + data-field : is_active / is_available ni AJAX bilan
     o'zgartiradi (toggle_active_ajax view). Sahifa qayta yuklanmaydi.
   - data-confirm : o'chirish/xavfli amallardan oldin tasdiq so'raydi.
   ========================================================================== */
(function () {
  "use strict";

  // --- CSRF cookie ---
  function getCookie(name) {
    if (!document.cookie) return null;
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var c = cookies[i].trim();
      if (c.substring(0, name.length + 1) === name + "=") {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return null;
  }

  // --- Status badge matnini almashtirish (ma'lum juftliklar) ---
  var TEXT_PAIRS = [
    ["Faol", "Nofaol"],
    ["Ha", "Yo'q"],
    ["Yoqilgan", "O'chirilgan"],
  ];
  function swapBadgeText(badge) {
    if (!badge) return;
    var cur = badge.textContent.trim();
    for (var i = 0; i < TEXT_PAIRS.length; i++) {
      var p = TEXT_PAIRS[i];
      if (cur === p[0]) { badge.textContent = p[1]; return; }
      if (cur === p[1]) { badge.textContent = p[0]; return; }
    }
  }

  function applyToggleState(btn, val) {
    btn.classList.toggle("btn-success", !!val);
    btn.classList.toggle("btn-secondary", !val);
    swapBadgeText(btn.querySelector(".status-badge"));
    var icon = btn.querySelector("i.ti");
    if (icon && (icon.classList.contains("ti-eye") || icon.classList.contains("ti-eye-off"))) {
      icon.classList.toggle("ti-eye", !!val);
      icon.classList.toggle("ti-eye-off", !val);
    }
    var card = btn.closest(".gallery-item");
    if (card) card.classList.toggle("gallery-item-inactive", !val);
  }

  // --- is_active / is_available toggle ---
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-toggle-url]");
    if (!btn) return;
    e.preventDefault();
    if (btn.dataset.busy === "1") return;

    var url = btn.getAttribute("data-toggle-url");
    var field = btn.getAttribute("data-field") || "is_active";
    btn.dataset.busy = "1";

    fetch(url + "?field=" + encodeURIComponent(field), {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.success) {
          applyToggleState(btn, data[field]);
        } else {
          window.alert((data && data.error) || "Amalni bajarib bo'lmadi.");
        }
      })
      .catch(function () { window.alert("Tarmoq xatosi. Qayta urinib ko'ring."); })
      .finally(function () { btn.dataset.busy = ""; });
  });

  // --- Tug'ilgan kun SMS tabrigi (topbar tugmasi) ---
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-birthday-congratulate]");
    if (!btn) return;
    e.preventDefault();
    if (btn.dataset.busy === "1") return;

    var msg = btn.getAttribute("data-confirm-msg");
    if (msg && !window.confirm(msg)) return;

    var url = btn.getAttribute("data-url");
    btn.dataset.busy = "1";
    btn.disabled = true;

    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        window.alert((data && data.message) || "Bajarildi.");
        if (data && data.sent) {
          // Yuborilgach bildirishnomani yashiramiz
          var note = document.getElementById("birthday-notification");
          if (note) note.remove();
        }
      })
      .catch(function () { window.alert("Tarmoq xatosi. Qayta urinib ko'ring."); })
      .finally(function () { btn.dataset.busy = ""; btn.disabled = false; });
  });

  // --- Bildirishnomalar: "Hammasi o'qildi" ---
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-mark-all-read]");
    if (!btn) return;
    e.preventDefault();
    var wrap = document.getElementById("notification-dropdown-people");
    var url = wrap && wrap.getAttribute("data-notif-mark-url");
    if (!url) return;
    btn.disabled = true;
    fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken"), "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) { return r.json(); })
      .then(function () { window.location.reload(); })
      .catch(function () { btn.disabled = false; });
  });

  // --- Bildirishnoma badge'ni orqaga qaytishda (bfcache) yangilash ---
  function updateNotifBadge(count) {
    var badge = document.getElementById("topbar-notif-badge");
    if (badge) {
      badge.textContent = count;
      badge.classList.toggle("d-none", !count);
    }
    var markBtn = document.getElementById("topbar-notif-mark-all");
    if (markBtn) markBtn.classList.toggle("d-none", !count);
  }
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return; // oddiy yuklanishda server badge'ni to'g'ri beradi
    var wrap = document.getElementById("notification-dropdown-people");
    var url = wrap && wrap.getAttribute("data-notif-count-url");
    if (!url) return;
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && typeof d.count !== "undefined") updateNotifBadge(d.count); })
      .catch(function () {});
  });

  // --- Tasdiq so'rash (o'chirish va h.k.) ---
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-confirm]");
    if (!el) return;
    var msg = el.getAttribute("data-confirm") || "Ishonchingiz komilmi?";
    if (!window.confirm(msg)) {
      e.preventDefault();
      e.stopPropagation();
    }
  });

  // --- Alert (xabar) bildirishnomalarini 5 soniyada avtomatik yopish ---
  (function () {
    var alerts = document.querySelectorAll(".alert-dismissible");
    Array.prototype.forEach.call(alerts, function (el) {
      setTimeout(function () {
        if (window.bootstrap && bootstrap.Alert) {
          bootstrap.Alert.getOrCreateInstance(el).close();
        } else {
          el.classList.remove("show");
          setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 200);
        }
      }, 5000);
    });
  })();

  // --- Sayt chat (dashboard) jonli yangilanish (oddiy poll) ---
  (function () {
    var thread = document.getElementById("chat-messages");
    if (!thread || !thread.dataset.pollUrl) return;
    var url = thread.dataset.pollUrl;
    var after = parseInt(thread.dataset.after || "0", 10) || 0;

    function esc(s) {
      var d = document.createElement("div");
      d.textContent = s == null ? "" : String(s);
      return d.innerHTML;
    }
    function scrollBottom() { thread.scrollTop = thread.scrollHeight; }
    scrollBottom();

    function append(m) {
      if (thread.querySelector('[data-msg-id="' + m.id + '"]')) return;
      var empty = document.getElementById("chat-empty");
      if (empty) empty.remove();
      var wrap = document.createElement("div");
      wrap.className = "chat-msg chat-msg-" + m.direction;
      wrap.setAttribute("data-msg-id", m.id);
      var meta = (m.is_auto ? "avto · " : "") + esc(m.time);
      wrap.innerHTML =
        '<div class="chat-bubble">' + esc(m.text) +
        '<span class="chat-meta">' + meta + "</span></div>";
      thread.appendChild(wrap);
    }

    function poll() {
      fetch(url + "?after=" + after, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var msgs = (data && data.messages) || [];
          if (!msgs.length) return;
          msgs.forEach(function (m) { append(m); if (m.id > after) after = m.id; });
          scrollBottom();
        })
        .catch(function () {});
    }
    setInterval(poll, 5000);
  })();
})();
