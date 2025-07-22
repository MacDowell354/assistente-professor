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
    "Se quiser um exemplo prático ou modelo, clique nos botões abaixo.",
    "Tem outro desafio no seu consultório? Me conte ou clique em Novo Tema.",
    "Se quiser aprofundar, escolha uma opção rápida ou pergunte de novo!",
    "Quer mudar de assunto? Só digitar ‘novo tema’.",
    "Essa resposta te ajudou? Clique em 👍 ou 👎."
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
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta == c or pergunta.startswith(c):
            return c
    return None

def remove_greeting_from_question(question):
    """Remove cumprimento do início da pergunta, se houver, para detectar dúvida real."""
    pergunta = question.strip().lower()
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta.startswith(c):
            pergunta_sem_cumprimento = pergunta[len(c):].lstrip(" ,.!?;-")
            return pergunta_sem_cumprimento
    return pergunta

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

def gerar_quick_replies(question, explicacao):
    """Sugere quick replies (chips) para UX moderna, de acordo com o tema."""
    base_replies = ["Novo Tema", "Preciso de exemplo", "Modelo PDF"]
    replies = []
    q = question.lower()
    if "plano" in q or "plan" in q:
        replies += ["Ver Exemplo de Plano", "Modelo PDF"]
    if "acne" in q:
        replies += ["Exemplo para Acne", "Tratamento Oral", "Cuidados Diários"]
    if not replies:
        replies = base_replies
    return list(dict.fromkeys(replies))[:3]  # Remove duplicatas e limita a 3

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    cumprimento_detectado = is_greeting(question)
    pergunta_limpa = remove_greeting_from_question(question)

    # Se, depois de remover o cumprimento, não sobrou nada relevante, responda só ao cumprimento
    if cumprimento_detectado and not pergunta_limpa.strip():
        return CUMPRIMENTOS_RESPOSTAS[cumprimento_detectado], []

    mostrar_saudacao = is_first_question
    mostrar_pergunta_repetida = is_first_question

    saudacao = random.choice(GREETINGS) if mostrar_saudacao else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(pergunta_limpa if pergunta_limpa.strip() else question)
    pergunta_repetida = f"<strong>Sua pergunta:</strong> \"{question}\"<br><br>" if mostrar_pergunta_repetida else ""

    # Gera prompt considerando histórico de chat, se disponível
    if history:
        prompt = (
            f"Você é Nanda Mac.ia, professora do curso Consultório High Ticket.\n"
            f"Abaixo está a conversa até agora entre o aluno e a professora:\n\n"
            f"{history}\n\n"
            f"O aluno enviou agora:\n"
            f"'{question}'\n\n"
            "Continue a conversa considerando o contexto anterior. Se o aluno pedir mais detalhes, exemplos, ou disser 'mais específico', aprofunde sobre o assunto que estavam conversando, sem mudar de tema e sem repetir tudo do zero."
            "\nSe for uma dúvida nova, responda normalmente."
            "\n[IMPORTANTE] Seja didática, acolhedora e responda exatamente ao que o aluno pediu."
            "\nUtilize o conteúdo abaixo como base para a resposta:\n"
            f"{snippet}\n"
        )
    else:
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
    quick_replies = gerar_quick_replies(question, explicacao)

    # Só exibe saudação e pergunta na primeira interação
    resposta = ""
    if mostrar_saudacao:
        resposta += f"{saudacao}<br><br>{pergunta_repetida}{explicacao}<br><br>{fechamento}"
    else:
        resposta += f"{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies
