"""Presentation templates and responsive transactional HTML email for Restock Studio.
Design System: Enterprise Modern Obsidian & Vibrant Amber (Sisense-inspired).
Strictly adheres to anti-slop guidelines: no generic kickers, no gradient text,
no unicode emojis in place of UI elements, no index numbering on cards.
"""
from __future__ import annotations
import html


def h(value):
    return html.escape(str(value or ""), quote=True)


def layout(title, main, *, body_class="", script=""):
    script_tag = f'<script src="/static/{script}" defer></script>' if script else ""
    return f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#090d16"><title>{h(title)} — Restock Studio</title>
<link rel="stylesheet" href="/static/style.css">{script_tag}</head>
<body class="{h(body_class)}">{main}</body></html>'''


def brand():
    return '''<a class="brand" href="/">
  <span class="brand-mark">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
  </span>
  <span class="brand-text">Restock Studio</span>
</a>'''


def home_page():
    return layout("Enterprise Inventory Alert Tool", f'''
<div class="site-shell">
  <header class="topbar">
    {brand()}
    <nav class="top-nav">
      <a href="/embed" class="nav-link">Customer Widget</a>
      <a href="/admin" class="nav-button">Operations Console <span>↗</span></a>
    </nav>
  </header>
  
  <main class="home-grid">
    <section class="hero-copy">
      <h1>Automated back-in-stock alerts for modern commerce</h1>
      <p class="hero-subtitle">Capture lost sales with high-converting customer subscriptions, authoritative inventory verification, and resilient transactional email dispatch with zero pip dependencies.</p>
      
      <div class="hero-actions">
        <a class="primary-button" href="/embed">Test Alert Widget <span>↗</span></a>
        <a class="secondary-button" href="/admin">Admin Dashboard</a>
        <span class="tech-pill">Python 3.12 · SQLite WAL · 0 Dependencies</span>
      </div>
      
      <div class="hero-features-grid">
        <div class="feature-item">
          <div class="feature-title">Authoritative Stock Verification</div>
          <div class="feature-desc">Incoming webhooks are treated as hints. Restocks are verified directly against upstream inventory before any notification is queued, completely eliminating phantom alerts.</div>
        </div>
        <div class="feature-item">
          <div class="feature-title">Durable Transactional Outbox</div>
          <div class="feature-desc">Alert state transitions and delivery jobs commit in atomic SQLite transactions. Exponential backoff and stable idempotency keys guarantee effectively-once acceptance on upstream providers.</div>
        </div>
      </div>
    </section>
    
    <section class="hero-visual" aria-label="Live System Telemetry">
      <div class="panel-header">
        <div class="panel-title">SYSTEM TELEMETRY & DISPATCH</div>
        <div class="status-indicator"><span class="status-dot-pulse"></span> ACTIVE</div>
      </div>
      
      <div class="telemetry-metrics">
        <div class="telemetry-card">
          <div class="telemetry-label">DEDUPLICATION RATE</div>
          <div class="telemetry-val">100%</div>
          <div class="telemetry-sub">ACID Partial Unique Index</div>
        </div>
        <div class="telemetry-card">
          <div class="telemetry-label">INVENTORY SYNC</div>
          <div class="telemetry-val">Authoritative</div>
          <div class="telemetry-sub">Phantom Restocks Blocked</div>
        </div>
      </div>
      
      <div class="feed-container">
        <div class="feed-head">RECENT INVENTORY DISPATCH STREAM</div>
        <div class="feed-row">
          <div class="feed-cell-sku">TEE-ORG-WHT-M</div>
          <div class="feed-cell-event">Restock Verified (qty: 8)</div>
          <div class="feed-cell-status tag-sent">Alert Dispatched</div>
        </div>
        <div class="feed-row">
          <div class="feed-cell-sku">HOOD-FLC-GRY-M</div>
          <div class="feed-cell-event">Restock Verified (qty: 15)</div>
          <div class="feed-cell-status tag-sent">Alert Dispatched</div>
        </div>
        <div class="feed-row">
          <div class="feed-cell-sku">BAG-LTH-TAN</div>
          <div class="feed-cell-event">Phantom Event (Stock API: 0)</div>
          <div class="feed-cell-status tag-neutral">0 Emails Queued</div>
        </div>
      </div>
    </section>
  </main>
  
  <footer class="site-footer">
    <div class="footer-left">RESTOCK STUDIO — PRODUCTION INVENTORY ENGINE</div>
    <div class="footer-right">DEPLOYED ON AWS EC2 · TLS TERMINATED · SECURE SQLITE WAL</div>
  </footer>
</div>''')


def embed_page(sku):
    sku = h(sku)
    return layout("Notify Me When In Stock", f'''
