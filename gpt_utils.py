import os
import re
import random
from openai import OpenAI, OpenAIError

# Configurar seu arquivo de transcrições
TRANSCRIPTS_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")

client = OpenAI()

OUT_OF_SCOPE_MSG = (
    "Desculpe, ainda não tenho informações suficientes sobre esse tema específico do curso. "
    "Por favor, envie outra pergunta ou consulte o material da aula."
)

GREETINGS = [
    "Olá, Doutor(a), seja muito bem-vindo(a)!",
    "Oi, Doutor(a), tudo bem? Como posso ajudar?",
    "Bem-vindo(a) de volta, Doutor(a)!",
    "Olá, Doutor(a)! Estou aqui para apoiar você no seu crescimento"
]

CLOSINGS = [
    "Se quiser um exemplo prático ou modelo, clique nos botões abaixo.",
    "Tem outro desafio no seu consultório? Me conte ou clique em Novo Tema.",
    "Se quiser aprofundar, escolha uma opção rápida ou pergunte de novo!",
    "Quer mudar de assunto? Só digitar ‘novo tema’.",
    "Essa resposta te ajudou? Clique em 👍 ou 👎."
]

CUMPRIMENTOS_RESPOSTAS = {
    "bom dia": "Bom dia! Se quiser tirar dúvidas sobre o curso, é só perguntar. Estou à disposição.",
    "boa tarde": "Boa tarde! Se quiser tirar dúvidas sobre o curso, é só perguntar. Estou à disposição.",
    "boa noite": "Boa noite! Estou aqui para ajudar. Pode enviar sua dúvida quando quiser.",
    "oi": "Oi, Doutor(a)! 😊 Seja bem-vindo(a)! Pode enviar sua dúvida quando quiser.",
    "olá": "Olá! Estou aqui para ajudar. Pode perguntar sobre Consultório High Ticket quando quiser!",
    "ola": "Olá! Estou aqui para ajudar. Pode perguntar sobre Consultório High Ticket quando quiser!",
    "tudo bem": "Tudo ótimo por aqui! Se quiser perguntar algo sobre o curso, fique à vontade.",
    "oi, tudo bem": "Oi, tudo bem! Se quiser tirar dúvidas, pode perguntar que estou à disposição.",
    "e aí": "E aí! Se quiser tirar dúvidas sobre o curso, estou por aqui para te ajudar."
}

CHIP_PERGUNTAS = [
    "Ver Exemplo de Plano", "Modelo no Canva", "Modelo PDF", "Novo Tema",
    "Preciso de exemplo", "Exemplo para Acne", "Tratamento Oral", "Cuidados Diários",
    "Baixar Plano de Ação", "Baixar Guia do Curso", "Baixar Dossiê 007"
]

def is_greeting(question):
    pergunta = question.strip().lower()
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta == c or pergunta.startswith(c):
            return c
    return None

def remove_greeting_from_question(question):
    pergunta = question.strip().lower()
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta.startswith(c):
            pergunta_sem_cumprimento = pergunta[len(c):].lstrip(" ,.!?;-")
            return pergunta_sem_cumprimento
    return pergunta

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

def search_transcripts_by_theme(theme):
    theme_norm = normalize_text(theme)
    if not os.path.exists(TRANSCRIPTS_PATH):
        return None

    with open(TRANSCRIPTS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content_norm = normalize_text(content)
    pos = content_norm.find(theme_norm)
    if pos == -1:
        palavras = theme_norm.split()
        for palavra in palavras:
            pos = content_norm.find(palavra)
            if pos != -1:
                break
        else:
            return None

    # Busca delimitador antes e depois (==== ou ----)
    delimitadores = ["====", "----"]
    start = 0
    end = len(content)

    for d in delimitadores:
        bloco_inicio = content.rfind(d, 0, pos)
        if bloco_inicio > start:
            start = bloco_inicio
    for d in delimitadores:
        bloco_fim = content.find(d, pos)
        if bloco_fim != -1 and bloco_fim < end:
            end = bloco_fim + len(d)

    snippet = content[start:end]
    return snippet.strip()
