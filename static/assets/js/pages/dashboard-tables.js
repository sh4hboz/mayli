/* ==========================================================================
   dashboard-tables.js — Universal jadval (DataTables) init
   --------------------------------------------------------------------------
   Har bir `table.js-datatable` ga client-side DataTables qo'shadi:
   qidiruv + ustun bo'yicha saralash + sahifalash + responsive.

   Shablon tomonidan boshqarish (faqat data-* atributlar, inline JS yo'q):
     <table class="... js-datatable" data-dt-order="5:desc" data-dt-page-length="25">
     <th data-orderable="false">      → ustunni saralanmaydigan qiladi
     <th data-searchable="false">     → ustunni qidiruvdan chiqaradi
   "Bo'sh" holat qatori (<td colspan=...>) bo'lsa init O'TKAZIB YUBORILADI.
   ========================================================================== */
(function () {
  "use strict";

  if (typeof window.jQuery === "undefined" || !window.jQuery.fn || !window.jQuery.fn.DataTable) {
    return;
  }
  var $ = window.jQuery;

  // O'zbekcha til satrlari
  var LANG = {
    sProcessing: "Yuklanmoqda...",
    sLengthMenu: "_MENU_ ta ko'rsatish",
    sZeroRecords: "Hech narsa topilmadi",
    sEmptyTable: "Ma'lumot yo'q",
    sInfo: "_TOTAL_ tadan _START_–_END_ ko'rsatilmoqda",
    sInfoEmpty: "0 ta yozuv",
    sInfoFiltered: "(_MAX_ tadan filtrlandi)",
    sSearch: "Qidirish:",
    sSearchPlaceholder: "yozing...",
    oPaginate: { sFirst: "Birinchi", sLast: "Oxirgi", sNext: "Keyingi", sPrevious: "Oldingi" },
    oAria: { sSortAscending: ": o'sish bo'yicha saralash", sSortDescending: ": kamayish bo'yicha saralash" },
  };

  function isEmptyPlaceholder(table) {
    var body = table.tBodies && table.tBodies[0];
    if (!body) return true;
    if (body.rows.length === 0) return true;
    // {% empty %} holatda bitta `<td colspan>` qatori bo'ladi — DataTables uni buzadi.
    return body.rows.length === 1 && !!body.rows[0].querySelector("td[colspan]");
  }

  function buildColumnDefs(table) {
    var defs = [];
    var ths = table.querySelectorAll("thead th");
    ths.forEach(function (th, i) {
      var def = { targets: i };
      var touched = false;
      if (th.dataset.orderable === "false") { def.orderable = false; touched = true; }
      if (th.dataset.searchable === "false") { def.searchable = false; touched = true; }
      if (touched) defs.push(def);
    });
    return defs;
  }

  function parseOrder(table) {
    // data-dt-order="5:desc" (yoki "5"); aniqlanmasa DataTables default (0:asc).
    var raw = table.getAttribute("data-dt-order");
    if (!raw) return null;
    var parts = raw.split(":");
    var col = parseInt(parts[0], 10);
    if (isNaN(col)) return null;
    var dir = (parts[1] || "asc").toLowerCase() === "desc" ? "desc" : "asc";
    return [[col, dir]];
  }

  document.querySelectorAll("table.js-datatable").forEach(function (table) {
    if (isEmptyPlaceholder(table)) return;
    if ($.fn.dataTable.isDataTable(table)) return;

    var pageLen = parseInt(table.getAttribute("data-dt-page-length"), 10);
    if (isNaN(pageLen)) pageLen = 25;

    var opts = {
      language: LANG,
      responsive: true,
      pageLength: pageLen,
      lengthMenu: [10, 25, 50, 100],
      columnDefs: buildColumnDefs(table),
      // search + length yuqorida, info + paginate pastda (bootstrap5 standart)
      dom: "<'row mb-2'<'col-sm-6'l><'col-sm-6'f>>" +
           "<'row'<'col-12'tr>>" +
           "<'row mt-2'<'col-sm-5'i><'col-sm-7'p>>",
    };

    var order = parseOrder(table);
    if (order) opts.order = order;

    $(table).DataTable(opts);
  });
})();