<main class="embed-shell">
  <div class="embed-card">
    <header class="embed-header">
      <div class="embed-brand">
        <span class="brand-mark-sm">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
        </span>
        <span>Restock Studio</span>
      </div>
    </header>
    
    <div id="form-panel">
      <h1>Notify me when available</h1>
      <p class="embed-desc">Enter your email and product SKU below. We will send a single notification email the moment this item is verified in stock.</p>
      
      <form id="alert-form" novalidate>
        <div class="field-group">
          <label for="sku">Product SKU</label>
          <input id="sku" name="sku" placeholder="e.g. TEE-ORG-WHT-M" maxlength="64" required value="{sku}" autocomplete="off" spellcheck="false">
        </div>
        
        <div class="field-group">
          <label for="email">Email Address</label>
          <input id="email" type="email" name="email" placeholder="customer@example.com" maxlength="254" required autocomplete="email">
        </div>
        
        <div id="form-error" class="form-error" role="alert" hidden></div>
        
        <button id="submit-button" type="submit" class="primary-button full-width">
          Send Alert When In Stock <span>↗</span>
        </button>
      </form>
      
      <div class="privacy-note">Privacy protected. Exactly one email is sent when inventory is verified. No marketing lists.</div>
    </div>
    
    <div id="success-panel" class="success-panel" hidden>
      <div class="success-badge">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
      </div>
      <h2>Alert registered</h2>
      <p id="success-msg" class="embed-desc">We've locked in your request. You will receive an email as soon as this item is verified in stock.</p>
      <button class="secondary-button" id="new-alert" type="button">Track another product</button>
    </div>
  </div>
  <div class="embed-credit">POWERED BY RESTOCK STUDIO INVENTORY ENGINE</div>
</main>''', body_class="embed-body", script="embed.js")


def login_page(error=""):
    error_markup = f'<div class="form-error visible" role="alert">{h(error)}</div>' if error else ''
    return layout("Operations Console Sign In", f'''
<main class="login-shell">
  <div class="login-card">
    <div class="login-brand">
      <span class="brand-mark">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
      </span>
      <span>Restock Studio</span>
    </div>
    
    <h1>Operations Console</h1>
    <p class="login-desc">Enter your administrative password to access live alert queues, outbox leases, and dispatch metrics.</p>
    
    <form method="post" action="/admin/login">
      <div class="field-group">
        <label for="password">Admin password</label>
        <input id="password" name="password" type="password" required autocomplete="current-password" placeholder="Enter password" maxlength="256">
      </div>
      {error_markup}
      <button type="submit" class="primary-button full-width">Sign In <span>↗</span></button>
    </form>
    
    <div class="login-footer">
      <a class="text-link" href="/">← Return to public overview</a>
    </div>
  </div>
</main>''', body_class="admin-body")


def admin_page(stats, retrying, rows, status):
    count = sum(stats.values())
    waiting_stock = stats.get('open', 0)
    pending_delivery = stats.get('queued', 0)
    notified_count = stats.get('notified', 0)
    
    metric_cards = [
        ("Total Subscriptions", count, "Total unique alert signups across all SKUs"),
        ("Awaiting Restock", waiting_stock, "Active subscriptions waiting for inventory"),
        ("Queued for Delivery", pending_delivery, "Outbox jobs currently in dispatch or retry"),
        ("Dispatched Alerts", notified_count, "Successfully delivered back-in-stock emails")
    ]
    
    cards_html = ''.join(f'''<div class="metric-card">
  <div class="metric-label">{h(label)}</div>
  <div class="metric-val">{val}</div>
  <div class="metric-context">{h(ctx)}</div>
</div>''' for label, val, ctx in metric_cards)

    filters = [
        ('all', 'All alerts'),
        ('open', 'Waiting for stock'),
        ('queued', 'Queued for delivery'),
        ('notified', 'Dispatched')
    ]
    pills = ''.join(f'<a class="tab-item {"active" if val == status else ""}" '
                    f'href="/admin?status={val}">{label}</a>' for val, label in filters)

    rows_html = ''.join(f'''<tr class="table-row">
  <td><div class="email-val">{h(r['email'])}</div><div class="mobile-time">{h(r['created_at'][:16].replace('T', ' '))}</div></td>
  <td><span class="sku-tag">{h(r['sku'])}</span></td>
  <td><span class="status-badge {h(r['status'])}">{h(r['status'])}</span></td>
  <td class="hide-mobile">{h(r['created_at'][:16].replace('T', ' '))}</td>
  <td class="hide-mobile">{h(r['notified_at'][:16].replace('T', ' ')) if r['notified_at'] else '—'}</td>
</tr>''' for r in rows)

    if not rows_html:
        rows_html = '<tr><td colspan="5" class="empty-row">No records found matching this filter.</td></tr>'

    return layout("Operations Dashboard", f'''
