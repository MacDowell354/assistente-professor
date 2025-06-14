from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import sqlite3

from main import get_current_user  # reutiliza a autenticação existente

router = APIRouter()

@router.get("/logs", response_class=HTMLResponse)
def visualizar_logs(request: Request, user: str = Depends(get_current_user)):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, pergunta, resposta, tipo_prompt, data_hora FROM logs ORDER BY id DESC LIMIT 50")
    registros = cursor.fetchall()
    conn.close()

    html = "<html><head><title>Logs de Perguntas</title></head><body style='font-family:sans-serif;padding:20px;'>"
    html += "<h2>📋 Últimos registros (50)</h2><table border='1' cellpadding='6' cellspacing='0'><tr><th>Usuário</th><th>Pergunta</th><th>Resposta</th><th>Prompt</th><th>Data/Hora</th></tr>"
    for row in registros:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2][:100]}...</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
    html += "</table></body></html>"

    return HTMLResponse(content=html)
