/* ==========================================================================
   sms-campaign.js — SMS yuborgich (dashboard)
   - Shablon tugmasi → yashirin sms_template_id + matn preview to'ladi.
   - "Barcha mijozlar" belgilansa → guruh (teg) tanlovi o'chiriladi.
   - Qo'lda raqamlar: IMask (+998...) bilan bittadan qo'shiladi (chip), yashirin textarea'ga sinxron.
   - "Hozir / Vaqtni tanlash" radiosi → sana maydonini ko'rsatadi/yashiradi.
   ========================================================================== */
(function () {
  "use strict";

  // --- Shablon tugmalari ---
  var hidden = document.getElementById("id_sms_template_id");
  var preview = document.getElementById("id_template");
  var buttons = document.querySelectorAll(".sms-tpl-btn");

  function selectBtn(btn) {
    Array.prototype.forEach.call(buttons, function (b) { b.classList.remove("active"); });
    btn.classList.add("active");
    if (hidden) hidden.value = btn.getAttribute("data-id") || "";
    if (preview) preview.value = btn.getAttribute("data-text") || "";
  }

  Array.prototype.forEach.call(buttons, function (btn) {
    btn.addEventListener("click", function () { selectBtn(btn); });
  });

  if (hidden && hidden.value) {
    Array.prototype.forEach.call(buttons, function (btn) {
      if (btn.getAttribute("data-id") === hidden.value) btn.classList.add("active");
    });
  }

  // --- "Barcha mijozlar" → guruhlarni o'chirish ---
  var allChk = document.getElementById("id_send_to_all_customers");
  var tagsWrap = document.getElementById("sms-tags-wrap");
  function toggleTags() {
    if (!allChk || !tagsWrap) return;
    var on = allChk.checked;
    tagsWrap.classList.toggle("opacity-50", on);
    var boxes = tagsWrap.querySelectorAll('input[type="checkbox"]');
    Array.prototype.forEach.call(boxes, function (b) {
      b.disabled = on;
      if (on) b.checked = false;
    });
  }
  if (allChk) {
    allChk.addEventListener("change", toggleTags);
    toggleTags();
  }

  // --- Qo'lda raqamlar (chip) ---
  var raw = document.getElementById("id_recipients_raw");   // yashirin textarea
  var numInput = document.getElementById("sms-num-input");
  var numAdd = document.getElementById("sms-num-add");
  var chips = document.getElementById("sms-num-chips");
  var numbers = [];

  if (raw) raw.hidden = true;  // textarea yashirin — chip orqali boshqariladi

  function syncRaw() {
    if (raw) raw.value = numbers.join("\n");
  }

  function renderChips() {
    if (!chips) return;
    chips.innerHTML = "";
    numbers.forEach(function (num, i) {
      var chip = document.createElement("span");
      chip.className = "badge bg-light text-dark border d-inline-flex align-items-center gap-1 p-2";
      chip.textContent = num;
      var x = document.createElement("button");
      x.type = "button";
      x.className = "btn-close btn-close-sm";
      x.style.fontSize = "0.6rem";
      x.setAttribute("aria-label", "O'chirish");
      x.addEventListener("click", function () {
        numbers.splice(i, 1);
        renderChips();
        syncRaw();
      });
      chip.appendChild(x);
      chips.appendChild(chip);
    });
  }

  function addNumber(value) {
    var v = (value || "").trim();
    if (!v) return;
    if (numbers.indexOf(v) === -1) numbers.push(v);
    renderChips();
    syncRaw();
  }

  // IMask instansiyasi (phone-mask.js o'rnatadi) — to'liqlikni tekshirish/tozalash uchun.
  function mask() { return numInput && numInput._imask; }

  // Joriy kiritmani qo'shadi. To'liq O'zbekiston raqami (12 raqam) bo'lsagina.
  function commitInput() {
    var m = mask();
    var digits = m ? m.unmaskedValue : (numInput.value || "").replace(/\D/g, "");
    if (digits.length < 12) {
      numInput.classList.add("is-invalid");
      return;
    }
    numInput.classList.remove("is-invalid");
    addNumber(m ? m.value : numInput.value);
    if (m) { m.value = ""; } else { numInput.value = ""; }
    numInput.focus();
  }

  // Mavjud kampaniya: textarea'dagi raqamlarni chip'larga yuklash.
  if (raw && raw.value.trim()) {
    raw.value.split(/[\s,;]+/).forEach(function (p) {
      var v = p.trim();
      if (v && numbers.indexOf(v) === -1) numbers.push(v);
    });
    renderChips();
    syncRaw();
  }

  if (numAdd) {
    numAdd.addEventListener("click", commitInput);
  }
  if (numInput) {
    numInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        commitInput();
      }
    });
    numInput.addEventListener("input", function () {
      numInput.classList.remove("is-invalid");
    });
  }

  // --- Vaqt: "Hozir" / "Vaqtni tanlash" ---
  var wrap = document.getElementById("sms-schedule-wrap");
  var radios = document.querySelectorAll('#sms-when input[name="when"]');
  function toggleSchedule() {
    var val = "";
    Array.prototype.forEach.call(radios, function (r) { if (r.checked) val = r.value; });
    if (wrap) wrap.classList.toggle("d-none", val !== "schedule");
  }
  Array.prototype.forEach.call(radios, function (r) {
    r.addEventListener("change", toggleSchedule);
  });
  toggleSchedule();
})();
