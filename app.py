
import os
import re
from functools import wraps
from pathlib import Path
from io import BytesIO

import qrcode
import click
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config import Config
from extensions import csrf, db, migrate
from models import Attendance, Certificate, Event, EventDay, Participant, User

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, template_folder=str(BASE_DIR), static_folder=None)
app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
oauth = OAuth(app)

GOOGLE_CONFIGURED = bool(app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"])
if GOOGLE_CONFIGURED:
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],
        client_kwargs={"scope": "openid email profile"},
    )


def cpf_digits(value):
    return re.sub(r"\D", "", value or "")


def valid_cpf(value):
    cpf = cpf_digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for length in (9, 10):
        total = sum(int(cpf[i]) * (length + 1 - i) for i in range(length))
        digit = (total * 10) % 11
        if digit == 10:
            digit = 0
        if digit != int(cpf[length]):
            return False
    return True


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect(url_for("login_page"))
        if user.status != "aprovado":
            session.clear()
            return render_template(
                "templates/access_denied.html",
                reason="Seu cadastro ainda não foi aprovado ou está bloqueado."
            ), 403
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            user = current_user()
            if user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_user():
    return {"logged_user": current_user()}


@app.get("/")
@app.get("/index.html")
def home():
    return render_template("index.html")


@app.get("/inscricao.html")
@app.get("/inscricao")
def registration_page():
    return render_template("inscricao.html")


@app.post("/inscricao.html")
@app.post("/inscricao")
def register_participant():
    full_name = " ".join(request.form.get("nome", "").split())
    email = request.form.get("email", "").strip().lower()
    cpf = cpf_digits(request.form.get("cpf", ""))
    registration_number = request.form.get("matricula", "").strip()
    course = " ".join(request.form.get("curso", "").split())

    if not all([full_name, email, cpf, registration_number, course]):
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Preencha todos os campos obrigatórios."
        ), 400

    if len(full_name) > 160 or len(email) > 254 or len(registration_number) > 40 or len(course) > 120:
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Um ou mais campos ultrapassam o tamanho permitido."
        ), 400

    if not valid_cpf(cpf):
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="O CPF informado não é válido. Confira os números e tente novamente."
        ), 400

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Informe um endereço de e-mail válido."
        ), 400

    if db.session.scalar(select(User.id).where(func.lower(User.email) == email)):
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Este e-mail já possui uma inscrição. Entre em contato com a organização."
        ), 409

    if db.session.scalar(select(Participant.id).where(Participant.cpf == cpf)):
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Este CPF já está associado a uma inscrição."
        ), 409

    if db.session.scalar(select(Participant.id).where(Participant.registration_number == registration_number)):
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Esta matrícula já está associada a uma inscrição."
        ), 409

    try:
        user = User(email=email, role="participante", status="pendente")
        participant = Participant(
            full_name=full_name,
            cpf=cpf,
            registration_number=registration_number,
            course=course,
            user=user,
        )
        db.session.add(user)
        db.session.add(participant)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Não foi possível concluir a inscrição porque algum dado já está cadastrado."
        ), 409

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Erro ao salvar inscrição")
        return render_template(
            "templates/registration_result.html",
            success=False,
            message="Ocorreu um erro ao salvar sua inscrição. Tente novamente mais tarde."
        ), 500

    return render_template(
        "templates/registration_result.html",
        success=True,
        message="Sua inscrição foi registrada e está aguardando validação da organização.",
        participant_name=full_name
    ), 201


@app.get("/login.html")
@app.get("/login")
def login_page():
    return render_template("login.html", google_configured=GOOGLE_CONFIGURED)


@app.get("/login/google")
def google_login():
    if not GOOGLE_CONFIGURED:
        return render_template(
            "login.html",
            google_configured=False,
            error="O acesso Google ainda está aguardando a configuração das credenciais da organização."
        ), 503

    callback_url = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(callback_url)


@app.get("/login/google/callback")
def google_callback():
    if not GOOGLE_CONFIGURED:
        abort(503)

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo") or oauth.google.userinfo()

    except Exception:
        app.logger.exception("Falha na autenticação Google")
        return render_template(
            "login.html",
            google_configured=True,
            error="Não foi possível validar sua conta Google. Tente novamente."
        ), 401

    google_sub = user_info.get("sub")
    email = (user_info.get("email") or "").strip().lower()
    email_verified = user_info.get("email_verified") is True

    if not google_sub or not email or not email_verified:
        return render_template(
            "templates/access_denied.html",
            reason="O Google não confirmou um e-mail válido para esta conta."
        ), 403

    user = db.session.scalar(select(User).where(User.google_sub == google_sub))

    if user is None:
        user = db.session.scalar(select(User).where(func.lower(User.email) == email))

        if user is None or user.status != "aprovado":
            return render_template(
                "templates/access_denied.html",
                reason="Esta conta Google não corresponde a um cadastro previamente aprovado."
            ), 403

        if user.google_sub and user.google_sub != google_sub:
            return render_template(
                "templates/access_denied.html",
                reason="Esta conta já está vinculada a outra identidade Google."
            ), 403

        user.google_sub = google_sub
        db.session.commit()

    if user.status != "aprovado":
        return render_template(
            "templates/access_denied.html",
            reason="Seu cadastro ainda não foi aprovado pela organização."
        ), 403

    session.clear()
    session["user_id"] = user.id
    return redirect(url_for("dashboard"))


