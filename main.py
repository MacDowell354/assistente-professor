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

# ===================== FUNÇÃO ASK (alteração pontual – com fallback/robustez) =====================
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

    # 🔍 Recupera o contexto com base na pergunta (protegido)
    try:
        print(f"🔎 DEBUG — Pergunta para contexto: {question}")
        context = retrieve_relevant_context(question)
        print(f"🔎 DEBUG — Contexto final aceito: {context}")
    except Exception as e:
        print(f"⚠️ DEBUG — Falha ao recuperar contexto: {e}")
        context = ""

    # 🧠 Inferência automática do tipo de prompt (protegido)
    try:
        tipo_de_prompt = inferir_tipo_de_prompt(question)
    except Exception as e:
        print(f"⚠️ DEBUG — Falha inferindo tipo_de_prompt: {e}")
        tipo_de_prompt = "explicacao"

    # 📝 Registro health plan (não deixa quebrar o fluxo)
    if tipo_de_prompt == "health_plan":
        try:
            registrar_healthplan(pergunta=question, usuario=user)
        except Exception as e:
            print(f"⚠️ DEBUG — Falha ao registrar healthplan: {e}")

    # 🚩 Controle de chips e 1ª pergunta (igual ao seu fluxo)
    chip_perguntas = [
        "Ver Exemplo de Plano", "Modelo no Canva", "Modelo PDF", "Novo Tema",
        "Preciso de exemplo", "Exemplo para Acne", "Tratamento Oral", "Cuidados Diários"
    ]
    is_chip = str(question).strip() in chip_perguntas
    is_first_question = (len(history) == 0) and (not is_chip)

    # 🧠 Geração da resposta (protegida) — aceita tupla ou string
    answer_markdown = ""
    quick_replies = []
    progresso = None
    try:
        result = generate_answer(
            question=question,
            context=context,
            history=history,
            tipo_de_prompt=tipo_de_prompt,
            is_first_question=is_first_question
        )
        if isinstance(result, tuple):
            tmp = list(result) + ["", "", ""]
            answer_markdown, quick_replies, progresso = tmp[:3]
        else:
            answer_markdown = result
        if answer_markdown is None:
            answer_markdown = ""
    except Exception as e:
        print(f"🔥 DEBUG — Erro em generate_answer: {e}")
        answer_markdown = ""

    # ✅ Fallback se vier vazio
    if not isinstance(answer_markdown, str) or not answer_markdown.strip():
        answer_markdown = (
            "Desculpe, tive um problema para gerar a resposta agora. "
            "Pode repetir sua pergunta ou dizer o módulo/aula que quer explorar?"
        )

    # 🖥️ Renderiza markdown como HTML (protegido)
    try:
        answer_html = markdown2.markdown(str(answer_markdown))
    except Exception as e:
        print(f"⚠️ DEBUG — Falha no markdown2: {e}")
        answer_html = f"<p>{str(answer_markdown)}</p>"

    # 🧾 Salva log (protegido)
    try:
        registrar_log(
            usuario=user,
            pergunta=question,
            resposta=answer_html,
            contexto=context,
            tipo_prompt=tipo_de_prompt
        )
    except Exception as e:
        print(f"⚠️ DEBUG — Falha ao registrar log: {e}")

    # Histórico (igual ao seu, com quick_replies/progresso)
    chip = str(question).strip() if is_chip else None
    new_history = history + [{
        "user": question,
        "ai": answer_html,
        "quick_replies": quick_replies or [],
        "chip": chip,
        "progresso": progresso
    }]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "history": new_history
    })
# =================== FIM DA ALTERAÇÃO PONTUAL NA FUNÇÃO ASK ===================

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
