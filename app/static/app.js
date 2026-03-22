// app.js — global utilities

function fmt(v, dec = 2) {
  return parseFloat(v || 0).toLocaleString('tr-TR', {
    minimumFractionDigits: dec, maximumFractionDigits: dec
  });
}
function fmtTL(v) { return fmt(v) + ' ₺'; }

function toast(msg, type = 'info', ms = 3000) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `show ${type}`;
  setTimeout(() => { el.className = ''; }, ms);
}

function confirm2(msg) { return window.confirm(msg); }

async function del(url, rowId) {
  if (!confirm2('Silinsin mi?')) return false;
  const d = await requestJson(url, 'DELETE');
  if (d.ok) {
    const row = document.getElementById(rowId);
    if (row) row.remove();
    toast('Silindi ✓', 'success');
  }
  return d.ok;
}

async function requestJson(url, method = 'GET', body = null) {
  const opts = { method, headers: {} };
  if (body !== null) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  try {
    const r = await fetch(url, opts);
    const text = await r.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch (_) { data = {}; }
    if (!r.ok && !data.error) data.error = `HTTP ${r.status}`;
    if (data.ok === undefined) data.ok = r.ok;
    return data;
  } catch (e) {
    return { ok: false, error: 'Ağ hatası' };
  }
}

async function post(url, body) {
  return requestJson(url, 'POST', body);
}

async function put(url, body) {
  return requestJson(url, 'PUT', body);
}

async function patch(url, body) {
  return requestJson(url, 'PATCH', body);
}

// Animate progress bars on load
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.progress-fill[data-w]').forEach(el => {
    const w = el.dataset.w;
    el.style.width = '0%';
    setTimeout(() => { el.style.width = w; }, 80);
  });

  const aiInput = document.getElementById('aiPopupInput');
  if (aiInput) {
    aiInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendAiPopupMessage();
      }
    });
    aiInput.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 130) + 'px';
    });
  }

  const aiOverlay = document.getElementById('aiPopup');
  if (aiOverlay) {
    aiOverlay.addEventListener('click', (e) => {
      if (e.target === aiOverlay) closeAiPopup();
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAiPopup();
  });
});

function openAiPopup() {
  const popup = document.getElementById('aiPopup');
  if (!popup) return;
  popup.classList.add('show');
  popup.setAttribute('aria-hidden', 'false');
  loadAiPopupHistory();
  const input = document.getElementById('aiPopupInput');
  if (input) input.focus();
}

function closeAiPopup() {
  const popup = document.getElementById('aiPopup');
  if (!popup) return;
  popup.classList.remove('show');
  popup.setAttribute('aria-hidden', 'true');
}

function aiPopupMsg(role, text, markdown = false) {
  const box = document.getElementById('aiPopupMessages');
  if (!box) return;
  const row = document.createElement('div');
  row.className = `ai-popup-msg ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  if (markdown && typeof marked !== 'undefined') bubble.innerHTML = marked.parse(text || '');
  else bubble.textContent = text || '';
  row.appendChild(bubble);
  box.appendChild(row);
  box.scrollTop = box.scrollHeight;
}

async function loadAiPopupHistory() {
  const box = document.getElementById('aiPopupMessages');
  if (!box || box.dataset.loaded === '1') return;
  box.innerHTML = '';
  aiPopupMsg('ai', 'Merhaba, finansal bir soru yazabilirsin. Uygun komutları otomatik olarak ilgili bölümlere işlerim.');
  try {
    const r = await fetch('/api/ai/gecmis');
    const d = await r.json();
    if (d.ok && Array.isArray(d.items) && d.items.length) {
      box.innerHTML = '';
      d.items.forEach(i => {
        aiPopupMsg('user', i.soru);
        aiPopupMsg('ai', i.cevap, true);
      });
    }
  } catch (e) {}
  box.dataset.loaded = '1';
}

async function sendAiPopupMessage() {
  const input = document.getElementById('aiPopupInput');
  const btn = document.getElementById('aiPopupSend');
  if (!input || !btn) return;
  const soru = (input.value || '').trim();
  if (!soru) return;

  aiPopupMsg('user', soru);
  input.value = '';
  input.style.height = '42px';
  btn.disabled = true;

  try {
    const d = await post('/api/ai/chat', { soru });
    if (d.ok && d.cevap) aiPopupMsg('ai', d.cevap, true);
    else aiPopupMsg('ai', 'Üzgünüm, yanıt alınamadı.');
  } catch (e) {
    aiPopupMsg('ai', 'Bağlantı hatası oluştu.');
  }
  btn.disabled = false;
}

async function clearAiPopupHistory() {
  try {
    const d = await post('/api/ai/chat/temizle', {});
    if (d.ok) {
      const box = document.getElementById('aiPopupMessages');
      if (box) {
        box.dataset.loaded = '0';
        box.innerHTML = '';
      }
      await loadAiPopupHistory();
      toast('AI geçmişi temizlendi ✓', 'success');
    }
  } catch (e) {
    toast('Temizleme başarısız', 'error');
  }
}
