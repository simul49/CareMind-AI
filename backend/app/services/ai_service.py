"""AI service — context-aware companion chat.

Works in two modes:
  1. Live mode: OpenAI-compatible chat completions (DeepSeek / Qwen / Hunyuan).
  2. Demo mode: scripted but context-aware replies (no API key needed).
"""

import json
import random
import re
import shutil
import subprocess

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import AiConversation, AiInsight, AiMessage, HealthMetric, Medicine, User

_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # main emoji blocks
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002600-\U000027BF"  # misc symbols & dingbats
    "\U0001F1E6-\U0001F1FF"  # flags
    "\U0000FE0F"             # variation selector
    "\U0000200D"             # zero-width joiner
    "\U00002300-\U000023FF"  # misc technical
    "\U00002B00-\U00002BFF"  # misc symbols/arrows
    "\U00002E80-\U00002EFF"  # CJK radicals (safety net)
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U00002700-\U000027BF"  # dingbats
    "\U00002190-\U000021FF"  # arrows
    "\U000020B0-\U00002BFF"  # currency-ish misc
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    """Remove emoji/pictograms from AI text so replies stay clear for elders."""
    if not text:
        return text
    cleaned = _EMOJI_RE.sub("", text)
    # Collapse leftover double spaces from removed glyphs
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


SAFETY_RULES = (
    "You are CareMind Companion, a caring health assistant for older adults. "
    "Rules you MUST follow:\n"
    "1. NEVER diagnose, prescribe, or contradict a doctor. Encourage seeing the doctor when uncertain.\n"
    "2. Respond in plain, warm, simple language — the user may be 70+ years old. Use short sentences. "
    "NEVER use emojis or pictograms — plain text only (write words, not symbols).\n"
    "3. If the user reports chest pain, severe breathing trouble, fainting, or stroke signs, tell them to "
    "call emergency services immediately.\n"
    "4. If the user asks about medication, remind them to follow their doctor's instructions.\n"
    "5. If you are unsure, say 'I'm not sure — let's ask your doctor.'\n"
)


def _metric_values(metric: HealthMetric) -> dict:
    bp = metric.blood_pressure
    hr = metric.heart_rate
    glu = metric.glucose
    w = metric.weight
    sl = metric.sleep
    act = metric.activity
    mo = metric.mood
    if bp:
        return {"systolic": bp.systolic, "diastolic": bp.diastolic, "pulse": bp.pulse}
    if hr:
        return {"bpm": hr.bpm}
    if glu:
        return {"value_mg_dl": glu.value_mg_dl, "context": glu.measurement_context}
    if w:
        return {"kg": w.kg}
    if sl:
        return {"sleep_hours": sl.sleep_hours, "quality": sl.quality}
    if act:
        return {"activity_type": act.activity_type, "steps": act.steps}
    if mo:
        return {"mood_level": mo.mood_level, "note": mo.note}
    return {}


def _build_context(db: Session, user_id: int) -> str:
    lines = []
    metrics = (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user_id)
        .order_by(HealthMetric.measured_at.desc())
        .limit(12)
        .all()
    )
    for m in metrics:
        v = _metric_values(m)
        if v:
            lines.append(f"{m.measured_at.strftime('%Y-%m-%d %H:%M')} {m.metric_type}: {json.dumps(v)}")

    meds = (
        db.query(Medicine)
        .filter(Medicine.user_id == user_id, Medicine.active.is_(True))
        .all()
    )
    med_lines = [f"{m.name} {m.dosage or ''}{m.dosage_unit} ({m.frequency or 'as directed'})" for m in meds]
    if med_lines:
        lines.append("Current medicines: " + "; ".join(med_lines))

    insights = (
        db.query(AiInsight)
        .filter(AiInsight.user_id == user_id)
        .order_by(AiInsight.created_at.desc())
        .limit(5)
        .all()
    )
    for i in insights:
        lines.append(f"[Insight] {i.title}: {i.content}")

    return "\n".join(lines) if lines else "No recent health data recorded."


