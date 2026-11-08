"""Presentation templates and responsive transactional HTML email for Restock Studio.
Design System: Achromatic Ledger (Distilled from taste-skill v2).
Strictly adheres to anti-slop guidelines: no generic kickers, no gradient text,
no unicode emojis in place of UI elements, no index numbering on cards,
pure achromatic chrome with data-only signals.
"""
from __future__ import annotations
import html
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")


def fmt_ny_time(iso_str):
    if not iso_str:
        return "—"
    try:
        clean = str(iso_str).strip()
        if clean.endswith('Z'):
            clean = clean[:-1] + '+00:00'
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ny_dt = dt.astimezone(NY_TZ)
        return ny_dt.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return str(iso_str)[:16].replace('T', ' ')


def h(value):
    return html.escape(str(value or ""), quote=True)


def layout(title, main, *, body_class="", script=""):
    script_tag = f'<script src="/static/{script}?v=9" defer></script>' if script else ""
    return f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f8f8f8"><title>{h(title)} — Restock Studio</title>
<link rel="stylesheet" href="/static/style.css?v=9">{script_tag}</head>
<body class="{h(body_class)}">{main}</body></html>'''


def brand():
    return '''<a class="brand" href="/">
  <span class="brand-mark">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
  </span>
  <span class="brand-text">Restock Studio</span>
</a>'''


def home_page():
    return layout("Inventory Alert Engine", f'''
<div class="site-shell">
  <header class="topbar">
    {brand()}
    <nav class="top-nav">
      <a href="/embed" class="nav-link">Customer Widget</a>
      <a href="/admin/login?demo=1" class="nav-button">Operations Console (Demo) <span>↗</span></a>
    </nav>
  </header>
  
  <main class="home-grid">
    <section class="hero-copy">
      <h1>Automated back-in-stock alerts for modern commerce</h1>
      <p class="hero-subtitle">Capture lost sales with high-converting customer subscriptions, authoritative inventory verification, and resilient transactional email dispatch with zero pip dependencies.</p>
      
      <div class="hero-actions">
        <a class="primary-button" href="/embed">Test Alert Widget <span>↗</span></a>
        <a class="secondary-button" href="/admin/login?demo=1">Operations Console (1-Click Demo) <span>↗</span></a>
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
        <div class="panel-title">System telemetry & dispatch</div>
        <div class="status-indicator"><span class="status-dot-pulse"></span> Active</div>
      </div>
      
      <div class="telemetry-metrics">
        <div class="telemetry-card">
          <div class="telemetry-label">Deduplication rate</div>
          <div class="telemetry-val">100%</div>
          <div class="telemetry-sub">ACID Partial Unique Index</div>
        </div>
        <div class="telemetry-card">
          <div class="telemetry-label">Inventory sync</div>
          <div class="telemetry-val">Authoritative</div>
          <div class="telemetry-sub">Phantom Restocks Blocked</div>
        </div>
      </div>
      
      <div class="feed-container">
        <div class="feed-head">Recent inventory dispatch stream</div>
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
    <div class="footer-left">Restock Studio — Production Inventory Engine</div>
    <div class="footer-right">Deployed on AWS EC2 · TLS Terminated · SQLite WAL</div>
  </footer>
</div>''')


def embed_page(sku):
    sku = h(sku or "TEE-ORG-WHT-M")
    sample_items = [
        ("TEE-ORG-WHT-M", "Organic T-Shirt", "White · Medium"),
        ("NB-DOT-A5", "Dot Grid Notebook", "A5 · 192 Pages"),
        ("PLNT-MON-M", "Monstera Plant", "Ceramic Pot · Medium"),
        ("KNF-CHF-20", "Chef's Knife", "20 cm Steel Blade"),
    ]
    catalog_items_html = "".join(f'''<button type="button" class="catalog-item {'active' if sku == item_sku else ''}" data-sku="{item_sku}">
  <span class="catalog-title">{item_title}</span>
  <span class="catalog-meta">{item_meta}</span>
  <span class="catalog-sku">{item_sku}</span>