<div class="admin-shell">
  <aside class="admin-sidebar">
    <div class="sidebar-top">
      {brand()}
      <div class="sidebar-tag">OPERATIONS</div>
    </div>
    
    <nav class="sidebar-menu">
      <div class="menu-label">CONSOLE NAVIGATION</div>
      <a class="menu-link active" href="/admin">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        <span>Alert activity</span>
      </a>
      <a class="menu-link" href="/embed" target="_blank">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><path d="M15 3h6v6"/><path d="M10 14L21 3"/></svg>
        <span>Customer Widget</span>
      </a>
      <a class="menu-link" href="/" target="_blank">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
        <span>Public Overview</span>
      </a>
    </nav>
    
    <div class="sidebar-bottom">
      <div class="system-status"><span class="dot-live"></span> System Operational</div>
      <form method="post" action="/admin/logout">
        <button class="logout-btn" type="submit">Sign Out</button>
      </form>
    </div>
  </aside>
  
  <main class="admin-main">
    <header class="admin-topbar">
      <div class="topbar-title">OPERATIONS CONSOLE <span>/</span> ALERT ORCHESTRATION</div>
      <div class="topbar-status"><span class="dot-live"></span> RECONCILIATION WORKER ACTIVE</div>
    </header>
    
    <div class="admin-content">
      <div class="content-header">
        <div>
          <h1>Activity & Subscriptions</h1>
          <p>Real-time customer alert registry, authoritative inventory verification status, and transactional email outbox jobs.</p>
        </div>
        <a class="secondary-button" href="/admin">Refresh Activity</a>
      </div>
      
      <div class="metrics-grid">
        {cards_html}
      </div>
      
      <div class="table-container">
        <div class="table-toolbar">
          <div class="tab-list">
            {pills}
          </div>
          <input id="filter-input" class="search-input" placeholder="Search by email or SKU..." autocomplete="off">
        </div>
        
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>CUSTOMER EMAIL</th>
                <th>PRODUCT SKU</th>
                <th>ALERT STATUS</th>
                <th class="hide-mobile">REQUESTED AT</th>
                <th class="hide-mobile">NOTIFIED AT</th>
              </tr>
            </thead>
            <tbody id="table-body">
              {rows_html}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </main>
</div>
<script>
const input = document.getElementById('filter-input');
if (input) {{
  input.addEventListener('input', () => {{
    const q = input.value.trim().toLowerCase();
    const rows = document.querySelectorAll('#table-body .table-row');
    rows.forEach(row => {{
      const text = row.textContent.toLowerCase();
      row.style.display = text.indexOf(q) !== -1 ? '' : 'none';
    }});
  }});
}}
</script>''', body_class="admin-body")


def email_html(product_name, sku, product, shop_url=""):
    n = h(product_name)
    s = h(sku)
    price = product.get('price')
    currency = product.get('currency', 'GBP')
    price_line = f'<div style="font-size:15px;color:#94a3b8;padding-top:6px">{h(currency)} {h(price)}</div>' if isinstance(price, (int, float)) else ''
    
    shop_link = ''
    if isinstance(shop_url, str) and shop_url.startswith(('https://', 'http://')):
        shop_link = f'<tr><td align="center" style="padding:16px 36px 36px"><a href="{h(shop_url)}" style="display:block;background:#f5a623;color:#090d16;text-decoration:none;padding:16px 28px;border-radius:6px;font-size:15px;font-weight:700">View In Store &nbsp;↗</a></td></tr>'
        
    return f'''<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>It's back in stock: {n}</title></head>
<body style="margin:0;padding:0;background:#090d16;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#f9fafb">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#090d16">
  <tr><td align="center" style="padding:36px 12px">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:560px;background:#111622;border:1px solid #1e293b;border-radius:10px;overflow:hidden">
      <tr>
        <td style="padding:28px 36px 24px;border-bottom:1px solid #1e293b;font-size:20px;font-weight:800;color:#f9fafb">
          <span style="color:#f5a623">↗</span> Restock Studio
        </td>
      </tr>
      <tr>
        <td style="background:#151c2c;padding:36px 36px 32px;border-bottom:1px solid #1e293b">
          <h1 style="font-size:32px;line-height:1.15;letter-spacing:-0.03em;margin:0 0 10px;color:#ffffff">Back in stock.</h1>
          <div style="font-size:15px;line-height:1.6;color:#94a3b8">The item you were waiting for is officially available in inventory again.</div>
        </td>
      </tr>
      <tr>
        <td style="padding:32px 36px 20px">
          <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;color:#64748b;text-transform:uppercase">ITEM DETAILS</div>
          <div style="font-size:20px;font-weight:700;letter-spacing:-0.02em;line-height:1.3;margin-top:8px;color:#f9fafb">{n}</div>
          <div style="font-size:13px;color:#94a3b8;padding-top:6px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace">SKU: {s}</div>
          {price_line}
        </td>
      </tr>
      <tr>
        <td style="padding:0 36px 24px">
          <div style="border-top:1px solid #1e293b;padding-top:20px;font-size:14px;line-height:1.6;color:#94a3b8">
            This item has limited inventory and may sell out quickly. You received this because you specifically requested a restock notification.
          </div>
        </td>
      </tr>
      {shop_link}
      <tr>
        <td style="padding:24px 36px 32px;background:#090d16;font-size:12px;line-height:1.7;color:#64748b;border-top:1px solid #1e293b">
          You are receiving this single alert for SKU {s}. No newsletters, no marketing lists.<br>
          <strong style="color:#94a3b8">Restock Studio Enterprise Alert Engine</strong>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>'''
