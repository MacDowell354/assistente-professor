import sqlite3
from datetime import datetime

DB_PATH = "logs.db"

def registrar_log(username, pergunta, resposta, contexto, tipo_prompt):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            pergunta TEXT,
            resposta TEXT,
            contexto TEXT,
            tipo_prompt TEXT,
            data_hora TEXT
        )
    """)

    data_hora = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO logs (username, pergunta, resposta, contexto, tipo_prompt, data_hora)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, pergunta, resposta, contexto, tipo_prompt, data_hora))

    conn.commit()
    conn.close()
