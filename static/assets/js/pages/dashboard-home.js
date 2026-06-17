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
})();
