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

def resposta_link(titulo, url):
    return (
        f"Olá, Doutor(a)! 😊 Aqui está o link direto para baixar o {titulo}:<br>"
        f"<a class='chip' href='{url}' target='_blank'>📄 Baixar {titulo}</a><br>"
        "Se precisar de orientação ou tiver dúvidas sobre como aplicar, é só perguntar!"
    )

CHIP_PERGUNTAS = [
    "Ver Exemplo de Plano", "Modelo no Canva", "Modelo PDF", "Novo Tema",
    "Preciso de exemplo", "Exemplo para Acne", "Tratamento Oral", "Cuidados Diários",
    "Baixar Plano de Ação", "Baixar Guia do Curso", "Baixar Dossiê 007"
]

def is_greeting(question):
    cumprimentos = ["bom dia", "boa tarde", "boa noite", "oi", "olá", "ola", "tudo bem", "oi, tudo bem", "e aí"]
    pergunta = question.strip().lower()
    for c in cumprimentos:
        if pergunta == c or pergunta.startswith(c):
            return c
    return None

def remove_greeting_from_question(question):
    cumprimentos = ["bom dia", "boa tarde", "boa noite", "oi", "olá", "ola", "tudo bem", "oi, tudo bem", "e aí"]
    pergunta = question.strip().lower()
    for c in cumprimentos:
        if pergunta.startswith(c):
            return pergunta[len(c):].lstrip(" ,.!?;-")
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

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    pergunta = question.strip().lower()

    if pergunta in ["baixar plano de ação", "pdf plano de ação", "plano de ação pdf", "baixar o plano de ação"]:
        return resposta_link("Plano de Ação do Consultório High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EV6wZ42I9nhHpmnSGa4DHfEBaff0ewZIsmH_4LqLAI46eQ?e=gd5hR0"), []

    if pergunta in ["baixar patient letter", "pdf patient letter", "modelo patient letter", "baixar carta de encaminhamento", "baixar carta patient letter", "download patient letter"]:
        return resposta_link("Patient Letter – Modelo Oficial", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EbdJ4rqiywhOjG0Yy3cDhjYBf04FMiNmoOXos4M5eZmoaA?e=YhljQ7"), []

    if pergunta in ["baixar guia do curso", "pdf guia do curso", "guia do curso pdf", "baixar o guia do curso"]:
        return resposta_link("Guia do Curso Consultório High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EQZrQJpHXlVCsK1N5YdDIHEBHocn7FR2yQUHhydgN84yOw?e=GAut9r"), []

    if pergunta in ["baixar dossiê 007", "baixar dossie 007", "pdf dossiê 007", "dossiê 007 pdf", "baixar o dossiê 007"]:
        return resposta_link("Dossiê 007 – Captação de Pacientes High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVdOpjU1frVBhApTKmmYAwgBFkbNggnj2Cp0w9luTajxgg?e=iQOnk0"), []

    if pergunta in ["modelo no canva", "modelo health plan", "modelo healthplan", "modelo de health plan"]:
        return resposta_link("Modelo de Health Plan no Canva", "https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview"), []

    if is_greeting(pergunta):
        return random.choice(GREETINGS), CHIP_PERGUNTAS

    pergunta_limpa = remove_greeting_from_question(pergunta)
    trecho = search_transcripts_by_theme(pergunta_limpa)
    if trecho:
        saudacao = random.choice(GREETINGS)
        fechamento = random.choice(CLOSINGS)
        resposta = f"{saudacao}<br><br>{trecho}<br><br>{fechamento}"
        return resposta, CHIP_PERGUNTAS

    prompt_final = f"""Você é uma professora didática, experiente e acolhedora, explicando o conteúdo do curso Consultório High Ticket para alunos médicos. Sua linguagem é objetiva, gentil e baseada no conteúdo da aula. Use estrutura com tópicos se necessário.

Pergunta: {pergunta}
Contexto da aula (se houver): {context}
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt_final}]
        )
        resposta_gerada = completion.choices[0].message.content
        saudacao = random.choice(GREETINGS)
        fechamento = random.choice(CLOSINGS)
        resposta = f"{saudacao}<br><br>{resposta_gerada}<br><br>{fechamento}"
        return resposta, CHIP_PERGUNTAS

    except OpenAIError as e:
        return f"Erro ao gerar resposta: {str(e)}", []

def remove_html_tags(text):
    return re.sub(r"<[^>]*>", "", text)

def extract_theme(question):
    clean = remove_html_tags(question).lower()
    palavras = clean.split()
    if not palavras:
        return ""
    return palavras[-1]
