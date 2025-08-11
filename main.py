import os
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from jose import jwt
import markdown2

from search_engine import retrieve_relevant_context
from gpt_utils import generate_answer
from db_logs import registrar_log
from logs_route import router as logs_router
from auth_utils import get_current_user
from prompt_router import inferir_tipo_de_prompt
from healthplan_log import registrar_healthplan

# ======= IMPORTS PARA O DASHBOARD =======
from sqlalchemy import create_engine, text
from io import StringIO
import csv
# ========================================

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.include_router(logs_router)

# 🔐 Autenticação
SECRET_KEY = "segredo-teste"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fake_users = {"aluno1": pwd_context.hash("N4nd@M4c#2025")}

def authenticate_user(username: str, password: str):
    if username not in fake_users:
        return False
    return pwd_context.verify(password, fake_users[username])

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/")
def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if not authenticate_user(username, password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário ou senha inválidos."})
    token = create_access_token({"sub": username})
    response = RedirectResponse(url="/chat", status_code=302)
    response.set_cookie(key="token", value=token, httponly=True)
    return response

@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("chat.html", {"request": request, "history": []})

@app.post("/ask", response_class=HTMLResponse)
async def ask(
    request: Request,
    question: Optional[str] = Form(None),
    user: str = Depends(get_current_user)
):
    if not question:
        return RedirectResponse(url="/chat", status_code=302)

    form_data = await request.form()
    history_str = form_data.get("history", "[]")
    try:
        history = json.loads(history_str)
    except Exception:
        history = []

    # 🔍 Recupera o contexto com base na transcrição
    context = retrieve_relevant_context(question)

    # 🧠 Inferência automática do tipo de prompt
    tipo_de_prompt = inferir_tipo_de_prompt(question)

    # 📝 Registra se for relacionado a Health Plan
    if tipo_de_prompt == "health_plan":
        registrar_healthplan(pergunta=question, usuario=user)

    # 🚩 Controle refinado para saudação premium e chips/quick replies
    chip_perguntas = [
        "Ver Exemplo de Plano", "Modelo no Canva", "Modelo PDF", "Novo Tema",
        "Preciso de exemplo", "Exemplo para Acne", "Tratamento Oral", "Cuidados Diários"
    ]
    is_chip = str(question).strip() in chip_perguntas
    is_first_question = (len(history) == 0) and (not is_chip)

    # 🧠 Gera resposta (AGORA SALVA PROGRESSO!)
    answer_markdown, quick_replies, progresso = generate_answer(
        question=question,
        context=context,
        history=history,
        tipo_de_prompt=tipo_de_prompt,
        is_first_question=is_first_question
    )

    # 🖥️ Renderiza markdown como HTML
    answer_html = markdown2.markdown(answer_markdown)

    # 🧾 Salva log da conversa
    registrar_log(
        usuario=user,
        pergunta=question,
        resposta=answer_html,
        contexto=context,
        tipo_prompt=tipo_de_prompt
    )

    # Adiciona quick replies e PROGRESSO ao histórico da resposta
    chip = None
    if str(question).strip() in chip_perguntas:
        chip = str(question).strip()

    new_history = history + [{
        "user": question,
        "ai": answer_html,
        "quick_replies": quick_replies,
        "chip": chip,
        "progresso": progresso   # <- ESSENCIAL: progresso salvo a cada interação!
    }]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "history": new_history
    })

# =============== INÍCIO DASHBOARD LOGS =================

# Caminho do seu banco SQLite de logs
DATABASE_URL = "sqlite:///logs.db"
engine = create_engine(DATABASE_URL)

def get_current_admin_user():
    # Controle de acesso: adapte conforme seu login/admin!
    return True

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_admin_user)):
    filtro_usuario = request.query_params.get("usuario", "")
    filtro_modulo = request.query_params.get("modulo", "")
    filtro_palavra = request.query_params.get("palavra", "")
    filtro_data_inicio = request.query_params.get("data_inicio", "")
    filtro_data_fim = request.query_params.get("data_fim", "")

    sql = "SELECT * FROM logs WHERE 1=1"
    params = {}

    if filtro_usuario:
        sql += " AND usuario LIKE :usuario"
        params["usuario"] = f"%{filtro_usuario}%"
    if filtro_modulo:
        sql += " AND modulo = :modulo"
        params["modulo"] = filtro_modulo
    if filtro_palavra:
        sql += " AND (pergunta LIKE :palavra OR resposta LIKE :palavra)"
        params["palavra"] = f"%{filtro_palavra}%"
    if filtro_data_inicio:
        sql += " AND data >= :data_inicio"
        params["data_inicio"] = filtro_data_inicio
    if filtro_data_fim:
        sql += " AND data <= :data_fim"
        params["data_fim"] = filtro_data_fim

    sql += " ORDER BY data DESC"

    with engine.connect() as conn:
        logs = conn.execute(text(sql), params).fetchall()
        total_usuarios = conn.execute(text("SELECT COUNT(DISTINCT usuario) FROM logs")).scalar()
        total_perguntas = conn.execute(text("SELECT COUNT(*) FROM logs")).scalar()
        perguntas_por_dia = conn.execute(text("SELECT strftime('%Y-%m-%d', data) as dia, COUNT(*) as total FROM logs GROUP BY dia ORDER BY dia DESC")).fetchall()
        perguntas_mais_frequentes = conn.execute(text("SELECT pergunta, COUNT(*) as total FROM logs GROUP BY pergunta ORDER BY total DESC LIMIT 5")).fetchall()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "logs": logs,
        "total_usuarios": total_usuarios,
        "total_perguntas": total_perguntas,
        "perguntas_por_dia": perguntas_por_dia,
        "perguntas_mais_frequentes": perguntas_mais_frequentes,
        "filtro_usuario": filtro_usuario,
        "filtro_modulo": filtro_modulo,
        "filtro_palavra": filtro_palavra,
        "filtro_data_inicio": filtro_data_inicio,
        "filtro_data_fim": filtro_data_fim
    })