@app.get("/painel")
@login_required
def dashboard():
    user = current_user()

    if user.role == "admin":
        return redirect(url_for("admin_panel"))

    if user.role == "professor":
        return redirect(url_for("professor_panel"))

    return redirect(url_for("participant_panel"))


@app.get("/aluno")
@roles_required("participante")
def participant_panel():
    user = current_user()
    participant = user.participant

    return render_template(
        "templates/dashboard_aluno.html",
        user=user,
        participant=participant
    )


@app.get("/participante/qr.png")
@roles_required("participante")
def participant_qr():
    participant = current_user().participant

    if not participant:
        abort(404)

    qr = qrcode.make(participant.qr_token)

    image = BytesIO()
    qr.save(image, format="PNG")
    image.seek(0)

    return send_file(image, mimetype="image/png")


@app.get("/professor")
@roles_required("professor", "admin")
def professor_panel():
    return render_template(
        "templates/dashboard_equipe.html",
        user=current_user(),
        profile="Professor"
    )


@app.post("/professor/identificar")
@roles_required("professor", "admin")
def identify_participant():
    qr_token = request.form.get("qr_token", "").strip()

    participant = db.session.scalar(
        select(Participant).where(Participant.qr_token == qr_token)
    )

    if not participant:
        flash("QR Code inválido ou participante não encontrado.", "error")
        return redirect(url_for("professor_panel"))

    event_days = db.session.scalars(
        select(EventDay).order_by(EventDay.event_date)
    ).all()

    return render_template(
        "templates/dashboard_equipe.html",
        user=current_user(),
        profile="Professor",
        scanned_participant=participant,
        event_days=event_days
    )


@app.post("/professor/confirmar")
@roles_required("professor", "admin")
def confirm_attendance():
    qr_token = request.form.get("qr_token", "").strip()
    event_day_id = request.form.get("event_day_id", type=int)

    participant = db.session.scalar(
        select(Participant).where(Participant.qr_token == qr_token)
    )

    event_day = db.session.get(EventDay, event_day_id)

    if not participant or not event_day:
        flash("Participante ou dia do evento inválido.", "error")
        return redirect(url_for("professor_panel"))

    attendance = Attendance(
        participant_id=participant.id,
        event_day_id=event_day.id,
        registered_by_user_id=current_user().id,
        method="qr"
    )

    try:
        db.session.add(attendance)
        db.session.commit()
        flash("Presença registrada com sucesso!", "success")

    except IntegrityError:
        db.session.rollback()
        flash("Este participante já possui presença registrada neste dia.", "error")

    return redirect(url_for("professor_panel"))


@app.get("/admin")
@roles_required("admin")
def admin_panel():
    pending_users = db.session.scalars(
        select(User).where(
            User.status == "pendente",
            User.role == "participante"
        ).order_by(User.created_at.desc())
    ).all()

    return render_template(
        "templates/dashboard_admin.html",
        user=current_user(),
        pending_users=pending_users
    )


@app.post("/admin/participantes/<int:participant_user_id>/aprovar")
@roles_required("admin")
def approve_participant(participant_user_id):
    user = db.session.get(User, participant_user_id)

    if user is None or user.role != "participante":
        abort(404)

    user.status = "aprovado"
    db.session.commit()
    flash("Cadastro aprovado com sucesso.", "success")

    return redirect(url_for("admin_panel"))


@app.get("/sair")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200

    except SQLAlchemyError:
        app.logger.exception("Falha ao verificar banco de dados")
        return {"status": "error", "database": "unavailable"}, 503


@app.get("/css/<path:filename>")
def css_files(filename):
    return send_from_directory(BASE_DIR / "css", filename)


@app.get("/js/<path:filename>")
def js_files(filename):
    return send_from_directory(BASE_DIR / "js", filename)


@app.get("/assets/<path:filename>")
def public_assets(filename):
    return send_from_directory(BASE_DIR / "assets", filename)


@app.cli.command("init-db")
def init_db_command():
    """Create all initial MySQL tables."""
    with app.app_context():
        db.create_all()

    click.echo("Tabelas iniciais criadas/verificadas no banco jornada_academica.")


@app.cli.command("criar-equipe")
@click.argument("email")
@click.option("--nome", prompt="Nome completo", help="Nome do administrador/professor.")
@click.option("--perfil", type=click.Choice(["admin", "professor"]), prompt="Perfil", help="Perfil de acesso.")
def create_staff_user(email, nome, perfil):
    """Pre-authorize an admin or professor email for Google sign-in."""
    normalized_email = email.strip().lower()
    user = db.session.scalar(
        select(User).where(func.lower(User.email) == normalized_email)
    )

    if user is None:
        user = User(email=normalized_email, role=perfil, status="aprovado")
        db.session.add(user)
    else:
        user.role = perfil
        user.status = "aprovado"

    db.session.commit()
    click.echo(
        f"Acesso {perfil} autorizado para {normalized_email}. Nome informado: {nome}."
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
