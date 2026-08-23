"""Day 2 smoke test — reports, notifications, doctor summary & care plans."""
import io
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./caremind_check2.db")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

with client:
    def login(email):
        r = client.post("/auth/login", json={"email": email, "password": "Password1!"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    # ---- ELDER: reports ----
    eh = login("rahma@caremind.demo")
    r = client.get("/reports", headers=eh)
    assert r.status_code == 200, r.text
    print("Elder reports before:", len(r.json()))

    fake = io.BytesIO(b"\x89PNG\r\n\x1a\n fake-png-bytes")
    r = client.post(
        "/reports/upload",
        headers=eh,
        data={"title": "Morning Blood Test", "report_type": "blood", "report_date": "2026-08-23"},
        files={"file": ("blood.png", fake, "image/png")},
    )
    assert r.status_code == 200, r.text
    rep = r.json()
    print("Uploaded report:", rep["title"], "| status:", rep["status"], "| summary:", (rep.get("summary") or "")[:60])

    r = client.get(f"/reports/{rep['id']}", headers=eh)
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    flags = {row["flag"] for row in results}
    print("Report detail rows:", len(results), "| flags:", flags)

    # ---- ELDER: notifications ----
    r = client.get("/notifications", headers=eh)
    assert r.status_code == 200, r.text
    n = r.json()["items"]
    print("Elder notifications:", len(n), "| types:", sorted({x['type'] for x in n}))

    # ---- ELDER: family chat ----
    r = client.get("/care/conversations", headers=eh)
    conv_id = r.json()[0]["id"]
    r = client.post(f"/care/conversations/{conv_id}/messages",
                    json={"conversation_id": conv_id, "content": "Nadia, I just uploaded my blood test. CareMind says I should show it to the doctor. 📄"},
                    headers=eh)
    assert r.status_code == 200, r.text
    print("Family message sent ok")

    # ---- FAMILY: notifications ----
    fh = login("nadia@caremind.demo")
    r = client.get("/notifications", headers=fh)
    assert r.status_code == 200, r.text
    print("Family notifications:", len(r.json()["items"]), "| types:", sorted({x['type'] for x in r.json()['items']}))

    # ---- DOCTOR: patients, summary, care plan ----
    dh = login("doctor@caremind.demo")
    r = client.get("/doctors/patients", headers=dh)
    assert r.status_code == 200, r.text
    pid = r.json()[0]["patient_id"]
    print("Doctor patients:", [(p["name"], p["adherence_rate"]) for p in r.json()])

    r = client.get(f"/doctors/patients/{pid}/summary", headers=dh)
    assert r.status_code == 200, r.text
    s = r.json()
    bp = [m for m in s["timeline"] if m["metric_type"] == "blood_pressure"]
    print("Patient summary: timeline", len(s["timeline"]), "| BP points", len(bp), "| medicines", len(s["medicines"]), "| plans", len(s["care_plans"]))

    r = client.post("/doctors/care-plans", headers=dh, json={
        "elder_user_id": pid,
        "title": "Reduce salt & walk 20 min daily",
        "description": "Limit salty food; gentle evening walk after dinner.",
        "instructions": "Walk slowly with family; stop if dizzy.",
    })
    assert r.status_code == 200, r.text
    print("Care plan created:", r.json())

    r = client.get(f"/doctors/patients/{pid}/summary", headers=dh)
    print("Plans after create:", len(r.json()["care_plans"]))

    # ---- DOCTOR: notifications ----
    r = client.get("/notifications", headers=dh)
    print("Doctor notifications:", len(r.json()["items"]), "| types:", sorted({x['type'] for x in r.json()['items']}))

print("\nDAY 2 SMOKE TESTS PASSED")
