/* ==========================================================================
   sms-campaign.js — Soddalashtirilgan SMS yuborgich (dashboard)
   - Shablon tugmasini bosish → yashirin sms_template_id + matn preview to'ladi.
   - "Hozir / Vaqtni tanlash" radiosi → sana maydonini ko'rsatadi/yashiradi.
   ========================================================================== */
(function () {
  "use strict";

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

  // Tahrirlash rejimi: joriy shablon tugmasini belgilab qo'yamiz.
  if (hidden && hidden.value) {
    Array.prototype.forEach.call(buttons, function (btn) {
      if (btn.getAttribute("data-id") === hidden.value) btn.classList.add("active");
    });
  }

  // Vaqt: "Hozir" / "Vaqtni tanlash"
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
