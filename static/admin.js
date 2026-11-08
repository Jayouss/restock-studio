(() => {
  const input = document.getElementById('filter-input');
  const soundBtn = document.getElementById('sound-toggle');
  const soundLabel = document.getElementById('sound-label');

  let audioCtx = null;
  let soundEnabled = localStorage.getItem('restock_sound_enabled') !== 'false';

  function updateSoundUI() {
    if (!soundBtn || !soundLabel) return;
    if (soundEnabled) {
      soundBtn.classList.remove('muted');
      soundBtn.setAttribute('aria-pressed', 'true');
      soundLabel.textContent = 'Audio alert on';
    } else {
      soundBtn.classList.add('muted');
      soundBtn.setAttribute('aria-pressed', 'false');
      soundLabel.textContent = 'Audio alert off';
    }
  }
  updateSoundUI();

  function getAudioContext() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  // Unlock audio on first user click or key anywhere on page
  const unlockAudio = () => {
    getAudioContext();
    document.removeEventListener('click', unlockAudio);
    document.removeEventListener('keydown', unlockAudio);
  };
  document.addEventListener('click', unlockAudio);
  document.addEventListener('keydown', unlockAudio);

  function playChime() {
    if (!soundEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const now = ctx.currentTime;

      // Note 1: E5 (659.25 Hz)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(659.25, now);
      gain1.gain.setValueAtTime(0.09, now);
      gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.3);

      // Note 2: A5 (880 Hz)
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(880, now + 0.09);
      gain2.gain.setValueAtTime(0.12, now + 0.09);
      gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.09);
      osc2.stop(now + 0.45);
    } catch (e) {
      // Audio not permitted or not supported
    }
  }

  if (soundBtn) {
    soundBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      soundEnabled = !soundEnabled;
      localStorage.setItem('restock_sound_enabled', String(soundEnabled));
      updateSoundUI();
      if (soundEnabled) {
        getAudioContext();
        playChime();
      }
    });
  }

  function applyFilter() {
    if (!input) return;
    const q = input.value.trim().toLowerCase();
    const rows = document.querySelectorAll('#table-body .table-row');
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.indexOf(q) !== -1 ? '' : 'none';
    });
  }

  if (input) {
    input.addEventListener('input', applyFilter);
  }

  function getRowSignature(row) {
    const email = row.querySelector('.email-val')?.textContent.trim() || '';
    const sku = row.querySelector('.sku-tag')?.textContent.trim() || '';
    const time = row.querySelector('.mobile-time')?.textContent.trim() || '';
    return `${email}|${sku}|${time}`;
  }

  const knownSignatures = new Set();
  document.querySelectorAll('#table-body .table-row').forEach(row => {
    const sig = getRowSignature(row);
    if (sig) knownSignatures.add(sig);
  });

  function getTotalSubscriptions() {
    const firstMetric = document.querySelector('.metrics-grid .metric-card .metric-val');
    return firstMetric ? parseInt(firstMetric.textContent.replace(/,/g, ''), 10) || 0 : 0;
  }
  let lastTotalCount = getTotalSubscriptions();

  async function autoSync() {
    // If user is actively typing in the search box, do not interrupt
    if (input && document.activeElement === input && input.value.trim().length > 0) {
      return;
    }

    try {
      const res = await fetch(window.location.href, {
        headers: { 'Cache-Control': 'no-cache' }
      });
      if (!res.ok) return;

      const htmlText = await res.text();
      const doc = new DOMParser().parseFromString(htmlText, 'text/html');

      // Check if new items arrived
      const newFirstMetric = doc.querySelector('.metrics-grid .metric-card .metric-val');
      const newTotalCount = newFirstMetric ? parseInt(newFirstMetric.textContent.replace(/,/g, ''), 10) || 0 : 0;

      const newRows = Array.from(doc.querySelectorAll('#table-body .table-row'));
      let hasNewItem = false;

      if (newTotalCount > lastTotalCount) {
        hasNewItem = true;
      }

      newRows.forEach(row => {
        const sig = getRowSignature(row);
        if (sig && !knownSignatures.has(sig)) {
          hasNewItem = true;
          row.classList.add('row-highlight');
          knownSignatures.add(sig);
        }
      });

      if (hasNewItem) {
        lastTotalCount = Math.max(lastTotalCount, newTotalCount);
        playChime();
      }

      // Update metric cards
      const newMetrics = doc.querySelector('.metrics-grid');
      const oldMetrics = document.querySelector('.metrics-grid');
      if (newMetrics && oldMetrics) {
        oldMetrics.innerHTML = newMetrics.innerHTML;
      }

      // Update table body
      const newTbody = doc.getElementById('table-body');
      const oldTbody = document.getElementById('table-body');
      if (newTbody && oldTbody) {
        if (oldTbody.innerHTML !== newTbody.innerHTML) {
          oldTbody.innerHTML = newTbody.innerHTML;
          applyFilter();
        }
      }

      // Update live status pulse in topbar
      const statusEl = document.querySelector('.topbar-status');
      if (statusEl) {
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        statusEl.innerHTML = '<span class="dot-live"></span> Live sync active · ' + now;
      }
    } catch (e) {
      // Network retry on next tick
    }
  }

  // Poll every 2 seconds for instantaneous updates without refresh
  setInterval(autoSync, 2000);

  // Sync immediately when returning to tab
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      autoSync();
    }
  });
})();