"""Seed demo data — Rahima Begum (elder), Nadia Rahman (daughter),
Dr. Ayesha Rahman (doctor) plus health history, medicines, moments and chat.
"""

import json
from datetime import datetime, date, time, timedelta

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.models import (
    AiConversation,
    AiInsight,
    AiMessage,
    CareCircle,
    CareCircleMember,
    Conversation,
    ConversationMember,
    Doctor,
    DoctorCarePlan,
    DoctorPatientRelationship,
    EmergencyContact,
    HealthMetric,
    MedicationLog,
    MedicationSchedule,
    Medicine,
    Message,
    Post,
    PostComment,
    Role,
    User,
    UserProfile,
)
from app.core.database import Base, engine, SessionLocal

DEMO_PASSWORD = "Password1!"


def init_roles(db: Session) -> dict[str, Role]:
    roles = {}
    for code, name in (("elder", "Elder"), ("family", "Family"),
                       ("doctor", "Doctor"), ("caregiver", "Caregiver")):
        role = db.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            db.add(role)
            db.flush()
        roles[code] = role
    db.commit()
    return roles


def _get_or_create_user(db: Session, roles: dict, email: str, full_name: str, role_code: str,
                        dob: str | None = None, gender: str | None = None,
                        city: str | None = None, phone: str | None = None) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, full_name=full_name, phone=phone,
                password_hash=hash_password(DEMO_PASSWORD), role_id=roles[role_code].id, is_verified=True)
    db.add(user)
    db.flush()
    db.add(UserProfile(
        user_id=user.id,
        date_of_birth=datetime.strptime(dob, "%Y-%m-%d").date() if dob else None,
        gender=gender or "prefer_not_to_say",
        city=city,
        primary_language="english",
    ))
    return user


