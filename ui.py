"""Presentation templates and a responsive transactional HTML email.
Design inspired by Sisense Intelligence: Modern Dark Slate & Vibrant Amber.
"""
from __future__ import annotations
import html


def h(value):
    return html.escape(str(value or ""), quote=True)


def layout(title, main, *, body_class="", script=""):
    script_tag = f'<script src="/static/{script}" defer></script>' if script else ""
    return f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0a0e17"><title>{h(title)} — Restock Studio</title>
<link rel="stylesheet" href="/static/style.css">{script_tag}</head>
<body class="{h(body_class)}">{main}</body></html>'''


def brand():
    return '<a class="brand" href="/"><span class="brand-mark">↗</span><span>Restock<span class="brand-dot">.</span></span></a>'


def home_page():
    return layout("Never miss a restock", f'''
<div class="site-shell">
  <header class="topbar">
    {brand()}
    <nav>
      <a href="/embed">Try Alert Widget</a>
      <a href="/admin" class="nav-button">Operations Dashboard <span>↗</span></a>
    </nav>
  </header>
  <main class="home-grid">
    <section class="hero-copy">
      <div class="eyebrow"><span class="online-dot"></span> AUTOMATED INVENTORY INTELLIGENCE</div>
      <h1>Enterprise alerts,<br><span class="gradient-text">precisely timed</span><span class="brand-dot">.</span></h1>
      <p class="hero-subtitle">Convert lost demand into captured revenue. High-converting embedded customer signups, authoritative inventory verification, and durable email delivery with zero duplicates.</p>
      <div class="hero-actions">
        <a class="primary-button" href="/embed">Launch Customer Widget <span>↗</span></a>
        <a class="nav-button" href="/admin">Admin Console <span>↗</span></a>
        <span class="quiet-note">Zero dependencies · SQLite WAL</span>
      </div>
      <div class="hero-foot">
        <div class="small-symbol">⚡</div>
        <div>
          <strong>Guaranteed Effective-Once Delivery</strong>
          <span>Idempotent Resend outbox with exponential backoff & store sync.</span>
        </div>
      </div>
    </section>
    <section class="hero-visual" aria-label="Live System Preview">
      <div class="visual-badge"><span class="online-dot"></span> LIVE RESTOCK ORCHESTRATION</div>
      <div class="visual-metric-grid">
        <div class="visual-kpi">
          <div class="visual-kpi-label">Deduplicated Alerts</div>
          <div class="visual-kpi-val">100<span style="font-size:18px;color:#f59e0b">%</span></div>
        </div>
        <div class="visual-kpi">
          <div class="visual-kpi-label">Restock Sync Time</div>
          <div class="visual-kpi-val">&lt; 1<span style="font-size:18px;color:#10b981">s</span></div>
        </div>
      </div>
      <div class="visual-feed-card">
        <div class="feed-header">
          <span>REAL-TIME INVENTORY STREAM</span>
          <span style="color:#10b981">● ACTIVE</span>
        </div>
        <div class="feed-item">
          <div><span class="feed-product">TEE-ORG-WHT-M</span> <span style="color:#94a3b8;font-size:12px;margin-left:6px">Restocked (qty: 8)</span></div>
          <span class="feed-status">✓ 1 Alert Sent</span>
        </div>
        <div class="feed-item">
          <div><span class="feed-product">HOOD-FLC-GRY-M</span> <span style="color:#94a3b8;font-size:12px;margin-left:6px">Restocked (qty: 15)</span></div>
          <span class="feed-status">✓ 1 Alert Sent</span>
        </div>
        <div class="feed-item">
          <div><span class="feed-product">BAG-LTH-TAN</span> <span style="color:#94a3b8;font-size:12px;margin-left:6px">Sold Out (qty: 0)</span></div>
          <span style="font-size:11px;color:#94a3b8">Collecting Signups</span>
        </div>
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <span>RESTOCK STUDIO © 2026 — ENTERPRISE INVENTORY ENGINE</span>
    <span>INSPIRED BY SISENSE ANALYTICS INTELLIGENCE</span>
  </footer>
</div>''')


def embed_page(sku):
    sku = h(sku)
    return layout("Get notified", f'''
