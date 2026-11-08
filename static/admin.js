(() => {
  const input = document.getElementById('filter-input');
  
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

  // Poll every 2.5 seconds
  setInterval(autoSync, 2500);
})();
