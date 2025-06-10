import os
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext

from search_engine import retrieve_relevant_context
from gpt_utils import generate_answer

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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

def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise RedirectResponse("/login")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise RedirectResponse("/login")

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
async def ask(request: Request, question: Optional[str] = Form(None), user: str = Depends(get_current_user)):
    if not question:
        return RedirectResponse(url="/chat", status_code=302)

    form_data = await request.form()
    history_str = form_data.get("history", "[]")
    try:
        history = json.loads(history_str)
    except Exception:
        history = []

    context = retrieve_relevant_context(question)
    answer = generate_answer(question, context=context, history=history)

    new_history = history + [{"user": question, "ai": answer}]
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "history": new_history
    })
