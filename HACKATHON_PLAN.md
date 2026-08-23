# CareMind AI — 3-Day Hackathon Battle Plan

> Goal: **win the demo**. Judges remember a polished, emotional, end-to-end story — not a wide feature list.

## Demo North Star (the 6-scene story from PRD §51)

1. **Morning** — Rahima (72) logs in, sees BP/sleep/activity + next medicine, confirms her medicine.
2. **Wellness** — Logs a morning walk → daughter reacts "Proud of you!" on the Moments feed.
3. **Health Report** — Uploads a report → AI finds 2 values to discuss, offers "Explain Simply".
4. **Doctor** — Doctor consult: sees timeline, BP trend, adherence; creates a care plan → reminders auto-created.
5. **Family** — Daughter receives "Dr. Rahman shared a care instruction".
6. **Emergency** — "I fell and can't get up." → SOS: location, nearby hospital, family alerted.

## Day 1 — Foundation (runs end-to-end)

- [x] Monorepo scaffold (backend + frontend + docker-compose)
- [x] SQLAlchemy models (full port of `schema.sql`)
- [x] JWT auth (register / login / me) + role-based access
- [x] Demo seed data (Rahima, Nadia, Dr. Rahman, medicines, BP trend, posts, emergency contacts)
- [x] Elder Mode shell + bottom nav + persistent SOS button
- [ ] AI service abstraction (mock mode ↔ real API)
- [ ] Landing + auth pages
- [ ] Elder Home dashboard (Today's Care, Today's Health, feeling check-in)

## Day 2 — Core demo journey

- [ ] Medicine flow: today's schedule → I TOOK IT → adherence
- [ ] Health: metric entry + Health Timeline + trend insight
- [ ] AI Companion: context-aware chat (mock + real)
- [ ] Report upload + AI summary
- [ ] Family chat + Care Circle
- [ ] CareMind Moments (post + react)
- [ ] SOS emergency flow (location, contacts, nearby hospital)

## Day 3 — Doctor, Caregiver & Polish

- [ ] Doctor dashboard (patient summary + care plan)
- [ ] Caregiver dashboard (Mom's Care Overview)
- [ ] Accessibility pass (large type, big targets, high contrast)
- [ ] 5-minute demo script + judge Q&A prep
- [ ] Deploy to CloudStudio
- [ ] Rehearse until the story is smooth

## Demo Account Convention

```
rahma@caremind.demo  /  Password1!   (elder)
nadia@caremind.demo  /  Password1!   (family)
doctor@caremind.demo /  Password1!   (doctor)
```

## Non-Negotiables

- The AI never diagnoses, prescribes, or contradicts doctors (PRD §12).
- Simulated integrations (hospital, emergency calls) are labeled as demo — never claimed as live.
- One clear "wow" moment: **the SOS voice flow**.
