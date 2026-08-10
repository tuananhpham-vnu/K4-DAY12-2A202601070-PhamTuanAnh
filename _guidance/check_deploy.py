"""Gọi thử 4 endpoint của bản deploy CP5 và sinh báo cáo HTML để xem trực quan.

Không dùng fetch() trong trình duyệt vì server không bật CORS — gọi HTTP ở
đây (Python) rồi render kết quả thành HTML tĩnh, mở lên xem như một dashboard.

Chạy lại bất cứ lúc nào:
    venv\\Scripts\\python.exe _guidance\\check_deploy.py
"""

from __future__ import annotations

import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
env = dotenv_values(ROOT / ".env")

BASE_URL = "https://day12-chat-an29.onrender.com"
GOOD_TOKEN = env.get("DEPLOY_API_TOKEN") or env.get("API_TOKEN") or ""
BAD_TOKEN = "token-sai-co-tinh"

CHECKS = []


def record(name: str, expect: int, resp: httpx.Response | None, note: str = "", error: str = ""):
    ok = resp is not None and resp.status_code == expect
    CHECKS.append(
        {
            "name": name,
            "expect": expect,
            "actual": resp.status_code if resp is not None else None,
            "ok": ok,
            "body": (resp.text[:500] if resp is not None else ""),
            "note": note,
            "error": error,
        }
    )


def run():
    with httpx.Client(timeout=20) as client:
        try:
            r = client.get(f"{BASE_URL}/healthz")
            record("GET /healthz (liveness)", 200, r)
        except httpx.HTTPError as e:
            record("GET /healthz (liveness)", 200, None, error=str(e))

        try:
            r = client.get(f"{BASE_URL}/readyz")
            record("GET /readyz (readiness — Redis)", 200, r)
        except httpx.HTTPError as e:
            record("GET /readyz (readiness — Redis)", 200, None, error=str(e))

        try:
            r = client.post(
                f"{BASE_URL}/chat",
                json={"message": "test token sai"},
                headers={"Authorization": f"Bearer {BAD_TOKEN}"},
            )
            record("POST /chat — token SAI", 401, r, note="phải bị từ chối")
        except httpx.HTTPError as e:
            record("POST /chat — token SAI", 401, None, error=str(e))

        if GOOD_TOKEN:
            try:
                r = client.post(
                    f"{BASE_URL}/chat",
                    json={"message": "Deploy la gi?"},
                    headers={
                        "Authorization": f"Bearer {GOOD_TOKEN}",
                        "X-Client-Id": "sv-dashboard",
                    },
                )
                record("POST /chat — token ĐÚNG", 200, r, note="phải trả lời")
            except httpx.HTTPError as e:
                record("POST /chat — token ĐÚNG", 200, None, error=str(e))
        else:
            record(
                "POST /chat — token ĐÚNG",
                200,
                None,
                note="Bỏ qua — chưa có DEPLOY_API_TOKEN trong .env",
            )


def render_html() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    passed = sum(1 for c in CHECKS if c["ok"])
    total = len(CHECKS)

    cards = []
    for c in CHECKS:
        badge_class = "pass" if c["ok"] else "fail"
        badge_text = "PASS" if c["ok"] else "FAIL"
        actual = c["actual"] if c["actual"] is not None else "—"
        error_html = f'<div class="error">{c["error"]}</div>' if c["error"] else ""
        note_html = f'<div class="note">{c["note"]}</div>' if c["note"] else ""
        body_html = f'<pre class="body">{c["body"]}</pre>' if c["body"] else ""
        cards.append(f"""
        <div class="card {badge_class}">
          <div class="card-head">
            <span class="badge {badge_class}">{badge_text}</span>
            <span class="name">{c['name']}</span>
          </div>
          <div class="codes">
            <span>Kỳ vọng: <b>{c['expect']}</b></span>
            <span>Thực tế: <b>{actual}</b></span>
          </div>
          {note_html}
          {error_html}
          {body_html}
        </div>""")

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>CP5 — Trạng thái deploy</title>
<style>
  :root {{
    --bg: #0f1115; --card: #1a1d24; --border: #2a2e37;
    --text: #e6e8eb; --muted: #9aa1ac;
    --pass: #2fbf71; --fail: #e5484d;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2.5rem 1.5rem; background: var(--bg); color: var(--text);
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  }}
  .wrap {{ max-width: 720px; margin: 0 auto; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 0.2rem; }}
  .sub {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }}
  .summary {{
    display: inline-block; padding: 0.4rem 0.9rem; border-radius: 999px;
    font-weight: 600; margin-bottom: 1.5rem;
    background: {"#153524" if passed == total else "#3a1f22"};
    color: {"var(--pass)" if passed == total else "var(--fail)"};
  }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-left: 4px solid var(--border); border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 0.9rem;
  }}
  .card.pass {{ border-left-color: var(--pass); }}
  .card.fail {{ border-left-color: var(--fail); }}
  .card-head {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; }}
  .badge {{
    font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.5rem;
    border-radius: 4px; letter-spacing: 0.03em;
  }}
  .badge.pass {{ background: var(--pass); color: #06210f; }}
  .badge.fail {{ background: var(--fail); color: #2a0808; }}
  .name {{ font-weight: 600; }}
  .codes {{ display: flex; gap: 1.2rem; font-size: 0.85rem; color: var(--muted); }}
  .note {{ font-size: 0.82rem; color: var(--muted); margin-top: 0.4rem; }}
  .error {{ font-size: 0.82rem; color: var(--fail); margin-top: 0.4rem; }}
  .body {{
    margin-top: 0.6rem; background: #0b0d11; border-radius: 6px; padding: 0.6rem 0.8rem;
    font-size: 0.78rem; color: var(--muted); overflow-x: auto; white-space: pre-wrap;
    word-break: break-all;
  }}
  footer {{ color: var(--muted); font-size: 0.78rem; margin-top: 1.5rem; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>CP5 — Trạng thái bản deploy</h1>
    <div class="sub">{BASE_URL}</div>
    <div class="summary">{passed}/{total} kiểm tra đạt</div>
    {''.join(cards)}
    <footer>Chạy lúc {ts} — chạy lại: <code>venv\\Scripts\\python.exe _guidance\\check_deploy.py</code></footer>
  </div>
</body>
</html>"""


def main():
    run()
    out = ROOT / "_guidance" / "deploy_status.html"
    out.write_text(render_html(), encoding="utf-8")
    print(f"Đã ghi báo cáo: {out}")
    for c in CHECKS:
        status = "PASS" if c["ok"] else "FAIL"
        print(f"  [{status}] {c['name']} — kỳ vọng {c['expect']}, thực tế {c['actual']}")
    webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
