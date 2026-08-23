from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------- health ----------------
class BloodPressureIn(BaseModel):
    systolic: int
    diastolic: int
    pulse: int | None = None
    measured_at: datetime | None = None


class HeartRateIn(BaseModel):
    bpm: int
    measured_at: datetime | None = None


class GlucoseIn(BaseModel):
    value_mg_dl: float
    measurement_context: str = "fasting"
    measured_at: datetime | None = None


class WeightIn(BaseModel):
    kg: float
    measured_at: datetime | None = None


class ActivityIn(BaseModel):
    activity_type: str = "walk"
    steps: int = 0
    duration_minutes: int | None = None
    distance_km: float | None = None
    calories: int | None = None
    note: str | None = None
    measured_at: datetime | None = None


class SleepIn(BaseModel):
    sleep_hours: float
    quality: str = "good"
    start_time: datetime | None = None
    end_time: datetime | None = None
    measured_at: datetime | None = None


class MoodIn(BaseModel):
    mood_level: int = Field(ge=1, le=5)
    note: str | None = None
    measured_at: datetime | None = None


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metric_type: str
    measured_at: datetime
    values: dict = {}


# ---------------- medicine ----------------
class MedicineIn(BaseModel):
    name: str
    dosage: str | None = None
    dosage_unit: str = "mg"
    frequency: str | None = None
    instructions: str | None = None
    food_requirement: str = "any"
    active: bool = True


class ScheduleIn(BaseModel):
    scheduled_time: str  # HH:MM
    dosage_amount: float | None = None
    dosage_unit: str = "mg"


class MedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dosage: str | None = None
    dosage_unit: str = "mg"
    instructions: str | None = None
    food_requirement: str = "any"
    active: bool


class DoseOut(BaseModel):
    log_id: int
    medicine_id: int
    medicine_name: str
    dosage: str | None = None
    scheduled_time: str
    scheduled_for: datetime
    status: str
    taken_at: datetime | None = None
    instructions: str | None = None
    food_requirement: str = "any"


# ---------------- AI ----------------
class ChatIn(BaseModel):
    conversation_id: int | None = None
    message: str


class ChatOut(BaseModel):
    conversation_id: int
    reply: str
    sources: list[str] = []


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    preview: str = ""


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    insight_type: str
    title: str
    content: str
    severity: str
    is_read: bool
    created_at: datetime


# ---------------- emergency ----------------
class EmergencyTriggerIn(BaseModel):
    trigger_type: str = "manual"
    location_label: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None


class EmergencyContactIn(BaseModel):
    name: str
    relationship_type: str = "family"
    phone: str
    is_primary: bool = False


# ---------------- social ----------------
class PostIn(BaseModel):
    content: str
    visibility: str = "care_circle"


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    author_name: str = ""
    content: str
    image_url: str | None = None
    created_at: datetime
    reaction_count: int = 0
    my_reaction: str | None = None


# ---------------- chat ----------------
class FamilyMessageIn(BaseModel):
    conversation_id: int
    content: str


class FamilyMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    sender_name: str = ""
    content: str
    created_at: datetime


# ---------------- report ----------------
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    report_date: str | None = None
    report_type: str = "other"
    original_filename: str | None = None
    summary: str | None = None
    status: str
    analyzed_at: datetime | None = None
