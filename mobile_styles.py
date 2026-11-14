MOBILE_CSS = """
<style>
    * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; -webkit-tap-highlight-color: transparent; }
    body { margin: 0; background: #0b1021; color: #f8fafc; padding-bottom: 84px; }
    .app-bar { background: #10172d; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e294b; position: sticky; top: 0; z-index: 10; }
    .brand { display: flex; align-items: center; gap: 8px; font-size: 1.15rem; font-weight: 800; color: #f8fafc; }
    .wrap { max-width: 520px; margin: 0 auto; padding: 16px; }
    .card { background: #131b31; border: 1px solid #222f52; border-radius: 18px; padding: 18px; margin-bottom: 14px; }
    .hero { background: linear-gradient(135deg, #4f46e5, #312e81); color: #fff; border-radius: 20px; padding: 20px; margin-bottom: 16px; border: 1px solid rgba(245, 158, 11, 0.35); }
    .badge { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
    .bal { font-size: 2rem; font-weight: 800; margin: 8px 0; display: flex; align-items: center; gap: 10px; }
    input, select, button { width: 100%; padding: 13px; margin-top: 10px; border-radius: 12px; border: 1px solid #2a3963; font-size: 0.98rem; }
    input, select { background: #0b1021; color: #f8fafc; }
    button { background: #4f46e5; color: #ffffff; font-weight: 700; border: none; cursor: pointer; }
    .btn-gold { background: #f59e0b; color: #111827; }
    .btn-dark { background: #1e294b; color: #e2e8f0; }
    .tab-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #10172d; border-top: 1px solid #1e294b; display: flex; justify-content: space-around; padding: 8px 0; z-index: 20; }
    .tab-btn { background: none; border: none; color: #94a3b8; font-size: 0.75rem; font-weight: 600; margin: 0; padding: 4px; width: auto; }
    .tab-btn.active { color: #fbbf24; }
    .tx { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #1e294b; gap: 10px; }
    .err { color: #fb7185; font-size: 0.88rem; min-height: 20px; margin-top: 8px; }
    .ok { color: #34d399; font-size: 0.88rem; min-height: 20px; margin-top: 8px; }
</style>
"""
