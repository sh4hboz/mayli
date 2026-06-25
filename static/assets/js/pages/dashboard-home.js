/* Dashboard home — analitika grafiklari (ApexCharts).
   Ma'lumotlar json_script orqali keladi: #dashboard-analytics-data. */
(function () {
  var el = document.getElementById('dashboard-analytics-data');
  if (!el || typeof ApexCharts === 'undefined') return;

  var data;
  try { data = JSON.parse(el.textContent); } catch (e) { return; }

  // 1) Oylik yangi mijozlar — area
  var m = data.monthly;
  if (m && document.querySelector('#chartMonthlyCustomers')) {
    new ApexCharts(document.querySelector('#chartMonthlyCustomers'), {
      chart: { type: 'area', height: 300, toolbar: { show: false } },
      series: [{ name: 'Yangi mijozlar', data: m.data }],
      xaxis: { categories: m.labels },
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth', width: 2 },
      colors: ['#ea6900'],
      fill: { type: 'gradient', gradient: { opacityFrom: 0.4, opacityTo: 0.05 } },
      grid: { borderColor: 'rgba(128,128,128,0.15)' }
    }).render();
  }

  // 2) Mijoz manbalari — donut
  var s = data.sources;
  if (s && s.data && s.data.length && document.querySelector('#chartSources')) {
    new ApexCharts(document.querySelector('#chartSources'), {
      chart: { type: 'donut', height: 300 },
      series: s.data,
      labels: s.labels,
      legend: { position: 'bottom' },
      dataLabels: { enabled: true },
      colors: ['#ea6900', '#3b82f6', '#22c55e', '#a855f7', '#eab308', '#64748b']
    }).render();
  }

  // 3) Kampaniya samarasi — stacked bar
  var c = data.campaigns;
  if (c && c.labels && c.labels.length && document.querySelector('#chartCampaigns')) {
    new ApexCharts(document.querySelector('#chartCampaigns'), {
      chart: { type: 'bar', height: 300, stacked: true, toolbar: { show: false } },
      series: [
        { name: 'Yuborildi', data: c.sent },
        { name: 'Xato', data: c.failed }
      ],
      xaxis: { categories: c.labels },
      plotOptions: { bar: { columnWidth: '45%', borderRadius: 3 } },
      dataLabels: { enabled: false },
      legend: { position: 'top' },
      colors: ['#22c55e', '#ef4444'],
      grid: { borderColor: 'rgba(128,128,128,0.15)' }
    }).render();
  }

  // 4) Buyurtma dinamikasi va daromad — bar (soni) + line (daromad), 2 o'q
  var o = data.orders;
  if (o && o.labels && o.labels.length && document.querySelector('#chartOrders')) {
    new ApexCharts(document.querySelector('#chartOrders'), {
      chart: { height: 300, type: 'line', stacked: false, toolbar: { show: false } },
      series: [
        { name: 'Buyurtmalar', type: 'column', data: o.counts },
        { name: "Daromad (so'm)", type: 'line', data: o.revenue }
      ],
      stroke: { width: [0, 3], curve: 'smooth' },
      plotOptions: { bar: { columnWidth: '45%', borderRadius: 3 } },
      dataLabels: { enabled: false },
      xaxis: { categories: o.labels },
      yaxis: [
        { title: { text: 'Buyurtmalar' }, labels: { formatter: function (v) { return Math.round(v); } } },
        { opposite: true, title: { text: 'Daromad' }, labels: { formatter: function (v) { return Math.round(v).toLocaleString('ru-RU'); } } }
      ],
      legend: { position: 'top' },
      colors: ['#ea6900', '#22c55e'],
      grid: { borderColor: 'rgba(128,128,128,0.15)' }
    }).render();
  }

  // 5) Buyurtma holatlari — donut
  var os = data.order_statuses;
  if (os && os.data && os.data.length && document.querySelector('#chartOrderStatuses')) {
    new ApexCharts(document.querySelector('#chartOrderStatuses'), {
      chart: { type: 'donut', height: 300 },
      series: os.data,
      labels: os.labels,
      legend: { position: 'bottom' },
      dataLabels: { enabled: true },
      colors: ['#3b82f6', '#eab308', '#22c55e', '#ef4444', '#64748b']
    }).render();
  }
})();