def seed_all() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        roles = init_roles(db)

        # ---------- demo family ----------
        rahma = _get_or_create_user(db, roles, "rahma@caremind.demo", "Rahima Begum", "elder",
                                    dob="1954-03-14", gender="female", city="Dhaka",
                                    phone="+880 1700 000 001")
        nadia = _get_or_create_user(db, roles, "nadia@caremind.demo", "Nadia Rahman", "family",
                                    dob="1985-06-02", gender="female", city="Dhaka",
                                    phone="+880 1700 000 002")
        dr_rahman = _get_or_create_user(db, roles, "doctor@caremind.demo", "Dr. Ayesha Rahman", "doctor",
                                        dob="1978-11-20", gender="female", city="Dhaka",
                                        phone="+880 1700 000 003")
        db.commit()

        # ---------- doctor profile ----------
        doctor = db.query(Doctor).filter(Doctor.user_id == dr_rahman.id).first()
        if doctor is None:
            doctor = Doctor(
                user_id=dr_rahman.id, license_number="BMDC-045321",
                specialty="Geriatric Medicine", hospital="City General Hospital",
                department="Geriatrics", years_experience=16,
                consultation_start=time(9, 0), consultation_end=time(17, 0),
                bio="Geriatrician focused on hypertension and preventive care for older adults.",
            )
            db.add(doctor)
            db.flush()

        # ---------- care circle ----------
        circle = db.query(CareCircle).filter(CareCircle.owner_user_id == rahma.id).first()
        if circle is None:
            circle = CareCircle(name="Rahima's Care Circle", owner_user_id=rahma.id,
                                invitation_code="RAHMA-CARE", created_by=rahma.id)
            db.add(circle)
            db.flush()
            db.add_all([
                CareCircleMember(care_circle_id=circle.id, user_id=rahma.id, relationship_type="self"),
                CareCircleMember(care_circle_id=circle.id, user_id=nadia.id, relationship_type="daughter"),
                CareCircleMember(care_circle_id=circle.id, user_id=dr_rahman.id, relationship_type="doctor"),
            ])

        # ---------- doctor-patient link + care plan ----------
        rel = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_user_id == rahma.id,
        ).first()
        if rel is None:
            db.add(DoctorPatientRelationship(doctor_id=doctor.id, patient_user_id=rahma.id))
        if db.query(DoctorCarePlan).filter(DoctorCarePlan.elder_user_id == rahma.id).count() == 0:
            db.add(DoctorCarePlan(
                doctor_id=doctor.id, elder_user_id=rahma.id,
                title="Blood pressure management",
                description="Monitor BP twice a day, reduce salt, gentle 20-minute walks.",
                instructions="Take Amlodipine 5mg daily at 8:00 PM. Log BP in the morning and evening.",
                start_date=date.today() - timedelta(days=45), end_date=None, status="active",
            ))

        # ---------- health history (BP trend + sleep + activity) ----------
        if db.query(HealthMetric).filter(HealthMetric.user_id == rahma.id).count() == 0:
            now = datetime.utcnow()
            # BP: 14 readings, trending upward
            base = (132, 84)
            for i in range(13, -1, -1):
                day = now - timedelta(days=i)
                morning = day.replace(hour=8, minute=30)
                systolic = base[0] + i  # older days lower, recent days higher
                diastolic = base[1] + max(0, i - 6) if i > 6 else base[1]
                m = HealthMetric(user_id=rahma.id, metric_type="blood_pressure", source="manual",
                                 measured_at=morning)
                db.add(m)
                db.flush()
                from app.models.models import BloodPressureRecord
                db.add(BloodPressureRecord(metric_id=m.id, systolic=systolic, diastolic=diastolic, pulse=74))

            # Sleep last 7 nights
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                hours = 6.5 + ((i * 37) % 10) / 10  # 6.5 - 7.5 h
                m = HealthMetric(user_id=rahma.id, metric_type="sleep", source="manual",
                                 measured_at=day.replace(hour=7, minute=0))
                db.add(m)
                db.flush()
                from app.models.models import SleepRecord
                db.add(SleepRecord(metric_id=m.id, start_time=day.replace(hour=23, minute=10) - timedelta(days=1),
                                   end_time=day.replace(hour=6, minute=20), sleep_hours=round(hours, 1),
                                   quality="good" if hours >= 7 else "fair"))

            # Morning walk today (demo scene 2)
            today_morning = now.replace(hour=7, minute=45)
            m = HealthMetric(user_id=rahma.id, metric_type="activity", source="manual",
                             measured_at=today_morning)
            db.add(m)
            db.flush()
            from app.models.models import ActivityRecord
            db.add(ActivityRecord(metric_id=m.id, activity_type="walk", steps=2840,
                                  duration_minutes=32, distance_km=2.1, calories=118,
                                  note="Morning walk to the park"))

        # ---------- medicines ----------
        amlodipine = db.query(Medicine).filter(Medicine.user_id == rahma.id, Medicine.name == "Amlodipine").first()
        if amlodipine is None:
            amlodipine = Medicine(
                user_id=rahma.id, name="Amlodipine", category="prescription",
                dosage="5", dosage_unit="mg", frequency="Once daily", 
                instructions="Take one tablet with water every evening.",
                food_requirement="any", start_date=date.today() - timedelta(days=60),
                created_by=doctor.id,
            )
            db.add(amlodipine)
            db.flush()
            sched = MedicationSchedule(medicine_id=amlodipine.id, scheduled_time=time(20, 0),
                                       dosage_amount=5, dosage_unit="mg", repeat_days="all")
            db.add(sched)
            db.flush()

            # Seed 7 days of logs (taken except today pending + tomorrow reminders)
            for offset in range(-6, 1):
                day = date.today() + timedelta(days=offset)
                log = MedicationLog(
                    medicine_id=amlodipine.id, schedule_id=sched.id, user_id=rahma.id,
                    scheduled_for=datetime.combine(day, time(20, 0)),
                    status="taken", taken_at=datetime.combine(day, time(20, 5)),
                )
                db.add(log)
            for offset in range(1, 4):
                day = date.today() + timedelta(days=offset)
                db.add(MedicationLog(
                    medicine_id=amlodipine.id, schedule_id=sched.id, user_id=rahma.id,
                    scheduled_for=datetime.combine(day, time(20, 0)), status="pending",
                ))

        if db.query(Medicine).filter(Medicine.user_id == rahma.id, Medicine.name == "Vitamin D3").count() == 0:
            vitd = Medicine(
                user_id=rahma.id, name="Vitamin D3", category="supplement",
                dosage="1000", dosage_unit="IU", frequency="Once daily",
                instructions="Take after breakfast.", food_requirement="after_food",
                start_date=date.today() - timedelta(days=90),
            )
            db.add(vitd)
            db.flush()
            sched = MedicationSchedule(medicine_id=vitd.id, scheduled_time=time(9, 0),
                                       dosage_amount=1000, dosage_unit="IU", repeat_days="all")
            db.add(sched)
            db.flush()
            db.add(MedicationLog(
                medicine_id=vitd.id, schedule_id=sched.id, user_id=rahma.id,
                scheduled_for=datetime.combine(date.today(), time(9, 0)),
                status="taken", taken_at=datetime.combine(date.today(), time(9, 3)),
            ))
            for offset in range(1, 3):
                day = date.today() + timedelta(days=offset)
                db.add(MedicationLog(
                    medicine_id=vitd.id, schedule_id=sched.id, user_id=rahma.id,
                    scheduled_for=datetime.combine(day, time(9, 0)), status="pending",
                ))

        # ---------- emergency contacts ----------
        if db.query(EmergencyContact).filter(EmergencyContact.elder_user_id == rahma.id).count() == 0:
            db.add_all([
                EmergencyContact(elder_user_id=rahma.id, name="Nadia Rahman", relationship_type="daughter",
                                 phone="+880 1700 000 002", is_primary=True),
                EmergencyContact(elder_user_id=rahma.id, name="City General Hospital", relationship_type="hospital",
                                 phone="+880 9600 000 111", is_primary=False),
            ])

        # ---------- Moments feed ----------
        if db.query(Post).filter(Post.author_id == rahma.id).count() == 0:
            post1 = Post(author_id=rahma.id, care_circle_id=circle.id,
                         content="Beautiful morning walk today! 2.1 km in the park. "
                                 "Feeling strong and grateful.",
                         visibility="care_circle")
            db.add(post1)
            db.flush()
            post2 = Post(author_id=nadia.id, care_circle_id=circle.id,
                         content="Mom's medicine adherence is at 100% this week! So proud of you.",
                         visibility="care_circle")
            db.add(post2)
            db.flush()
            db.add(PostComment(post_id=post1.id, author_id=nadia.id, content="So proud of you, Mom!"))

        # ---------- family chat ----------
        family_conv = (
            db.query(Conversation).filter(Conversation.conversation_type == "family",
                                          Conversation.care_circle_id == circle.id).first()
        )
        if family_conv is None:
            family_conv = Conversation(conversation_type="family", title="Rahima's Family",
                                       care_circle_id=circle.id)
            db.add(family_conv)
            db.flush()
            db.add_all([
                ConversationMember(conversation_id=family_conv.id, user_id=rahma.id),
                ConversationMember(conversation_id=family_conv.id, user_id=nadia.id),
            ])
            db.add_all([
                Message(conversation_id=family_conv.id, sender_id=nadia.id,
                        content="Good morning Mom! How did you sleep?"),
                Message(conversation_id=family_conv.id, sender_id=rahma.id,
                        content="Good morning dear! Slept well, about 7 hours. Heading out for my walk."),
                Message(conversation_id=family_conv.id, sender_id=nadia.id,
                        content="Wonderful! Call me if you need anything."),
            ])

        # ---------- AI companion starter ----------
        if db.query(AiConversation).filter(AiConversation.user_id == rahma.id).count() == 0:
            conv = AiConversation(user_id=rahma.id, title="About my blood pressure")
            db.add(conv)
            db.flush()
            db.add_all([
                AiMessage(conversation_id=conv.id, sender="assistant",
                          content="Hello Rahima! I'm CareMind, your companion. "
                                  "How are you feeling today?"),
                AiMessage(conversation_id=conv.id, sender="user",
                          content="My blood pressure has been a bit high lately. Should I worry?"),
                AiMessage(conversation_id=conv.id, sender="assistant",
                          content="I looked at your readings, Rahima. They've been trending from about "
                                  "132/84 to 145/90 over two weeks. One reading isn't a diagnosis, but I'd "
                                  "gently suggest mentioning it to Dr. Rahman — I can help you book that. "
                                  "In the meantime, keep taking Amlodipine as prescribed."),
            ])
            db.add(AiInsight(
                user_id=rahma.id, insight_type="blood_pressure", severity="info",
                title="Your blood pressure is trending upward",
                content="Last 3 readings: 141/88, 143/89, 145/90. Consider discussing with Dr. Rahman.",
            ))

        db.commit()
        print("[seed] CareMind demo data ready - login with rahma@ / nadia@ / doctor@caremind.demo")
    finally:
        db.close()
