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

  // O'zbekcha til satrlari (DataTables 2.x format — camelCase)
  var LANG = {
    processing: "Yuklanmoqda...",
    lengthMenu: "_MENU_ ta ko'rsatish",
    zeroRecords: "Hech narsa topilmadi",
    emptyTable: "Ma'lumot yo'q",
    info: "_TOTAL_ tadan _START_–_END_ ko'rsatilmoqda",
    infoEmpty: "0 ta yozuv",
    infoFiltered: "(_MAX_ tadan filtrlandi)",
    search: "Qidirish:",
    searchPlaceholder: "yozing...",
    paginate: { first: "Birinchi", last: "Oxirgi", next: "Keyingi", previous: "Oldingi" },
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
      pageLength: pageLen,
      lengthMenu: [10, 25, 50, 100],
      columnDefs: buildColumnDefs(table),
      // Layout — DataTables 2.x standart (tema app.min.css dt-* ni stillaydi).
    };

    var order = parseOrder(table);
    if (order) opts.order = order;

    var dt = $(table).DataTable(opts);
    buildColumnFilters(table, dt);
  });

  // Ustun-darajasidagi filtrlar (th data-dt-filter="text|select|contains").
  // thead'ga ikkinchi qator qo'shadi: text=qidiruv inputi, select=aniq moslik dropdown,
  // contains=ichida-bor moslik dropdown (ko'p qiymatli ustun — masalan kategoriya).
  function buildColumnFilters(table, dt) {
    var ths = table.querySelectorAll("thead tr th");
    var hasFilter = Array.prototype.some.call(ths, function (th) { return th.dataset.dtFilter; });
    if (!hasFilter) return;

    var row = document.createElement("tr");
    row.className = "dt-filter-row";

    Array.prototype.forEach.call(ths, function (th, i) {
      var cell = document.createElement("th");
      var type = th.dataset.dtFilter;

      if (type === "text") {
        var inp = document.createElement("input");
        inp.type = "search";
        inp.className = "form-control form-control-sm";
        inp.placeholder = "Qidirish...";
        inp.addEventListener("keyup", function () { dt.column(i).search(this.value).draw(); });
        inp.addEventListener("click", function (e) { e.stopPropagation(); });
        cell.appendChild(inp);
      } else if (type === "select" || type === "contains") {
        var sel = document.createElement("select");
        sel.className = "form-select form-select-sm";
        var first = document.createElement("option");
        first.value = ""; first.textContent = "Barchasi";
        sel.appendChild(first);

        var values = [];
        if (th.dataset.dtOptions) {
          values = th.dataset.dtOptions.split("|");
        } else {
          dt.column(i).data().unique().sort().each(function (d) {
            var t = $("<div>").html(d).text().trim();
            if (t && values.indexOf(t) === -1) values.push(t);
          });
        }
        values.forEach(function (v) {
          if (!v) return;
          var o = document.createElement("option");
          o.value = v; o.textContent = v;
          sel.appendChild(o);
        });

        sel.addEventListener("click", function (e) { e.stopPropagation(); });
        sel.addEventListener("change", function () {
          if (!this.value) { dt.column(i).search("").draw(); return; }
          if (type === "contains") {
            dt.column(i).search(this.value, false, false).draw();           // ichida-bor
          } else {
            var esc = $.fn.dataTable.util.escapeRegex(this.value);
            dt.column(i).search("^" + esc + "$", true, false).draw();        // aniq moslik
          }
        });
        cell.appendChild(sel);
      }

      row.appendChild(cell);
    });

    table.querySelector("thead").appendChild(row);
  }
})();
