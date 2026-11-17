from datetime import datetime, timezone
import secrets

from sqlalchemy import CheckConstraint, UniqueConstraint

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("role IN ('participante', 'professor', 'admin')", name="ck_usuario_role"),
        CheckConstraint("status IN ('pendente', 'aprovado', 'bloqueado')", name="ck_usuario_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    google_sub = db.Column(db.String(255), nullable=True, unique=True)
    role = db.Column(db.String(20), nullable=False, default="participante")
    status = db.Column(db.String(20), nullable=False, default="pendente")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    participant = db.relationship("Participant", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Participant(db.Model):
    __tablename__ = "participantes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_name = db.Column(db.String(160), nullable=False)
    cpf = db.Column(db.String(11), nullable=False, unique=True, index=True)
    registration_number = db.Column(db.String(40), nullable=False, unique=True, index=True)
    course = db.Column(db.String(120), nullable=False)
    qr_token = db.Column(db.String(64), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(32))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    user = db.relationship("User", back_populates="participant")
    attendances = db.relationship("Attendance", back_populates="participant", cascade="all, delete-orphan")
    certificates = db.relationship("Certificate", back_populates="participant", cascade="all, delete-orphan")


class Event(db.Model):
    __tablename__ = "eventos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    theme = db.Column(db.String(255), nullable=True)
    starts_at = db.Column(db.Date, nullable=False)
    ends_at = db.Column(db.Date, nullable=False)
    total_hours = db.Column(db.Numeric(5, 2), nullable=False)
    minimum_attendance_percent = db.Column(db.Numeric(5, 2), nullable=False, default=75.00)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    days = db.relationship("EventDay", back_populates="event", cascade="all, delete-orphan")
    certificates = db.relationship("Certificate", back_populates="event", cascade="all, delete-orphan")


class EventDay(db.Model):
    __tablename__ = "dias_evento"
    __table_args__ = (UniqueConstraint("event_id", "event_date", name="uq_event_day_date"),)

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    label = db.Column(db.String(120), nullable=False)
    scheduled_hours = db.Column(db.Numeric(5, 2), nullable=False)

    event = db.relationship("Event", back_populates="days")
    attendances = db.relationship("Attendance", back_populates="event_day", cascade="all, delete-orphan")


class Attendance(db.Model):
    __tablename__ = "frequencias"
    __table_args__ = (UniqueConstraint("participant_id", "event_day_id", name="uq_participant_event_day"),)

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participantes.id", ondelete="CASCADE"), nullable=False)
    event_day_id = db.Column(db.Integer, db.ForeignKey("dias_evento.id", ondelete="CASCADE"), nullable=False)
    registered_by_user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    check_in_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    method = db.Column(db.String(20), nullable=False, default="manual")

    participant = db.relationship("Participant", back_populates="attendances")
    event_day = db.relationship("EventDay", back_populates="attendances")
    registered_by = db.relationship("User", foreign_keys=[registered_by_user_id])


class Certificate(db.Model):
    __tablename__ = "certificados"
    __table_args__ = (UniqueConstraint("participant_id", "event_id", name="uq_participant_event_certificate"),)

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participantes.id", ondelete="CASCADE"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False)
    verification_code = db.Column(db.String(48), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(24))
    workload_hours = db.Column(db.Numeric(5, 2), nullable=False)
    issued_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    private_file_name = db.Column(db.String(255), nullable=True)

    participant = db.relationship("Participant", back_populates="certificates")
    event = db.relationship("Event", back_populates="certificates")
