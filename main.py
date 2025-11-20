import os
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from passlib.hash import sha256_crypt
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
import re
# ========================================

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.include_router(logs_router)

# 🔐 Autenticação
SECRET_KEY = "segredo-teste"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ❤️ CORREÇÃO bcrypt 72 bytes → usa SHA256 antes do bcrypt
def hash_for_bcrypt(password: str) -> str:
    return pwd_context.hash(sha256_crypt.hash(password))

fake_users = {
    "aluno1": hash_for_bcrypt("N4nd@M4c#2025")
}

def authenticate_user(username: str, password: str):
    if username not in fake_users:
        return False
    return pwd_context.verify(sha256_crypt.hash(password), fake_users[username])

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ROTAS ================================

@app.get("/")
def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if not authenticate_user(username, password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuário ou senha inválidos."}
        )
    token = create_access_token({"sub": username})
    response = RedirectResponse(url="/chat", status_code=302)
    response.set_cookie(key="token", value=token, httponly=True)
    return response

@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("chat.html", {"request": request, "history": []})


# ---------- MÓDULO INTELIGENTE ----------
_MOD_RE = re.compile(r"\bm[óo]dulo\s*0*(\d{1,2})\b", re.IGNORECASE)
_AULA_RE = re.compile(r"\baula\s*0*(\d{1,2})(?:\.(\d{1,2}))?(?:\.(\d{1,2}))?\b", re.IGNORECASE)
_CURTA_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})(?:\.(\d{1,2}))?\b")

def _normalizar_comando_modulo_aula(texto: str):
    if not isinstance(texto, str):
        return None
    t = texto.strip().lower()

    modulo = None
    aula_str = None

    m = _MOD_RE.search(t)
    if m:
        modulo = int(m.group(1))

    a = _AULA_RE.search(t)
    if a:
        partes = [p for p in a.groups() if p]
        aula_str = ".".join(str(int(p)) for p in partes)

    if aula_str is None:
        c = _CURTA_RE.search(t)
        if c:
            partes = [p for p in c.groups() if p]
            aula_str = ".".join(str(int(p)) for p in partes)

    if modulo is None and ("módulo" in t or "modulo" in t):
        n = re.search(r"\b0*(\d{1,2})\b", t)
        if n:
            modulo = int(n.group(1))

    if modulo is None and aula_str is None:
        return None

    if modulo is not None and aula_str:
        return f"módulo {modulo}, aula {aula_str}"
    if modulo is not None:
        return f"módulo {modulo}"
    return f"aula {aula_str}"


def _parece_lista_modulos(texto: str) -> bool:
    if not isinstance(texto, str):
        return False
    t = texto.lower()
    return ("composto por 7 módulos" in t) or ("módulo 01" in t and "módulo 07" in t)


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

    canon = _normalizar_comando_modulo_aula(question)
    if canon:
        question = canon

    TAG_RE = re.compile(r"<[^>]+>")
    def strip_tags(text: str) -> str:
        return TAG_RE.sub(" ", text).strip() if isinstance(text, str) else ""

    def normalize_history(hist_list):
        safe = []
        for item in (hist_list or []):
            safe.append({
                "user": item.get("user", ""),
                "ai": strip_tags(item.get("ai", "")),
                "quick_replies": item.get("quick_replies", []),
                "chip": item.get("chip"),
                "progresso": item.get("progresso")
            })
        return safe

    history_norm = normalize_history(history)

    context = retrieve_relevant_context(question)
    tipo_de_prompt = inferir_tipo_de_prompt(question)

    if tipo_de_prompt == "health_plan":
        registrar_healthplan(pergunta=question, usuario=user)

    chip_perguntas = [
        "Ver Exemplo de Plano", "Modelo no Canva", "Modelo PDF", "Novo Tema",
        "Preciso de exemplo", "Exemplo para Acne", "Tratamento Oral", "Cuidados Diários"
    ]
    is_chip = str(question).strip() in chip_perguntas
    is_first_question = (len(history_norm) == 0) and (not is_chip)

    answer_markdown, quick_replies, progresso = generate_answer(
        question=question,
        context=context,
        history=history_norm,
        tipo_de_prompt=tipo_de_prompt,
        is_first_question=is_first_question
    )

    if canon and _parece_lista_modulos(answer_markdown or ""):
        reforco = (
            f"{question}. Ir diretamente para este conteúdo agora. "
            "Não repita a lista de módulos; apresente a aula ou o módulo solicitado e continue a trilha."
        )
        answer_markdown, quick_replies, progresso = generate_answer(
            question=reforco,
            context=context,
            history=history_norm,
            tipo_de_prompt=tipo_de_prompt,
            is_first_question=False
        )

    answer_html = markdown2.markdown(answer_markdown)

    registrar_log(
        usuario=user,
        pergunta=question,
        resposta=answer_html,
        contexto=context,
        tipo_prompt=tipo_de_prompt
    )

    chip = None
    if str(question).strip() in chip_perguntas:
        chip = str(question).strip()

    new_history = history + [{
        "user": question,
        "ai": answer_html,
        "quick_replies": quick_replies,
        "chip": chip,
        "progresso": progresso
    }]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "history": new_history
    })


# =============== DASHBOARD ==================

DATABASE_URL = "sqlite:///logs.db"
engine = create_engine(DATABASE_URL)

def get_current_admin_user():
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
        perguntas_por_dia = conn.execute(
            text("SELECT strftime('%Y-%m-%d', data) as dia, COUNT(*) as total FROM logs GROUP BY dia ORDER BY dia DESC")
        ).fetchall()
        perguntas_mais_frequentes = conn.execute(
            text("SELECT pergunta, COUNT(*) as total FROM logs GROUP BY pergunta ORDER BY total DESC LIMIT 5")
        ).fetchall()

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

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=logs_export.csv"}
    )