<main class="embed-shell">
  <div class="embed-card">
    <div class="embed-top">
      <div class="tiny-brand"><span class="tiny-mark">↗</span> Restock<span class="brand-dot">.</span></div>
      <span class="embed-label"><span class="tiny-dot"></span> BACK IN STOCK ALERT</span>
    </div>
    
    <div id="form-panel">
      <div class="section-kicker">INSTANT NOTIFICATION</div>
      <h1>First in line.<br><span>Right on time.</span></h1>
      <p class="embed-description">We'll send you a single, perfectly timed email the moment this item returns to stock. No spam, guaranteed.</p>
      
      <form id="alert-form" novalidate>
        <label for="sku">Product SKU</label>
        <input id="sku" name="sku" placeholder="e.g. TEE-ORG-WHT-M" maxlength="64" required value="{sku}" autocomplete="off" spellcheck="false">
        
        <label for="email">Your Email Address</label>
        <input id="email" type="email" name="email" placeholder="you@company.com" maxlength="254" required autocomplete="email">
        
        <div id="form-error" class="form-error" role="alert" hidden></div>
        
        <button id="submit-button" type="submit" class="primary-button full-button">
          Notify Me When Available <span>↗</span>
        </button>
      </form>
      
      <div class="trust-line"><span>🔒</span> Exactly one alert when stock is verified. Unsubscribe anytime.</div>
    </div>
    
    <div id="success-panel" class="success-panel" hidden>
      <div class="success-icon">✓</div>
      <div class="section-kicker">CONFIRMED</div>
      <h1>You're on the list<span class="brand-dot">.</span></h1>
      <p id="success-msg" class="embed-description">We've locked in your request. You will be emailed as soon as this item is available.</p>
      <button class="text-button" id="new-alert" type="button">Track another product ↗</button>
    </div>
  </div>
  <p class="widget-credit">POWERED BY <strong>RESTOCK STUDIO ENTERPRISE</strong></p>
</main>''', body_class="embed-body", script="embed.js")


def login_page(error=""):
    error_markup = f'<p class="form-error visible">{h(error)}</p>' if error else ''
    return layout("Admin login", f'''
<main class="login-wrap">
  <div class="login-card">
    <div class="tiny-brand"><span class="tiny-mark">↗</span> Restock<span class="brand-dot">.</span></div>
    <div class="login-emblem">⚡</div>
    <div class="section-kicker">ENTERPRISE CONSOLE</div>
    <h1>Operations login<span class="brand-dot">.</span></h1>
    <p class="muted">Enter your administrative password to access live alerts and dispatch metrics.</p>
    <form method="post" action="/admin/login">
      <label for="password">Admin password</label>
      <input id="password" name="password" type="password" required autocomplete="current-password" placeholder="Enter dashboard password" maxlength="256">
      {error_markup}
      <button type="submit" class="primary-button full-button">Access Dashboard <span>↗</span></button>
    </form>
    <a class="back-link" href="/">← Return to overview</a>
  </div>
</main>''', body_class="admin-body")


def admin_page(stats, retrying, rows, status):
    count = sum(stats.values())
    waiting_stock = stats.get('open', 0)
    pending_delivery = stats.get('queued', 0)
    notified_count = stats.get('notified', 0)
    
    cards = [
        ("Total requests", count, "01"),
        ("Waiting for stock", waiting_stock, "02"),
        ("Pending delivery", pending_delivery, "03"),
        ("Emails sent", notified_count, "04")
    ]
    card_markup = ''.join(f'''<div class="stat-card">
  <div class="stat-top"><span>{h(k)}</span><span>{n}</span></div>
  <div class="stat-value">{v}</div>
  <div class="stat-rule"></div>
</div>''' for k, v, n in cards)

    filters = [
        ('all', 'All alerts'),
        ('open', 'Waiting for stock'),
        ('queued', 'Queued'),
        ('notified', 'Notified')
    ]
    pills = ''.join(f'<a class="filter-pill {"selected" if val == status else ""}" '
                    f'href="/admin?status={val}">{label}</a>' for val, label in filters)

    rows_html = ''.join(f'''<tr class="alert-row">
  <td><div class="table-email">{h(r['email'])}</div><div class="mobile-date">{h(r['created_at'][:16].replace('T', ' '))}</div></td>
  <td><span class="sku-chip">{h(r['sku'])}</span></td>
  <td><span class="status-tag {h(r['status'])}"><span class="status-dot"></span>{h(r['status'])}</span></td>
  <td class="hide-small">{h(r['created_at'][:16].replace('T', ' '))}</td>
  <td class="hide-small">{h(r['notified_at'][:16].replace('T', ' ')) if r['notified_at'] else '—'}</td>
</tr>''' for r in rows)

    if not rows_html:
        rows_html = '<tr><td colspan="5" class="empty-state">No alerts in this view yet.</td></tr>'

    return layout("Operations dashboard", f'''
