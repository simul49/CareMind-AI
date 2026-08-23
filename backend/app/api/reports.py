"""Health report upload + AI-assisted analysis.

For the hackathon, uploads are stored locally and "analysis" runs a rule-based
parser on the filename/meta (mock). Wiring a real OCR/LLM pipeline is a Day-3
upgrade — the API contract won't change.
"""

import json
import os
import uuid
from datetime import datetime, date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.config import settings
from app.models.models import AiInsight, HealthReport, ReportResult, User
from app.api.deps import get_current_user
from app.schemas.common import ReportOut
from app.services.ai_service import _live_chat

router = APIRouter(prefix="/reports", tags=["reports"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
ALLOWED = {".pdf", ".png", ".jpg", ".jpeg"}

# Demo rule-based analysis for common lab items
_FLAG_RULES = {
    "hemoglobin": ("low", 120.0, 160.0),
    "glucose": ("high", 70.0, 110.0),
    "cholesterol": ("high", 0.0, 200.0),
    "ldl": ("high", 0.0, 100.0),
    "creatinine": ("high", 0.6, 1.2),
    "potassium": ("high", 3.5, 5.2),
}


def _parse_value(text: str) -> float | None:
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _enrich_summary(report: HealthReport, findings: list[dict]) -> str | None:
    """Ask the live AI to reword the analysis for a 70+ reader (no-op without a key)."""
    if not settings.AI_API_KEY:
        return None
    rows = "\n".join(
        f"- {f['item']}: {f['value']} {f['unit']} (typical {f['range']} — {f['flag']})"
        for f in findings
    )
    msgs = [
        {"role": "system", "content": (
            "You are CareMind, a caring health assistant explaining lab results to a 70+ year old. "
            "Write a short, warm explanation (max 110 words) in plain language with short sentences. "
            "Mention any flagged values gently, state clearly this is not a diagnosis, and suggest "
            "discussing them with the doctor. Use a friendly emoji at the end."
        )},
        {"role": "user", "content": f"Report '{report.title}':\n{rows}"},
    ]
    try:
        reply = _live_chat(msgs)
        return reply if reply and reply.strip() else None
    except Exception:
        return None


def _analyze(report: HealthReport) -> None:
    """Mock analysis: extract a couple of demo findings from the filename."""
    name = (report.original_filename or "").lower()
    findings = []
    if "blood" in name or "lab" in name:
        findings = [
            {"item": "Hemoglobin", "value": "11.8", "unit": "g/dL", "range": "12.0 – 16.0", "flag": "low"},
            {"item": "Fasting Glucose", "value": "118", "unit": "mg/dL", "range": "70 – 110", "flag": "high"},
            {"item": "Total Cholesterol", "value": "194", "unit": "mg/dL", "range": "< 200", "flag": "normal"},
        ]
    elif "thyroid" in name:
        findings = [
            {"item": "TSH", "value": "4.9", "unit": "mIU/L", "range": "0.4 – 4.0", "flag": "high"},
            {"item": "T4", "value": "8.1", "unit": "µg/dL", "range": "5.0 – 12.0", "flag": "normal"},
        ]
    else:
        findings = [
            {"item": "Hemoglobin", "value": "12.4", "unit": "g/dL", "range": "12.0 – 16.0", "flag": "normal"},
            {"item": "Fasting Glucose", "value": "96", "unit": "mg/dL", "range": "70 – 110", "flag": "normal"},
            {"item": "Creatinine", "value": "1.1", "unit": "mg/dL", "range": "0.6 – 1.2", "flag": "normal"},
        ]

    flagged = [f for f in findings if f["flag"] != "normal"]
    for f in findings:
        db = SessionLocal()
        try:
            db.add(ReportResult(
                report_id=report.id, item_name=f["item"], result_value=f["value"],
                unit=f["unit"], reference_range=f["range"], flag=f["flag"],
                interpretation=(
                    "Below reference range." if f["flag"] == "low"
                    else "Above reference range." if f["flag"] == "high"
                    else "Within normal range."
                ),
            ))
            db.commit()
        finally:
            db.close()

    if flagged:
        names = ", ".join(f["item"] for f in flagged)
        summary = (
            f"CareMind found {len(flagged)} value(s) outside the typical range: {names}. "
            "This is not a diagnosis. Please review these with Dr. Rahman."
        )
        db = SessionLocal()
        try:
            db.add(AiInsight(
                user_id=report.user_id, insight_type="report", severity="warning",
                title="Report review: a few values to discuss",
                content=summary,
            ))
            db.commit()
        finally:
            db.close()
    else:
        summary = "All values are within the typical reference range. Keep up the great routine!"

    # Live-AI enrichment: when an AI key is configured, rewrite the summary in
    # warm, plain language for the elder. Falls back to the rule-based summary.
    enriched = _enrich_summary(report, findings)
    if enriched:
        summary = enriched

    report.summary = summary
    report.status = "analyzed"
    report.analyzed_at = datetime.utcnow()


@router.post("/upload", response_model=ReportOut)
def upload_report(
    title: str = Form(""),
    report_type: str = Form("other"),
    report_date: str | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            "Only PDF, PNG or JPG reports are supported")
    UPLOAD_DIR.mkdir(exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / stored_name
    dest.write_bytes(file.file.read())

    rdate = None
    if report_date:
        try:
            rdate = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            rdate = None

    report = HealthReport(
        user_id=user.id, title=title or file.filename, report_date=rdate or date.today(),
        report_type=report_type, file_path=str(dest), original_filename=file.filename,
        uploaded_by=user.id, status="uploaded",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    _analyze(report)
    db.commit()
    db.refresh(report)
    return _report_out(report)


@router.get("", response_model=list[ReportOut])
def list_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(HealthReport)
        .filter(HealthReport.user_id == user.id)
        .order_by(HealthReport.created_at.desc())
        .limit(20)
        .all()
    )
    return [_report_out(r) for r in rows]


@router.get("/{report_id}")
def report_detail(report_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(HealthReport, report_id)
    if report is None or report.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    results = db.query(ReportResult).filter(ReportResult.report_id == report_id).all()
    return {
        **_report_out(report).model_dump(),
        "results": [
            {"item_name": r.item_name, "result_value": r.result_value, "unit": r.unit,
             "reference_range": r.reference_range, "flag": r.flag, "interpretation": r.interpretation}
            for r in results
        ],
    }


def _report_out(report: HealthReport) -> ReportOut:
    return ReportOut(
        id=report.id, title=report.title, report_date=report.report_date.isoformat() if report.report_date else None,
        report_type=report.report_type, original_filename=report.original_filename,
        summary=report.summary, status=report.status, analyzed_at=report.analyzed_at,
    )
