"""Day 3 smoke test — wellness challenges + live-AI report summaries."""
import io
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./caremind_check3.db")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

with client:
    r = client.post("/auth/login", json={"email": "rahma@caremind.demo", "password": "Password1!"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # --- Wellness challenge ---
    r = client.get("/challenges/today", headers=h)
    assert r.status_code == 200, r.text
    c = r.json()
    print(f"Challenge today: {c['icon']} {c['title']} [{c['category']}] done={c['done']} week={c['week_done']}")

    r = client.post("/challenges/today/complete", headers=h)
    assert r.status_code == 200 and r.json()["done"], r.text
    print("Challenge completed:", r.json()["week_done"] >= 1)

    r = client.post("/challenges/today/complete", headers=h)
    assert r.json()["done"]
    print("Re-complete is idempotent ✅")

    # --- Report upload with LIVE AI enrichment (Qwen) ---
    fake = io.BytesIO(b"\x89PNG\r\n\x1a\n fake-png-bytes")
    r = client.post(
        "/reports/upload",
        headers=h,
        data={"title": "Quarterly Blood Test", "report_type": "lab", "report_date": "2026-08-23"},
        files={"file": ("lab.png", fake, "image/png")},
    )
    assert r.status_code == 200, r.text
    rep = r.json()
    print("Report:", rep["title"], "| status:", rep["status"])
    print("AI summary:", (rep.get("summary") or "")[:160])

print("\nDAY 3 SMOKE TESTS PASSED")