<div class="dashboard-shell">
  <aside class="sidebar">
    <div class="sidebar-head">
      {brand()}
      <small>INTELLIGENCE</small>
    </div>
    <div class="sidebar-group">
      <div class="sidebar-overline">CORE OPERATIONS</div>
      <a class="sidebar-link active" href="/admin">⚡ <span>Alert Activity</span></a>
      <a class="sidebar-link" href="/embed" target="_blank">↗ <span>Customer Widget</span></a>
      <a class="sidebar-link" href="/" target="_blank">◫ <span>Public Overview</span></a>
    </div>
    <div class="sidebar-bottom">
      <span class="service-online"><span class="online-dot"></span> Live Sync Active</span>
      <form method="post" action="/admin/logout">
        <button class="logout-button" type="submit">Sign out ↗</button>
      </form>
    </div>
  </aside>
  
  <main class="dashboard-main">
    <header class="dashboard-top">
      <div class="breadcrumb">WORKSPACE <span>/</span> INVENTORY INTELLIGENCE</div>
      <div class="header-right"><span class="header-indicator">●</span> LIVE TRACKING</div>
    </header>
    
    <div class="dashboard-content">
      <div class="section-kicker">OPERATIONS OVERVIEW</div>
      <div class="dashboard-titlebar">
        <div>
          <h1>Alert activity <span class="count-bubble">{count}</span></h1>
          <p>Real-time back-in-stock alerts, authoritative stock verification & outbox status.</p>
        </div>
        <div style="display:flex;gap:12px;">
          <a class="outline-button" href="/embed" target="_blank">Preview Widget ↗</a>
        </div>
      </div>
      
      <section class="stats-grid" aria-label="Alert metrics">
        {card_markup}
      </section>
      
      <div class="activity-top">
        <div>
          <div class="section-kicker">DISPATCH LEDGER</div>
          <h2>Alert activity</h2>
        </div>
        <div class="retry-note">↻ {retrying} retrying</div>
      </div>
      
      <div class="table-card">
        <div class="table-toolbar">
          {pills}
          <input type="text" id="table-search" class="table-search" placeholder="Filter by email or SKU…" oninput="filterTable()">
          <span class="table-hint">SHOWING {len(rows)} RECENT</span>
        </div>
        <div class="table-scroll">
          <table id="alerts-table">
            <thead>
              <tr>
                <th>CUSTOMER</th>
                <th>PRODUCT SKU</th>
                <th>STATUS</th>
                <th class="hide-small">REQUESTED</th>
                <th class="hide-small">NOTIFIED</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>
      </div>
      
      <p class="dashboard-footnote">Restock Studio Enterprise · Sisense Architecture · Verified Stock API · Zero-Duplicate Outbox</p>
    </div>
  </main>
</div>
<script>
function filterTable() {{
  var q = document.getElementById('table-search').value.toLowerCase();
  var rows = document.querySelectorAll('.alert-row');
  rows.forEach(function(row) {{
    var text = row.innerText.toLowerCase();
    row.style.display = text.indexOf(q) !== -1 ? '' : 'none';
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
        shop_link = f'<tr><td align="center" style="padding:16px 36px 36px"><a href="{h(shop_url)}" style="display:block;background:#f59e0b;color:#0a0e17;text-decoration:none;padding:16px 28px;border-radius:8px;font-size:15px;font-weight:700">View In Store &nbsp;↗</a></td></tr>'
        
    return f'''<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>It's back in stock: {n}</title></head>
<body style="margin:0;padding:0;background:#0a0e17;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#f8fafc">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#0a0e17">
  <tr><td align="center" style="padding:36px 12px">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:560px;background:#111827;border:1px solid #1e293b;border-radius:14px;overflow:hidden">
      <tr>
        <td style="padding:28px 36px 24px;border-bottom:1px solid #1e293b;font-size:22px;font-weight:800;color:#f8fafc">
          <span style="color:#f59e0b">↗</span> Restock<span style="color:#f59e0b">.</span>
        </td>
      </tr>
      <tr>
        <td style="background:#0f172a;padding:40px 36px 36px;border-bottom:1px solid #1e293b">
          <div style="font-size:11px;letter-spacing:0.12em;color:#f59e0b;font-weight:700">RESTOCK CONFIRMATION</div>
          <h1 style="font-size:36px;line-height:1.15;letter-spacing:-0.03em;margin:14px 0 10px;color:#ffffff">Back in stock.</h1>
          <div style="font-size:16px;line-height:1.6;color:#94a3b8">The item you were waiting for is officially available again.</div>
        </td>
      </tr>
      <tr>
        <td style="padding:32px 36px 20px">
          <div style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#64748b;text-transform:uppercase">ITEM DETAILS</div>
          <div style="font-size:22px;font-weight:800;letter-spacing:-0.02em;line-height:1.3;margin-top:8px;color:#f8fafc">{n}</div>
          <div style="font-size:13px;color:#94a3b8;padding-top:6px;font-family:monospace">SKU: {s}</div>
          {price_line}
        </td>
      </tr>
      <tr>
        <td style="padding:0 36px 24px">
          <div style="border-top:1px solid #1e293b;padding-top:20px;font-size:14px;line-height:1.6;color:#94a3b8">
            This item has limited inventory and may sell out quickly. You received this because you specifically requested a notification.
          </div>
        </td>
      </tr>
      {shop_link}
      <tr>
        <td style="padding:24px 36px 32px;background:#090e17;font-size:12px;line-height:1.7;color:#64748b;border-top:1px solid #1e293b">
          You are receiving this single alert for {s}. No newsletters, no marketing lists.<br>
          <strong style="color:#94a3b8">Restock Studio Enterprise Alert Engine</strong>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>'''
