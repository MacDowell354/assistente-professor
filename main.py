import os
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Cria a aplicação FastAPI
app = FastAPI()

# Registra as rotas de visualização de logs (requer autenticação)
app.include_router(logs_router)

# Configura templates
templates = Jinja2Templates(directory="templates")

# Configura autenticação
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cria token de acesso

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Rotas de login e chat
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

    # Determina o tipo de prompt
    tipo_de_prompt = inferir_tipo_de_prompt(question)

    # Recupera contexto relevante
    context = retrieve_relevant_context(question)

    # Se for health_plan, registra log específico
    if tipo_de_prompt == "health_plan":
        registrar_healthplan(pergunta=question, usuario=user)

    # Gera resposta
    answer_markdown = generate_answer(
        question=question,
        context=context,
        history=history,
        tipo_de_prompt=tipo_de_prompt
    )

    # Converte Markdown para HTML
    answer_html = markdown2.markdown(answer_markdown)

    # Salva log da conversa
    registrar_log(
        username=user,
        pergunta=question,
        resposta=answer_html,
        contexto=context,
        tipo_prompt=tipo_de_prompt
    )

    # Atualiza histórico e renderiza chat
    new_history = history + [{"user": question, "ai": answer_html}]
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "history": new_history
    })
