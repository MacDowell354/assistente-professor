import os
import re
import random
from openai import OpenAI, OpenAIError

# Configurar seu arquivo de transcrições
TRANSCRIPTS_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")

# Instância do cliente OpenAI
client = OpenAI()

# Mensagem padrão para temas não encontrados
OUT_OF_SCOPE_MSG = (
    "Desculpe, ainda não tenho informações suficientes sobre esse tema específico do curso. "
    "Por favor, envie outra pergunta ou consulte o material da aula."
)

# Saudações e fechamentos para humanizar as respostas
GREETINGS = [
    "Olá, Doutor(a), seja muito bem-vindo(a)!",
    "Oi, Doutor(a), tudo bem? Como posso ajudar?",
    "Bem-vindo(a) de volta, Doutor(a)!",
    "Olá, Doutor(a)! Estou aqui para apoiar você no seu crescimento"
]

CLOSINGS = [
    "Fique à vontade para perguntar sempre que quiser evoluir.",
    "Espero ter ajudado! Qualquer dúvida, é só chamar.",
    "Conte comigo para o seu sucesso no Consultório High Ticket."
]

# Cumprimentos específicos e respostas dedicadas
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

def is_greeting(question):
    pergunta = question.strip().lower()
    # Se pergunta é um cumprimento exato ou começa com um cumprimento
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta == c or pergunta.startswith(c):
            return c
    return None

def normalize_text(text):
    """Normaliza texto para melhorar buscas: minusculas, sem acentos, sem caracteres especiais."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

def search_transcripts_by_theme(theme):
    """Busca no arquivo de transcrições o trecho que contém o tema."""
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

    start = max(0, pos - 500)
    end = min(len(content), pos + 500)
    snippet = content[start:end]
    return snippet.strip()

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    # NOVO: Detecta cumprimento simples antes de todo o resto
    cumprimento_detectado = is_greeting(question)
    if cumprimento_detectado:
        return CUMPRIMENTOS_RESPOSTAS[cumprimento_detectado]

    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(question)

    pergunta_repetida = f"<strong>Sua pergunta:</strong> \"{question}\"<br><br>"

    if snippet:
        prompt = (
            f"Você é Nanda Mac.ia, professora do curso Consultório High Ticket.\n"
            f"O aluno fez a seguinte pergunta:\n\n"
            f"'{question}'\n\n"
            "Responda de forma extremamente objetiva e didática, exatamente como faria numa aula particular.\n"
            "Forneça uma resposta estruturada em tópicos numerados, utilizando exemplos práticos e claros.\n"
            "Use APENAS o conteúdo fornecido abaixo como referência e responda diretamente à pergunta feita,\n"
            "sem introduções ou divagações gerais:\n\n"
            f"{snippet}\n\n"
            "[IMPORTANTE] Seja objetiva, acolhedora e responda EXCLUSIVAMENTE ao tema solicitado."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )
        except OpenAIError:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )

        explicacao = response.choices[0].message.content.strip()

        if saudacao:
            return f"{saudacao}<br><br>{pergunta_repetida}{explicacao}<br><br>{fechamento}"
        else:
            return f"{pergunta_repetida}{explicacao}<br><br>{fechamento}"

    else:
        if saudacao:
            return f"{saudacao}<br><br>{pergunta_repetida}{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
        else:
            return f"{pergunta_repetida}{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