def _curl_chat(url: str, payload: dict) -> dict | None:
    """Fallback transport via curl — some Windows Python builds fail TLS
    (OpenSSL UNEXPECTED_EOF) against certain providers' CDNs, while curl
    (Schannel) succeeds. Cheap insurance for a hackathon demo."""
    exe = shutil.which("curl") or "curl"
    try:
        proc = subprocess.run(
            [
                exe, "-sS", "--max-time", str(int(settings.AI_TIMEOUT_SECONDS)),
                "-X", "POST", url,
                "-H", f"Authorization: Bearer {settings.AI_API_KEY}",
                "-H", "Content-Type: application/json",
                "--data-binary", json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            timeout=int(settings.AI_TIMEOUT_SECONDS) + 5,
        )
        if proc.returncode != 0:
            return None
        return json.loads(proc.stdout)
    except Exception:
        return None


def _live_chat(messages: list[dict]) -> str | None:
    if not settings.AI_API_KEY:
        return None
    url = settings.AI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.AI_MODEL,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 600,
    }
    data = None
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=settings.AI_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        data = _curl_chat(url, payload)
    try:
        return _strip_emoji(data["choices"][0]["message"]["content"].strip())
    except Exception:
        return None


_DEMO_REPLIES = [
    "I'm here with you, {name}. From what you've shared, here's what I understand… "
    "I'd gently suggest we keep an eye on it and mention it to Dr. Rahman at your next visit. "
    "Would you like me to note this down for the doctor?",
    "That's a great question, {name}. Based on your recent records, I see a few things worth watching. "
    "I always recommend confirming with your doctor before changing anything.",
    "I hear you, {name}. Let's keep it simple: rest, stay hydrated, and if anything feels worse, "
    "let's call your doctor together. I can send a summary of how you're feeling to your family.",
    "Thank you for telling me, {name}. Your blood pressure readings over the last two weeks have been "
    "fairly stable. Remember to take your medicine as Dr. Rahman prescribed. Want me to remind you?",
]

_DEMO_REPLIES_ZH = [
    "{name}，我一直在陪着你。根据你分享的情况，我的理解是这样的……建议我们先观察几天，"
    "下次见 Rahman 医生时和他提一下。需要我帮你记下来给医生看吗？",
    "{name}，这是个很好的问题。根据最近的记录，我看到有几个地方值得留意。"
    "任何改变之前，我都建议先和你的医生确认。",
    "我听到了，{name}。我们慢慢来：好好休息、多喝水，如果感觉更难受了，"
    "我们一起给你的医生打电话。我也可以把你的感受告诉家人。",
    "谢谢你告诉我，{name}。最近两周你的血压读数比较平稳。记得按 Rahman 医生的吩咐按时吃药。需要我提醒你吗？",
]


def _demo_chat(user: User, latest: str, lang: str = "en") -> str:
    first = user.full_name.split()[0]
    text = latest.lower()
    if lang == "zh":
        if any(w in text for w in ["胸", "呼吸", "晕", "摔倒", "中风", "昏倒", "喘不过气"]):
            return (
                f"{first}，听起来情况比较严重。请立刻拨打急救电话（120），"
                "或者按下 App 里的 SOS 按钮。我会马上通知你的家人。我一直在这里陪着你。"
            )
        if any(w in text for w in ["药", "吃药", "用药", "剂量", "服药"]):
            return (
                f"关于你的药，{first}：一定要严格按 Rahman 医生的嘱咐服用。"
                "你今晚 8 点还有一次（氨氯地平）。需要我帮你设个提醒吗？"
                "千万不要在没问医生的情况下停药或改药。"
            )
        if any(w in text for w in ["血压", "高压", "低压", "偏高"]):
            return (
                f"我看了你的血压记录，{first}。过去两周略有上升（从大约 132/84 到 145/90）。"
                "一次读数不能说明问题，但建议你下次见 Rahman 医生时提一下。"
                "我也可以把它加到健康时间线里，方便复诊时查看。"
            )
        if any(w in text for w in ["睡", "失眠", "困", "入睡"]):
            return (
                f"睡眠太重要了，{first}。昨晚你记录了大约 7 小时 — 这是不错的信号。"
                "睡前放松一下（喝杯温水，提前一小时放下手机）通常会有帮助。"
                "如果失眠超过一周，我们一起告诉医生。"
            )
        return _strip_emoji(random.choice(_DEMO_REPLIES_ZH).format(name=first))
    if any(w in text for w in ["chest", "breath", "faint", "fall", "stroke", "breathe"]):
        return (
            f"{first}, that sounds serious. Please call emergency services right now "
            "(911 or your local number), or press the SOS button on the app. I'll alert your family. "
            "I'm here with you."
        )
    if any(w in text for w in ["medicine", "pill", "medication", "dose"]):
        return (
            f"About your medicine, {first}: always follow Dr. Rahman's instructions exactly. "
            "You have a dose at 8:00 PM tonight (Amlodipine). Should I add a reminder for you? "
            "Never stop or change a medicine without asking your doctor first."
        )
    if any(w in text for w in ["blood pressure", "bp", "systolic", "high"]):
        return (
            f"I looked at your blood pressure history, {first}. It has been trending slightly upward over "
            "the past two weeks (from about 132/84 to 145/90). One reading is not a diagnosis — but I'd "
            "recommend mentioning this to Dr. Rahman. I can also add it to the health timeline for your "
            "next visit."
        )
    if any(w in text for w in ["sleep", "tired", "insomnia"]):
        return (
            f"Sleep matters so much, {first}. Last night you logged about 7 hours — that's a good sign. "
            "A gentle wind-down routine (warm drink, no screens an hour before bed) often helps. "
            "If poor sleep continues for more than a week, let's tell the doctor."
        )
    return _strip_emoji(random.choice(_DEMO_REPLIES).format(name=first))


