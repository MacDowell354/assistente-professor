import os
import re
import random
from openai import OpenAI, OpenAIError

# Configuração do caminho para o arquivo de transcrições
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
    start = max(0, pos - 500)
    end = min(len(content), pos + 500)
    snippet = content[start:end]
    return snippet.strip()

def gerar_quick_replies(question, explicacao, history=None):
    # Botões rápidos didáticos e aplicáveis para médicos
    return [
        "Quero um exemplo prático",
        "Me explique passo a passo",
        "Tenho uma dúvida sobre esse tema"
    ]

def resposta_link(titulo, url, icone="📄"):
    # icone pode ser: 📄, 📝, 🎵, 📑 etc.
    return (
        f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"
    )

def resposta_link_externo(titulo, url, icone="🔗"):
    return (
        f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"
    )

def generate_answer(
    question, context="", history=None, tipo_de_prompt=None, is_first_question=True
):
    cumprimento_detectado = is_greeting(question)
    pergunta_limpa = remove_greeting_from_question(question)

    # Blocos ESPECIAIS de PDF/links
    PLANO_ACAO_KEYWORDS = [
        "plano de ação", "pdf plano de ação", "atividade da primeira semana",
        "material do onboarding", "ação consultório", "plano onboarding",
        "plano de ação consultório", "atividade plano", "baixar plano de ação"
    ]
    GUIA_CURSO_KEYWORDS = [
        "guia do curso", "guia cht", "guia consultório high ticket",
        "manual do curso", "manual cht", "material de onboarding",
        "passos iniciais", "guia onboarding", "baixar guia do curso"
    ]
    DOSSIÊ_007_KEYWORDS = [
        "dossiê 007", "dossie 007", "dossiê captação", "dossie aula 5.8",
        "captação de pacientes", "estratégias 007", "baixar dossiê 007"
    ]
    PATIENT_LETTER_KEYWORDS = [
        "patient letter", "carta patient letter", "pdf patient letter", "modelo patient letter",
        "baixar patient letter", "patient letter do curso"
    ]
    SECRETARIA_KEYWORDS = [
        "scripts da secretária", "script da secretária", "roteiro secretária",
        "pdf scripts secretária", "modelo de secretária", "secretaria", "secretária"
    ]
    HEALTHPLAN_KEYWORDS = [
        "health plan", "modelo health plan", "modelo no canva", "formulário health plan", "healthplan", "plano de saúde"
    ]
    SPOTIFY_KEYWORDS = [
        "playlist spotify", "playlist no spotify", "música spotify", "spotify do curso", "link spotify", "playlist do curso"
    ]

    # Prepara variáveis para adicionar botão ao final, mesmo em respostas longas
    extra_link = ""
    if any(x in pergunta_limpa for x in PLANO_ACAO_KEYWORDS) or any(x in question.lower() for x in PLANO_ACAO_KEYWORDS):
        extra_link = resposta_link("Baixar Plano de Ação do Consultório High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EV6wZ42I9nhHpmnSGa4DHfEBaff0ewZIsmH_4LqLAI46eQ?e=gd5hR0")
    elif any(x in pergunta_limpa for x in GUIA_CURSO_KEYWORDS) or any(x in question.lower() for x in GUIA_CURSO_KEYWORDS):
        extra_link = resposta_link("Baixar Guia do Curso Consultório High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EQZrQJpHXlVCsK1N5YdDIHEBHocn7FR2yQUHhydgN84yOw?e=GAut9r")
    elif any(x in pergunta_limpa for x in DOSSIÊ_007_KEYWORDS) or any(x in question.lower() for x in DOSSIÊ_007_KEYWORDS):
        extra_link = resposta_link("Baixar Dossiê 007 – Captação de Pacientes High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVdOpjU1frVBhApTKmmYAwgBFkbNggnj2Cp0w9luTajxgg?e=iQOnk0")
    elif any(x in pergunta_limpa for x in PATIENT_LETTER_KEYWORDS) or any(x in question.lower() for x in PATIENT_LETTER_KEYWORDS):
        extra_link = resposta_link("Baixar Patient Letter – Modelo Oficial", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EbdJ4rqiywhOjG0Yy3cDhjYBf04FMiNmoOXos4M5eZmoaA?e=90kaBp")
    elif any(x in pergunta_limpa for x in SECRETARIA_KEYWORDS) or any(x in question.lower() for x in SECRETARIA_KEYWORDS):
        extra_link = resposta_link("Baixar Scripts da Secretária – Consultório High Ticket", "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVgtSPvwpw9OhOS4CibHXGYB7KNAolar5o0iY2I2dOKCAw?e=LVZlX3")
    elif any(x in pergunta_limpa for x in HEALTHPLAN_KEYWORDS) or any(x in question.lower() for x in HEALTHPLAN_KEYWORDS):
        extra_link = resposta_link_externo("Acessar Modelo Editável de Health Plan no Canva", "https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview", icone="📝")
    # --------- CORREÇÃO DO SPOTIFY: busca ampla por qualquer variação ------------
    elif (
        any(x in pergunta_limpa for x in SPOTIFY_KEYWORDS)
        or any(x in question.lower() for x in SPOTIFY_KEYWORDS)
        or any(kw in pergunta_limpa.lower() for kw in ["spotify", "playlist", "música", "musica", "trilha sonora"])
        or any(kw in question.lower() for kw in ["spotify", "playlist", "música", "musica", "trilha sonora"])
    ):
        extra_link = resposta_link_externo(
            "Acessar Playlist Oficial do Consultório High Ticket no Spotify",
            "https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80",
            icone="🎵"
        )

    is_chip = any(question.strip().lower() == c.lower() for c in CHIP_PERGUNTAS)
    mostrar_saudacao = is_first_question and not is_chip
    mostrar_pergunta_repetida = is_first_question and not is_chip

    saudacao = random.choice(GREETINGS) if mostrar_saudacao else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(pergunta_limpa if pergunta_limpa.strip() else question)
    pergunta_repetida = (
        f"<strong>Sua pergunta:</strong> \"{question}\"<br><br>" if mostrar_pergunta_repetida else ""
    )

    # ----------- Blocos de prompt personalizados por contexto ----------------
    if history:
        prompt = (
            "Você é a professora Nanda Mac.ia, uma inteligência artificial didática, acolhedora e especializada em ensinar médicos a construir um consultório lucrativo, valorizado e com pacientes High Ticket.\n"
            "Seu papel é ser extremamente clara, paciente, motivadora e experiente, explicando sempre em linguagem simples, estruturada e com exemplos práticos. Transforme conceitos em passos aplicáveis à rotina médica.\n"
            "Trate cada dúvida como oportunidade de aprendizado, incentive perguntas e adapte a resposta ao contexto e à especialidade do aluno quando possível.\n"
            "Explique sempre de forma humanizada, como faria em uma mentoria individual, e proponha próximos passos, reflexões e sugestões para aplicação prática.\n"
            "Se a pergunta do aluno for sobre como começar, primeiros passos, o que fazer em cada aula ou sobre a ordem/objetivo dos módulos, explique resumidamente o objetivo de cada módulo do curso (de 1 a 7), oriente sobre o início, o caminho ideal, o que é esperado em cada etapa e incentive o aluno a seguir a sequência proposta.\n"
            "Nunca critique dúvidas. Seja motivadora, precisa, didática e mantenha o foco no sucesso do aluno e na transformação do consultório.\n"
            f"Abaixo está a conversa até agora entre o aluno e a professora:\n\n"
            f"{history}\n\n"
            f"O aluno enviou agora:\n"
            f"'{question}'\n\n"
            "Continue a conversa considerando o contexto anterior. Se o aluno pedir mais detalhes, exemplos ou disser 'mais específico', aprofunde sobre o assunto que estavam conversando, sem mudar de tema e sem repetir tudo do zero.\n"
            "Se for uma dúvida nova, responda normalmente.\n"
            "[IMPORTANTE] Siga as diretrizes acima. Utilize o conteúdo abaixo como base para a resposta:\n"
            f"{snippet}\n"
        )
    else:
        prompt = (
            "Você é a professora Nanda Mac.ia, uma inteligência artificial didática, acolhedora e especializada em ensinar médicos a construir um consultório lucrativo, valorizado e com pacientes High Ticket.\n"
            "Seu papel é ser extremamente clara, paciente, motivadora e experiente, explicando sempre em linguagem simples, estruturada e com exemplos práticos. Transforme conceitos em passos aplicáveis à rotina médica.\n"
            "Trate cada dúvida como oportunidade de aprendizado, incentive perguntas e adapte a resposta ao contexto e à especialidade do aluno quando possível.\n"
            "Explique sempre de forma humanizada, como faria em uma mentoria individual, e proponha próximos passos, reflexões e sugestões para aplicação prática.\n"
            "Se a pergunta do aluno for sobre como começar, primeiros passos, o que fazer em cada aula ou sobre a ordem/objetivo dos módulos, explique resumidamente o objetivo de cada módulo do curso (de 1 a 7), oriente sobre o início, o caminho ideal, o que é esperado em cada etapa e incentive o aluno a seguir a sequência proposta.\n"
            "Nunca critique dúvidas. Seja motivadora, precisa, didática e mantenha o foco no sucesso do aluno e na transformação do consultório.\n"
            f"O aluno fez a seguinte pergunta:\n\n"
            f"'{question}'\n\n"
            "Responda de forma extremamente objetiva, estruturada em tópicos numerados, utilizando exemplos práticos, analogias e sempre orientando para aplicação real no consultório.\n"
            "Use APENAS o conteúdo fornecido abaixo como referência e responda diretamente à pergunta feita, sem introduções ou divagações gerais.\n"
            "[IMPORTANTE] Siga as diretrizes acima. Utilize o conteúdo abaixo como base para a resposta:\n"
            f"{snippet}\n"
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=700
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=700
        )

    explicacao = response.choices[0].message.content.strip()
    quick_replies = gerar_quick_replies(question, explicacao, history)

    resposta = ""
    if mostrar_saudacao:
        resposta += f"{saudacao}<br><br>{pergunta_repetida}{explicacao}{extra_link}<br><br>{fechamento}"
    else:
        resposta += f"{explicacao}{extra_link}<br><br>{fechamento}"

    return resposta, quick_replies