@app.get("/dashboard/export", response_class=StreamingResponse)
async def dashboard_export(request: Request, user=Depends(get_current_admin_user)):
    filtro_usuario = request.query_params.get("usuario", "")
    filtro_modulo = request.query_params.get("modulo", "")
    filtro_palavra = request.query_params.get("palavra", "")
    filtro_data_inicio = request.query_params.get("data_inicio", "")
    filtro_data_fim = request.query_params.get("data_fim", "")

    sql = "SELECT * FROM logs WHERE 1=1"
    params = {}

    if filtro_usuario:
        sql += " AND usuario LIKE :usuario"
        params["usuario"] = f"%{filtro_usuario}%"
    if filtro_modulo:
        sql += " AND modulo = :modulo"
        params["modulo"] = filtro_modulo
    if filtro_palavra:
        sql += " AND (pergunta LIKE :palavra OR resposta LIKE :palavra)"
        params["palavra"] = f"%{filtro_palavra}%"
    if filtro_data_inicio:
        sql += " AND data >= :data_inicio"
        params["data_inicio"] = filtro_data_inicio
    if filtro_data_fim:
        sql += " AND data <= :data_fim"
        params["data_fim"] = filtro_data_fim

    sql += " ORDER BY data DESC"

    with engine.connect() as conn:
        logs = conn.execute(text(sql), params).fetchall()
        headers = logs[0].keys() if logs else ["usuario","modulo","aula","pergunta","resposta","data"]

    def iter_csv():
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(headers)
        for row in logs:
            cw.writerow([row[c] for c in headers])
        yield si.getvalue()

    return StreamingResponse(iter_csv(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=logs_export.csv"})

# =============== FIM DASHBOARD LOGS ===================


# ===================== BLOCO VOZ — INÍCIO =====================
import os as _os
import uuid as _uuid
import json as _json
import re as _re
from fastapi import UploadFile, File, Form, Depends as _Depends
from fastapi.responses import FileResponse, RedirectResponse
from voice_utils import transcribe_with_whisper, tts_with_elevenlabs, AUDIO_DIR
try:
    from db_logs import registrar_log as _registrar_log  # reuse seu logger
except Exception:
    _registrar_log = None

@app.get("/audio/{filename}")
def get_audio(filename: str, user: str = _Depends(get_current_user)):
    path = _os.path.join(AUDIO_DIR, filename)
    if not _os.path.exists(path):
        return RedirectResponse("/dashboard")
    return FileResponse(path, media_type="audio/mpeg", filename=filename)

@app.post("/ask-voice")
async def ask_voice(
    audio: UploadFile = File(...),
    history: str = Form("[]"),
    context: str = Form(""),
    user: str = _Depends(get_current_user)
):
    # 1) Salvar upload temporariamente
    tmp_name = f"rec_{_uuid.uuid4().hex}_{audio.filename or 'audio.webm'}"
    tmp_path = _os.path.join(AUDIO_DIR, tmp_name)
    with open(tmp_path, "wb") as f:
        f.write(await audio.read())

    # 2) Transcrever
    try:
        pergunta_txt = transcribe_with_whisper(tmp_path).strip()
        if not pergunta_txt:
            pergunta_txt = "(áudio sem fala detectável)"
    except Exception:
        pergunta_txt = "(falha na transcrição)"

    # 3) Reusar seu fluxo de geração
    try:
        hist_list = []
        try:
            hist_list = _json.loads(history) if history else []
        except Exception:
            hist_list = []
        answer_markdown, quick_replies, progresso = generate_answer(
            question=pergunta_txt,
            context=context or "",
            history=hist_list,
            tipo_de_prompt="voz",
            is_first_question=(len(hist_list) == 0),
        )
        answer_html = markdown2.markdown(answer_markdown)
    except Exception:
        answer_html = "Tivemos um problema ao processar o áudio. Tente novamente."
        quick_replies = []
        progresso = None

    # 4) (Opcional) TTS da resposta
    audio_filename = None
    try:
        plain = _re.sub("<[^<]+?>", " ", answer_html)
        audio_filename = tts_with_elevenlabs(plain)
    except Exception:
        audio_filename = None

    # 5) Log (tipo_prompt='voz')
    try:
        if _registrar_log:
            _registrar_log(
                usuario=user,
                pergunta=pergunta_txt,
                resposta=answer_html,
                contexto=context or "",
                tipo_prompt="voz",
                modulo=(progresso or {}).get("modulo"),
                aula=(progresso or {}).get("aula"),
            )
    except Exception:
        pass

    # 6) Retorno para o front
    return {
        "ok": True,
        "question_text": pergunta_txt,
        "answer_html": answer_html,
        "quick_replies": quick_replies or [],
        "audio_url": (f"/audio/{audio_filename}" if audio_filename else None),
        "progresso": progresso,
    }
# ===================== BLOCO VOZ — FIM =====================
