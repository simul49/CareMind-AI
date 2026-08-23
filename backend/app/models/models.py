"""SQLAlchemy models — full port of schema.sql (CareMind AI v2.1)."""

from datetime import datetime, date, time

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

# ---------------------------------------------------------------- enums
ROLES = ("elder", "family", "doctor", "caregiver")
GENDERS = ("male", "female", "other", "prefer_not_to_say")
RELATIONSHIP_TYPES = ("self", "spouse", "son", "daughter", "caregiver", "other")
STATUS_PENDING = "pending"
STATUS_CONFIRMED = "confirmed"
STATUS_REJECTED = "rejected"
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------- identity
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)  # elder/family/doctor/caregiver
    name = Column(String(50), nullable=False)

    users = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    role = relationship("Role", back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    emergency_contacts = relationship("EmergencyContact", back_populates="elder")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    avatar_url = Column(String(500))
    date_of_birth = Column(Date)
    gender = Column(String(20), default="prefer_not_to_say")
    address = Column(String(255))
    city = Column(String(100))
    primary_language = Column(String(50), default="english")
    emergency_notes = Column(Text)
    medical_conditions = Column(Text)
    allergies = Column(Text)
    current_medications = Column(Text)
    primary_doctor_id = Column(Integer, ForeignKey("doctors.id"))
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    is_accessible_mode = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile")


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    license_number = Column(String(50))
    specialty = Column(String(100))
    hospital = Column(String(150))
    department = Column(String(100))
    years_experience = Column(Integer)
    consultation_start = Column(Time)
    consultation_end = Column(Time)
    bio = Column(Text)

    user = relationship("User")
    patients = relationship("DoctorPatientRelationship", back_populates="doctor")
    care_plans = relationship("DoctorCarePlan", back_populates="doctor")


class CareCircle(Base, TimestampMixin):
    __tablename__ = "care_circles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitation_code = Column(String(20), unique=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    members = relationship("CareCircleMember", back_populates="care_circle")


class CareCircleMember(Base):
    __tablename__ = "care_circle_members"
    __table_args__ = (UniqueConstraint("care_circle_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    care_circle_id = Column(Integer, ForeignKey("care_circles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_type = Column(String(20), default="other")
    joined_at = Column(DateTime, default=datetime.utcnow)

    care_circle = relationship("CareCircle", back_populates="members")
    user = relationship("User")


class DoctorPatientRelationship(Base, TimestampMixin):
    __tablename__ = "doctor_patient_relationships"
    __table_args__ = (UniqueConstraint("doctor_id", "patient_user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_status = Column(String(20), default=STATUS_CONFIRMED)

    doctor = relationship("Doctor", back_populates="patients")
    patient = relationship("User")


class Consent(Base, TimestampMixin):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String(50))
    content_version = Column(String(20))
    signed_at = Column(DateTime)


# ---------------------------------------------------------------- health data
class HealthMetric(Base, TimestampMixin):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # blood_pressure/heart_rate/glucose/spo2/temperature/weight/water/sleep/mood/activity
    source = Column(String(50), default="manual")
    measured_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    blood_pressure = relationship("BloodPressureRecord", back_populates="metric", uselist=False)
    heart_rate = relationship("HeartRateRecord", back_populates="metric", uselist=False)
    glucose = relationship("GlucoseRecord", back_populates="metric", uselist=False)
    spo2 = relationship("SpO2Record", back_populates="metric", uselist=False)
    temperature = relationship("TemperatureRecord", back_populates="metric", uselist=False)
    weight = relationship("WeightRecord", back_populates="metric", uselist=False)
    water = relationship("WaterRecord", back_populates="metric", uselist=False)
    sleep = relationship("SleepRecord", back_populates="metric", uselist=False)
    mood = relationship("MoodRecord", back_populates="metric", uselist=False)
    activity = relationship("ActivityRecord", back_populates="metric", uselist=False)


class BloodPressureRecord(Base):
    __tablename__ = "blood_pressure_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    systolic = Column(Integer, nullable=False)
    diastolic = Column(Integer, nullable=False)
    pulse = Column(Integer)

    metric = relationship("HealthMetric", back_populates="blood_pressure")


class HeartRateRecord(Base):
    __tablename__ = "heart_rate_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    bpm = Column(Integer, nullable=False)

    metric = relationship("HealthMetric", back_populates="heart_rate")


class GlucoseRecord(Base):
    __tablename__ = "glucose_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    value_mg_dl = Column(Float, nullable=False)
    measurement_context = Column(String(20), default="fasting")  # fasting/post_meal/random

    metric = relationship("HealthMetric", back_populates="glucose")


class SpO2Record(Base):
    __tablename__ = "spo2_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    percent = Column(Integer, nullable=False)

    metric = relationship("HealthMetric", back_populates="spo2")


class TemperatureRecord(Base):
    __tablename__ = "temperature_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    celsius = Column(Float, nullable=False)

    metric = relationship("HealthMetric", back_populates="temperature")


class WeightRecord(Base):
    __tablename__ = "weight_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    kg = Column(Float, nullable=False)

    metric = relationship("HealthMetric", back_populates="weight")


class WaterRecord(Base):
    __tablename__ = "water_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    ml = Column(Integer, nullable=False)

    metric = relationship("HealthMetric", back_populates="water")


class SleepRecord(Base):
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    sleep_hours = Column(Float, nullable=False)
    quality = Column(String(20))  # excellent/good/fair/poor

    metric = relationship("HealthMetric", back_populates="sleep")


class MoodRecord(Base):
    __tablename__ = "mood_records"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    mood_level = Column(Integer, nullable=False)  # 1..5
    note = Column(String(255))

    metric = relationship("HealthMetric", back_populates="mood")


class ActivityRecord(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("health_metrics.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # walk/badminton/cycling/...
    steps = Column(Integer, default=0)
    duration_minutes = Column(Integer)
    distance_km = Column(Float)
    calories = Column(Integer)
    note = Column(String(255))

    metric = relationship("HealthMetric", back_populates="activity")


class Symptom(Base, TimestampMixin):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptom_type = Column(String(50), nullable=False)
    severity = Column(Integer)  # 1..5
    duration_days = Column(Integer)
    notes = Column(Text)
    reported_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------- medicines
class Medicine(Base, TimestampMixin):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # prescription/otc/supplement
    dosage = Column(String(50))
    dosage_unit = Column(String(20), default="mg")
    frequency = Column(String(50))
    instructions = Column(Text)
    food_requirement = Column(String(50))  # before_food/after_food/with_food/any
    start_date = Column(Date)
    end_date = Column(Date)
    active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    schedules = relationship("MedicationSchedule", back_populates="medicine", cascade="all, delete-orphan")
    logs = relationship("MedicationLog", back_populates="medicine")


class MedicationSchedule(Base, TimestampMixin):
    __tablename__ = "medication_schedules"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    scheduled_time = Column(Time, nullable=False)
    dosage_amount = Column(Float)
    dosage_unit = Column(String(20), default="mg")
    repeat_days = Column(String(50), default="all")  # all or comma list 0-6
    active = Column(Boolean, default=True)

    medicine = relationship("Medicine", back_populates="schedules")
    logs = relationship("MedicationLog", back_populates="schedule")


class MedicationLog(Base, TimestampMixin):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("medication_schedules.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    taken_at = Column(DateTime)
    status = Column(String(20), default="pending")  # pending/taken/skipped/missed/reminded
    reminder_sent_at = Column(DateTime)
    note = Column(String(255))

    medicine = relationship("Medicine", back_populates="logs")
    schedule = relationship("MedicationSchedule", back_populates="logs")


# ---------------------------------------------------------------- reports
class HealthReport(Base, TimestampMixin):
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150))
    report_date = Column(Date)
    report_type = Column(String(50))  # lab/blood/imaging/discharge/other
    file_path = Column(String(500))
    original_filename = Column(String(255))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    summary = Column(Text)
    status = Column(String(20), default="uploaded")  # uploaded/analyzing/analyzed/failed
    analyzed_at = Column(DateTime)

    results = relationship("ReportResult", back_populates="report")


class ReportResult(Base, TimestampMixin):
    __tablename__ = "report_results"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("health_reports.id"), nullable=False)
    item_name = Column(String(150), nullable=False)
    result_value = Column(String(50))
    unit = Column(String(30))
    reference_range = Column(String(80))
    flag = Column(String(20), default="normal")  # normal/low/high/critical
    interpretation = Column(Text)

    report = relationship("HealthReport", back_populates="results")


# ---------------------------------------------------------------- social
class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500))
    visibility = Column(String(20), default="care_circle")  # care_circle/family/doctor/public
    care_circle_id = Column(Integer, ForeignKey("care_circles.id"))

    author = relationship("User")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("PostReaction", back_populates="post", cascade="all, delete-orphan")


class PostComment(Base, TimestampMixin):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)

    post = relationship("Post", back_populates="comments")


class PostReaction(Base, TimestampMixin):
    __tablename__ = "post_reactions"
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reaction_type = Column(String(20), default="like")  # like/love/care/haha/wow

    post = relationship("Post", back_populates="reactions")


# ---------------------------------------------------------------- chat
class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_type = Column(String(20), default="family")  # family/doctor/caregiver
    title = Column(String(100))
    care_circle_id = Column(Integer, ForeignKey("care_circles.id"))

    members = relationship("ConversationMember", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")


class ConversationMember(Base):
    __tablename__ = "conversation_members"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="members")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text/image/system
    read_by = Column(Text)  # JSON array of user ids

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")


# ---------------------------------------------------------------- appointments & care plans
class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    elder_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    appointment_type = Column(String(30), default="in_person")  # in_person/video/phone
    status = Column(String(20), default="scheduled")  # scheduled/completed/cancelled
    reason = Column(Text)
    summary = Column(Text)


class DoctorCarePlan(Base, TimestampMixin):
    __tablename__ = "doctor_care_plans"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    elder_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default=STATUS_ACTIVE)

    doctor = relationship("Doctor", back_populates="care_plans")