</button>''' for item_sku, item_title, item_meta in sample_items)

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
          <div class="catalog-grid" role="group" aria-label="Select catalog item">
            {catalog_items_html}
          </div>
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
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2e7d32" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
      </div>
      <h2>Alert registered</h2>
      <p id="success-msg" class="embed-desc">We've locked in your request. You will receive an email as soon as this item is verified in stock.</p>
      <button class="secondary-button" id="new-alert" type="button">Track another product</button>
    </div>
  </div>
  <div class="embed-credit">Restock Studio inventory notification engine</div>
</main>''', body_class="embed-body", script="embed.js")


def login_page(error="", password_hint=""):
    error_markup = f'<div class="form-error visible" role="alert">{h(error)}</div>' if error else ''
    cred_hint = f'''<div class="demo-cred-row"><span>Demo password:</span> <code>{h(password_hint)}</code></div>''' if password_hint else ''
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
    
    <div class="demo-access-card">
      <div class="demo-access-head">
        <span class="demo-pill">Portfolio Reviewer</span>
        <span class="demo-note">Instant live access</span>
      </div>
      <p class="demo-access-desc">Reviewing this project from my portfolio? Enter directly without typing credentials:</p>
      <a class="secondary-button full-width text-center" href="/admin/login?demo=1">Enter Operations Console (1-Click Demo) ↗</a>
      {cred_hint}
    </div>
    
    <form method="post" action="/admin/login">
      <div class="field-group">
        <label for="password">Admin password</label>
        <input id="password" name="password" type="password" required autocomplete="current-password" placeholder="Enter password" maxlength="256" value="{h(password_hint)}">
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

    rows_html = ''.join(f'''<tr class="table-row" data-id="{r['id']}" data-status="{r['status']}">
  <td><div class="email-val">{h(r['email'])}</div><div class="mobile-time">{h(fmt_ny_time(r['created_at']))}</div></td>
  <td><span class="sku-tag">{h(r['sku'])}</span></td>
  <td><span class="status-badge {h(r['status'])}">{h(r['status'])}</span></td>
  <td class="hide-mobile">{h(fmt_ny_time(r['created_at']))}</td>
  <td class="hide-mobile">{h(fmt_ny_time(r['notified_at']))}</td>
  <td class="text-right">
    <button type="button" class="btn-inspect" data-target="details-{r['id']}" title="Inspect delivery diagnostics">Details ▾</button>
  </td>
</tr>
<tr class="details-row" id="details-{r['id']}" hidden>
  <td colspan="6">
    <div class="inspector-box">
      <div class="inspector-grid">
        <div class="inspector-item">
          <span class="inspector-label">Internal Request ID</span>
          <span class="inspector-val">#{r['id']}</span>
        </div>
        <div class="inspector-item">
          <span class="inspector-label">Outbox Delivery Attempts</span>
          <span class="inspector-val">{r.get('attempts', 0) or 0} of 5</span>
        </div>
        <div class="inspector-item">
          <span class="inspector-label">Provider Message Reference</span>
          <span class="inspector-val">{h(r.get('provider_id') or 'Pending In-Stock')}</span>
        </div>
        <div class="inspector-item">
          <span class="inspector-label">Execution Stage</span>
          <span class="inspector-val">{'Dispatched via Resend' if r['status'] == 'notified' else ('Queued for Transmission' if r['status'] == 'queued' else ('Alert Cancelled' if r['status'] == 'cancelled' else 'Awaiting Stock Verification'))}</span>
        </div>
        <div class="inspector-item full-width">
          <span class="inspector-label">Outbox Diagnostic Trace / Error Log</span>
          <span class="inspector-val code-val">{h(r.get('last_error') or 'Zero errors recorded. Pipeline operating normally.')}</span>
        </div>
      </div>
      { f'<div class="inspector-footer"><button type="button" class="btn-cancel-alert" data-id="{r["id"]}">Cancel and remove from waitlist</button></div>' if r['status'] == 'open' else '' }
    </div>
  </td>
</tr>''' for r in rows)

    if not rows_html:
        rows_html = '<tr><td colspan="6" class="empty-row">No records found matching this filter.</td></tr>'

    ny_now_str = datetime.now(NY_TZ).strftime("%I:%M:%S %p %Z")

    return layout("Operations Dashboard", f'''
<div class="admin-shell">
  <aside class="admin-sidebar">
    <div class="sidebar-top">
      {brand()}
      <div class="sidebar-tag">Operations</div>
    </div>
    
    <nav class="sidebar-menu">
      <div class="menu-label">Navigation</div>
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
      <div class="topbar-title">Operations Console / Alert Orchestration</div>
      <div class="topbar-actions">
        <button id="sound-toggle" class="sound-toggle" type="button" aria-pressed="true" title="Toggle audio alert on new subscription">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/></svg>
          <span id="sound-label">Audio alert on</span>
        </button>
        <div class="topbar-status"><span class="dot-live"></span> Live sync active · {ny_now_str}</div>
      </div>
    </header>
    
    <div class="admin-content">
      <div class="content-header">
        <div>
          <h1>Activity & Subscriptions</h1>
          <p>Real-time customer alert registry, authoritative inventory verification status, and transactional email outbox jobs.</p>
        </div>
        <div class="content-actions">
          <a class="secondary-button" href="/admin/export.csv" id="btn-export-csv" download title="Export subscriptions to CSV">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Export CSV</span>
          </a>
          <a class="secondary-button" href="/admin">Refresh Activity</a>
        </div>
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
                <th>Customer email</th>
                <th>Product SKU</th>
                <th>Alert status</th>
                <th class="hide-mobile">Requested at (EST)</th>
                <th class="hide-mobile">Notified at (EST)</th>
                <th class="text-right">Diagnostics</th>
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
</div>''', body_class="admin-body", script="admin.js")


