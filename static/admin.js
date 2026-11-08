(() => {
  const input = document.getElementById('filter-input');
  const soundBtn = document.getElementById('sound-toggle');
  const soundLabel = document.getElementById('sound-label');
  const exportBtn = document.getElementById('btn-export-csv');
  const tabLinks = document.querySelectorAll('.tab-item');
  const tbody = document.getElementById('table-body');

  let audioCtx = null;
  let soundEnabled = localStorage.getItem('restock_sound_enabled') !== 'false';
  let currentTabStatus = new URLSearchParams(window.location.search).get('status') || 'all';

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

  function formatNYTime() {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      timeZoneName: 'short'
    }).format(new Date());
  }

  const statusEl = document.querySelector('.topbar-status');
  function updateLiveStatus() {
    if (statusEl) {
      statusEl.innerHTML = '<span class="dot-live"></span> Live sync active · ' + formatNYTime();
    }
  }
  updateLiveStatus();

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

  // Unlock audio on first user gesture anywhere
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
    const q = input ? input.value.trim().toLowerCase() : '';
    const rows = document.querySelectorAll('#table-body .table-row');
    rows.forEach(row => {
      const rowStatus = row.getAttribute('data-status') || '';
      const text = row.textContent.toLowerCase();
      const matchesTab = (currentTabStatus === 'all' || rowStatus === currentTabStatus);
      const matchesSearch = !q || text.indexOf(q) !== -1;
      
      if (matchesTab && matchesSearch) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
        const inspectBtn = row.querySelector('.btn-inspect');
        const detailsId = inspectBtn?.getAttribute('data-target');
        if (detailsId) {
          const detailsRow = document.getElementById(detailsId);
          if (detailsRow) {
            detailsRow.hidden = true;
            if (inspectBtn) inspectBtn.textContent = 'Details ▾';
          }
        }
      }
    });
  }

  if (input) {
    input.addEventListener('input', applyFilter);
  }

  function applyTab(status, pushState = true) {
    currentTabStatus = status;
    tabLinks.forEach(t => {
      const href = t.getAttribute('href') || '';
      const s = new URLSearchParams(href.split('?')[1] || '').get('status') || 'all';
      if (s === status) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });
    if (exportBtn) {
      exportBtn.setAttribute('href', `/admin/export.csv?status=${encodeURIComponent(status)}`);
    }
    if (pushState) {
      history.pushState(null, '', `/admin?status=${encodeURIComponent(status)}`);
    }
    applyFilter();
  }

  tabLinks.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const href = tab.getAttribute('href') || '';
      const s = new URLSearchParams(href.split('?')[1] || '').get('status') || 'all';
      applyTab(s, true);
    });
  });

  window.addEventListener('popstate', () => {
    const s = new URLSearchParams(window.location.search).get('status') || 'all';
    applyTab(s, false);
  });

  // Delegate Row Inspector and Cancel Actions
  if (tbody) {
    tbody.addEventListener('click', async (e) => {
      // Toggle Inspector
      const inspectBtn = e.target.closest('.btn-inspect');
      if (inspectBtn) {
        const targetId = inspectBtn.getAttribute('data-target');
        const targetRow = document.getElementById(targetId);
        if (targetRow) {
          targetRow.hidden = !targetRow.hidden;
          inspectBtn.textContent = targetRow.hidden ? 'Details ▾' : 'Hide ▴';
        }
        return;
      }

      // Cancel Alert Action
      const cancelBtn = e.target.closest('.btn-cancel-alert');
      if (cancelBtn) {
        const reqId = cancelBtn.getAttribute('data-id');
        if (!reqId) return;
        if (!confirm('Cancel this back-in-stock alert subscription?')) return;
        cancelBtn.disabled = true;
        cancelBtn.textContent = 'Cancelling…';
        try {
          const res = await fetch('/admin/requests/cancel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: Number(reqId) })
          });
          const data = await res.json();
          if (res.ok && data.ok) {
            const mainRow = document.querySelector(`.table-row[data-id="${reqId}"]`);
            if (mainRow) {
              mainRow.setAttribute('data-status', 'cancelled');
              const badge = mainRow.querySelector('.status-badge');
              if (badge) {
                badge.className = 'status-badge cancelled';
                badge.textContent = 'Cancelled';
              }
            }
            const detailsRow = document.getElementById(`details-${reqId}`);
            if (detailsRow) {
              const stageVal = detailsRow.querySelector('.inspector-item:nth-child(4) .inspector-val');
              if (stageVal) stageVal.textContent = 'Alert Cancelled';
              cancelBtn.remove();
            }
            applyFilter();
          } else {
            alert(data.error || 'Could not cancel alert.');
            cancelBtn.disabled = false;
            cancelBtn.textContent = 'Cancel and remove from waitlist';
          }
        } catch (err) {
          alert('Network error. Could not cancel alert.');
          cancelBtn.disabled = false;
          cancelBtn.textContent = 'Cancel and remove from waitlist';
        }
      }
    });
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
    // If user is actively typing in search, do not interrupt
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

      // Record which details rows were open
      const openDetailIds = new Set(
        Array.from(document.querySelectorAll('.details-row:not([hidden])')).map(r => r.id)
      );

      // Update table body
      const newTbody = doc.getElementById('table-body');
      const oldTbody = document.getElementById('table-body');
      if (newTbody && oldTbody) {
        if (oldTbody.innerHTML !== newTbody.innerHTML) {
          oldTbody.innerHTML = newTbody.innerHTML;
          // Restore open details
          openDetailIds.forEach(id => {
            const restored = document.getElementById(id);
            if (restored) {
              restored.hidden = false;
              const parentRow = restored.previousElementSibling;
              const btn = parentRow?.querySelector('.btn-inspect');
              if (btn) btn.textContent = 'Hide ▴';
            }
          });
          applyFilter();
        }
      }

      // Update live status pulse in topbar
      updateLiveStatus();
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

  // Initial tab filter setup
  applyTab(currentTabStatus, false);
})();
