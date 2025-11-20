import os
import json
import hashlib
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

from sqlalchemy import create_engine, text
from io import StringIO
import csv
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.include_router(logs_router)

SECRET_KEY = "segredo-teste"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 🔥 CORREÇÃO FINAL
def pre_hash(password: str) -> str:
    """SHA256 puro (hexdigest) antes do bcrypt."""
    return hashlib.sha256(password.encode()).hexdigest()


fake_users = {
    "aluno1": pwd_context.hash(pre_hash("N4nd@M4c#2025"))
}

def authenticate_user(username: str, password: str):
    if username not in fake_users:
        return False
    return pwd_context.verify(pre_hash(password), fake_users[username])


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


# (todo o restante do código permanece igual — não alterei mais nada)