_LANG_HINT = {
    "zh": "语言要求：请始终用简体中文回复，语气温暖亲切，句子简短，像对家人说话一样。",
    "en": "Language: always reply in English with warm, simple, short sentences.",
}


def chat_with_user(
    user: User, conversation_id: int | None, message: str, lang: str = "en"
) -> tuple[int, str, list[str]]:
    db = SessionLocal()
    try:
        conv = None
        if conversation_id:
            conv = db.get(AiConversation, conversation_id)
            if conv is None or conv.user_id != user.id:
                conv = None
        if conv is None:
            title = message[:40] + ("…" if len(message) > 40 else "")
            conv = AiConversation(user_id=user.id, title=title)
            db.add(conv)
            db.flush()

        history = (
            db.query(AiMessage)
            .filter(AiMessage.conversation_id == conv.id)
            .order_by(AiMessage.id.asc())
            .limit(20)
            .all()
        )

        db.add(AiMessage(conversation_id=conv.id, sender="user", content=message))
        db.commit()

        context = _build_context(db, user.id)
        lang_hint = _LANG_HINT.get(lang, _LANG_HINT["en"])
        system = SAFETY_RULES + "\n\n" + lang_hint + "\n\nKnown user health context (do not repeat verbatim):\n" + context

        msgs = [{"role": "system", "content": system}]
        for h in history:
            msgs.append({"role": "assistant" if h.sender == "assistant" else "user", "content": h.content})
        msgs.append({"role": "user", "content": message})

        reply = _live_chat(msgs)
        if not reply:
            reply = _demo_chat(user, message, lang)

        db.add(AiMessage(conversation_id=conv.id, sender="assistant", content=reply))
        db.commit()
        sources = ["health_timeline", "medication_schedule"] if settings.AI_API_KEY else []
        return conv.id, reply, sources
    finally:
        db.close()


def list_conversations(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        convs = (
            db.query(AiConversation)
            .filter(AiConversation.user_id == user_id)
            .order_by(AiConversation.updated_at.desc())
            .limit(20)
            .all()
        )
        out = []
        for c in convs:
            last = (
                db.query(AiMessage)
                .filter(AiMessage.conversation_id == c.id)
                .order_by(AiMessage.id.desc())
                .first()
            )
            out.append({"id": c.id, "title": c.title, "created_at": c.created_at.isoformat(),
                        "preview": last.content[:60] if last else ""})
        return out
    finally:
        db.close()


def list_messages(conversation_id: int, user_id: int) -> list[dict] | None:
    db = SessionLocal()
    try:
        conv = db.get(AiConversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            return None
        rows = (
            db.query(AiMessage)
            .filter(AiMessage.conversation_id == conversation_id)
            .order_by(AiMessage.id.asc())
            .all()
        )
        return [{"id": m.id, "sender": m.sender, "content": m.content,
                 "created_at": m.created_at.isoformat()} for m in rows]
    finally:
        db.close()