# ---------------------------------------------------------------- emergency
class EmergencyContact(Base, TimestampMixin):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    elder_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    relationship_type = Column(String(30))
    phone = Column(String(20), nullable=False)
    is_primary = Column(Boolean, default=False)

    elder = relationship("User", back_populates="emergency_contacts")


class EmergencyEvent(Base, TimestampMixin):
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    elder_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trigger_type = Column(String(30), default="manual")  # manual/fall_sensor/voice
    status = Column(String(20), default="active")  # active/resolving/resolved
    location_lat = Column(Float)
    location_lng = Column(Float)
    location_label = Column(String(255))
    started_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    summary = Column(Text)

    logs = relationship("EmergencyLog", back_populates="event", cascade="all, delete-orphan")


class EmergencyLog(Base, TimestampMixin):
    __tablename__ = "emergency_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("emergency_events.id"), nullable=False)
    log_type = Column(String(30), nullable=False)  # contact_notified/sms/call/created/resolved
    detail = Column(Text)

    event = relationship("EmergencyEvent", back_populates="logs")


# ---------------------------------------------------------------- AI
class AiConversation(Base, TimestampMixin):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), default="New conversation")
    context_snapshot = Column(Text)  # JSON snapshot of health context

    messages = relationship("AiMessage", back_populates="conversation", order_by="AiMessage.id")


class AiMessage(Base, TimestampMixin):
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # user/assistant
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON

    conversation = relationship("AiConversation", back_populates="messages")


class AiInsight(Base, TimestampMixin):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    insight_type = Column(String(50), nullable=False)  # blood_pressure/sleep/medication/activity/report
    title = Column(String(150))
    content = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info/warning/critical
    source_data = Column(Text)
    is_read = Column(Boolean, default=False)


# ---------------------------------------------------------------- misc
class RiskScore(Base, TimestampMixin):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)  # 0-100
    risk_type = Column(String(30), default="overall")
    factors = Column(Text)
    calculated_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    body = Column(Text)
    notification_type = Column(String(30))  # medicine/health/emergency/social/doctor
    is_read = Column(Boolean, default=False)
    related_id = Column(Integer)


class WellnessChallengeLog(Base):
    """One row per completed daily wellness challenge (Day 3 feature)."""
    __tablename__ = "wellness_challenge_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_key = Column(String(64), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    detail = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