def email_html(product_name, sku, product, shop_url=""):
    n = h(product_name)
    s = h(sku)
    price = product.get('price')
    currency = product.get('currency', 'GBP')
    price_line = f'<div style="font-size:15px;color:#6b6b6b;padding-top:6px">{h(currency)} {h(price)}</div>' if isinstance(price, (int, float)) else ''
    
    shop_link = ''
    if isinstance(shop_url, str) and shop_url.startswith(('https://', 'http://')):
        shop_link = f'<tr><td align="center" style="padding:16px 36px 36px"><a href="{h(shop_url)}" style="display:block;background:#141414;color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:6px;font-size:14px;font-weight:600">View In Store &nbsp;↗</a></td></tr>'
        
    return f'''<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>It's back in stock: {n}</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0a0a0a">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#f8f8f8">
  <tr><td align="center" style="padding:36px 12px">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:540px;background:#ffffff;border:1px solid #e6e6e6;border-radius:8px;overflow:hidden">
      <tr>
        <td style="padding:24px 32px 20px;border-bottom:1px solid #e6e6e6;font-size:18px;font-weight:700;color:#0a0a0a">
          Restock Studio
        </td>
      </tr>
      <tr>
        <td style="padding:32px 32px 24px;border-bottom:1px solid #e6e6e6">
          <h1 style="font-size:26px;line-height:1.2;letter-spacing:-0.02em;margin:0 0 10px;color:#0a0a0a">Back in stock.</h1>
          <div style="font-size:15px;line-height:1.6;color:#6b6b6b">The item you were waiting for is officially available in inventory again.</div>
        </td>
      </tr>
      <tr>
        <td style="padding:28px 32px 20px">
          <div style="font-size:12px;font-weight:600;color:#6b6b6b">Item details</div>
          <div style="font-size:18px;font-weight:700;line-height:1.3;margin-top:6px;color:#0a0a0a">{n}</div>
          <div style="font-size:13px;color:#6b6b6b;padding-top:4px">SKU: {s}</div>
          {price_line}
        </td>
      </tr>
      <tr>
        <td style="padding:0 32px 24px">
          <div style="border-top:1px solid #f0f0f0;padding-top:18px;font-size:13px;line-height:1.6;color:#6b6b6b">
            This item has limited inventory and may sell out quickly. You received this because you specifically requested a restock notification.
          </div>
        </td>
      </tr>
      {shop_link}
      <tr>
        <td style="padding:20px 32px 28px;background:#f8f8f8;font-size:12px;line-height:1.6;color:#999999;border-top:1px solid #e6e6e6">
          You are receiving this single alert for SKU {s}. No newsletters, no marketing lists.<br>
          <strong style="color:#6b6b6b">Restock Studio Inventory Engine</strong>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>'''
