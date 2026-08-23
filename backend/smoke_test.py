import os
import time

os.environ.setdefault("DATABASE_URL", "sqlite:///./caremind_check.db")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)  # context triggers startup -> seed

with client:
    # health
    r = client.get("/")
    assert r.status_code == 200, r.text
    print("GET / ok:", r.json()["status"])

    # login elder
    r = client.post("/auth/login", json={"email": "rahma@caremind.demo", "password": "Password1!"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    print("Login elder ok, role:", r.json()["user"]["role"])
    headers = {"Authorization": f"Bearer {token}"}

    # today's medicines
    r = client.get("/medicines/today", headers=headers)
    assert r.status_code == 200, r.text
    doses = r.json()
    print("Today doses:", [(d["medicine_name"], d["scheduled_time"], d["status"]) for d in doses])

    # take the pending evening dose if present
    for d in doses:
        if d["status"] == "pending":
            r = client.post(f"/medicines/take/{d['log_id']}", headers=headers)
            assert r.status_code == 200, r.text
            print("Took dose:", d["medicine_name"], "->", r.json()["status"])
            break

    # health today summary
    r = client.get("/health/today", headers=headers)
    assert r.status_code == 200, r.text
    print("Health today:", r.json())

    # AI chat
    r = client.post("/ai/chat", json={"message": "My blood pressure is high, should I worry?"}, headers=headers)
    assert r.status_code == 200, r.text
    print("AI chat reply:", r.json()["reply"][:100], "...")

    # AI chat - emergency keyword
    r = client.post("/ai/chat", json={"message": "I think I am having chest pain"}, headers=headers)
    assert r.status_code == 200, r.text
    print("AI emergency reply:", r.json()["reply"][:100], "...")

    # SOS trigger
    r = client.post("/emergency/trigger", json={"trigger_type": "manual"}, headers=headers)
    assert r.status_code == 200, r.text
    sos = r.json()
    print("SOS:", sos["message"], "| hospital:", sos["hospital"]["name"])
    event_id = sos["event_id"]

    # resolve SOS
    r = client.post(f"/emergency/events/{event_id}/resolve", json={"summary": "False alarm"}, headers=headers)
    assert r.status_code == 200, r.text
    print("SOS resolved:", r.json()["status"])

    # Moments feed
    r = client.get("/care/posts", headers=headers)
    assert r.status_code == 200, r.text
    print("Moments posts:", len(r.json()))

    # family chat
    r = client.get("/care/conversations", headers=headers)
    assert r.status_code == 200, r.text
    conv_id = r.json()[0]["id"]
    print("Family conversations:", len(r.json()))
    r = client.post(f"/care/conversations/{conv_id}/messages",
                    json={"conversation_id": conv_id, "content": "Test message"}, headers=headers)
    assert r.status_code == 200, r.text
    print("Family message sent:", r.json()["content"])

    # doctor login + patients
    r = client.post("/auth/login", json={"email": "doctor@caremind.demo", "password": "Password1!"})
    doc_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.get("/doctors/patients", headers=doc_headers)
    assert r.status_code == 200, r.text
    print("Doctor patients:", [(p["name"], p["adherence_rate"]) for p in r.json()])

    # caregiver overview
    r = client.post("/auth/login", json={"email": "nadia@caremind.demo", "password": "Password1!"})
    fam_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.get("/caregiver/overview", headers=fam_headers)
    assert r.status_code == 200, r.text
    print("Caregiver overview:", r.json())

print("\nALL SMOKE TESTS PASSED")
