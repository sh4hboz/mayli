/* phone-mask.js — dashboard telefon inputlariga O'zbekiston mask (saytdagi kabi).
   IMask: +998 (XX) XXX-XX-XX. input[type=tel] yoki input[name=phone] ga ulanadi. */
(function () {
  if (typeof IMask === "undefined") return;
  var els = document.querySelectorAll('input[type="tel"], input[name="phone"]');
  Array.prototype.forEach.call(els, function (el) {
    if (el.dataset.maskInit) return;
    el.dataset.maskInit = "1";
    // Instansiyani elementga saqlaymiz — boshqa skriptlar tozalash/o'qish uchun ishlatadi.
    el._imask = IMask(el, { mask: "+{998} (00) 000-00-00", lazy: false });
  });
})();
