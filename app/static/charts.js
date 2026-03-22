// charts.js — Chart.js 4 configuration for BütçePlan

const C = {
  bg:      '#1c1b18',
  surface: '#252420',
  border:  '#3d3a34',
  text:    '#ede9e3',
  muted:   '#a09a8e',
  accent:  '#df7b4a',
  green:   '#4ade80',
  red:     '#f87171',
  blue:    '#60a5fa',
  purple:  '#c084fc',
  yellow:  '#fbbf24',
  cyan:    '#22d3ee',
};

if (typeof Chart !== 'undefined') {
  Chart.defaults.color           = C.muted;
  Chart.defaults.borderColor     = C.border;
  Chart.defaults.font.family     = "'Inter', sans-serif";
  Chart.defaults.font.size       = 12;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding       = 14;
  Chart.defaults.plugins.tooltip.backgroundColor     = C.surface;
  Chart.defaults.plugins.tooltip.borderColor         = C.border;
  Chart.defaults.plugins.tooltip.borderWidth         = 1;
  Chart.defaults.plugins.tooltip.padding             = 10;
  Chart.defaults.plugins.tooltip.titleColor          = C.text;
  Chart.defaults.plugins.tooltip.bodyColor           = C.muted;
  Chart.defaults.plugins.tooltip.cornerRadius        = 8;
}

/* ─── Helper ─────────────────────────────────────────────────────── */
function hexAlpha(hex, a) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}

/* ─── Monthly Income vs Expense Bar Chart ───────────────────────── */
async function initMonthlyChart(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  try {
    const res  = await fetch('/api/grafik/aylik');
    const data = await res.json();
    const labels = data.map(d => d.ay);
    new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Gelir',
            data: data.map(d => d.gelir),
            backgroundColor: hexAlpha(C.green, .75),
            borderColor: C.green,
            borderWidth: 1.5,
            borderRadius: 5,
          },
          {
            label: 'Gider',
            data: data.map(d => d.gider),
            backgroundColor: hexAlpha(C.red, .75),
            borderColor: C.red,
            borderWidth: 1.5,
            borderRadius: 5,
          },
          {
            label: 'Kalan',
            data: data.map(d => d.kalan),
            backgroundColor: hexAlpha(C.accent, .7),
            borderColor: C.accent,
            borderWidth: 1.5,
            borderRadius: 5,
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: {
          x: { grid: { color: hexAlpha(C.border, .5) } },
          y: {
            grid: { color: hexAlpha(C.border, .5) },
            ticks: {
              callback: v => v.toLocaleString('tr-TR') + ' ₺'
            }
          }
        }
      }
    });
  } catch(e) { console.error('Monthly chart error:', e); }
}

/* ─── Expense Breakdown Donut ─────────────────────────────────────── */
async function initExpenseChart(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  try {
    const res  = await fetch('/api/grafik/gider-dagilimi');
    const data = await res.json();
    if (!data.labels.length) {
      canvas.parentElement.innerHTML = '<p class="center muted" style="padding:2rem">Bu ay gider kaydı yok</p>';
      return;
    }
    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.values,
          backgroundColor: data.colors.map(c => hexAlpha(c, .85)),
          borderColor: data.colors,
          borderWidth: 1.5,
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { position: 'right' },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.raw.toLocaleString('tr-TR', {minimumFractionDigits:2})} ₺`
            }
          }
        }
      }
    });
  } catch(e) { console.error('Expense chart error:', e); }
}

/* ─── Investment Portfolio Donut ─────────────────────────────────── */
async function initPortfolioChart(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  try {
    const res  = await fetch('/api/grafik/yatirim');
    const data = await res.json();
    if (!data.labels.length) {
      canvas.parentElement.innerHTML = '<p class="center muted" style="padding:2rem">Yatırım kaydı yok</p>';
      return;
    }
    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.values,
          backgroundColor: data.colors.map(c => hexAlpha(c, .85)),
          borderColor: data.colors,
          borderWidth: 1.5,
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { position: 'right' },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.raw.toLocaleString('tr-TR', {minimumFractionDigits:2})} ₺`
            }
          }
        }
      }
    });
  } catch(e) { console.error('Portfolio chart error:', e); }
}

/* ─── Simple bar for sabit giderler ─────────────────────────────── */
function initSabitGiderChart(canvasId, labels, values, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors.map(c => hexAlpha(c, .8)),
        borderColor: colors,
        borderWidth: 1.5,
        borderRadius: 5,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: hexAlpha(C.border, .5) },
          ticks: { callback: v => v.toLocaleString('tr-TR') + ' ₺' }
        }
      }
    }
  });
}
