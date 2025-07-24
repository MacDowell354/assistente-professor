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
    start = max(0, pos - 500)
    end = min(len(content), pos + 500)
    snippet = content[start:end]
    return snippet.strip()

def gerar_quick_replies(question, explicacao, history=None):
    base_replies = ["Novo Tema", "Preciso de exemplo"]
    tema_healthplan = False
    tema_acne = False
    tema_plano_acao = False
    tema_guia_curso = False
    tema_dossie_007 = False

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

    if history and isinstance(history, list) and len(history) > 0:
        for msg in history:
            if "user" in msg and isinstance(msg["user"], str):
                q = msg["user"].lower()
                if any(x in q for x in ["health plan", "healthplan", "realplan"]):
                    tema_healthplan = True
                    break
                elif "acne" in q:
                    tema_acne = True
                    break
                elif any(x in q for x in PLANO_ACAO_KEYWORDS):
                    tema_plano_acao = True
                    break
                elif any(x in q for x in GUIA_CURSO_KEYWORDS):
                    tema_guia_curso = True
                    break
                elif any(x in q for x in DOSSIÊ_007_KEYWORDS):
                    tema_dossie_007 = True
                    break
    else:
        q = question.lower()
        if any(x in q for x in ["health plan", "healthplan", "realplan"]):
            tema_healthplan = True
        elif "acne" in q:
            tema_acne = True
        elif any(x in q for x in PLANO_ACAO_KEYWORDS):
            tema_plano_acao = True
        elif any(x in q for x in GUIA_CURSO_KEYWORDS):
            tema_guia_curso = True
        elif any(x in q for x in DOSSIÊ_007_KEYWORDS):
            tema_dossie_007 = True

    replies = []
    if tema_healthplan:
        replies += ["Ver Exemplo de Plano", "Modelo no Canva"]
    elif tema_acne:
        replies += ["Exemplo para Acne", "Tratamento Oral", "Cuidados Diários"]
    if tema_plano_acao:
        replies += ["Baixar Plano de Ação"]
    if tema_guia_curso:
        replies += ["Baixar Guia do Curso"]
    if tema_dossie_007:
        replies += ["Baixar Dossiê 007"]
    if not replies:
        replies = base_replies

    usados = set()
    if history and isinstance(history, list):
        for msg in history:
            if "chip" in msg and msg["chip"]:
                usados.add(msg["chip"].strip().lower())
            if "user" in msg and msg["user"]:
                u = msg["user"].strip().lower()
                if u in [x.lower() for x in replies]:
                    usados.add(u)
    ESSENCIAIS = ["modelo no canva", "baixar plano de ação", "baixar guia do curso", "baixar dossiê 007"]
    filtered = []
    for r in replies:
        if r.lower() in ESSENCIAIS:
            if r.lower() not in usados:
                filtered.append(r)
        else:
            if r.lower() not in usados:
                filtered.append(r)
    if len(filtered) < 2:
        filtered += [r for r in base_replies if r not in filtered]
    return filtered[:3]

def resposta_link_didatica(material, url, explicacao):
    return (
        f"{explicacao}<br><br>"
        f"<a class='chip' href='{url}' target='_blank'>📄 Baixar {material}</a><br>"
        "Se precisar de orientação ou tiver dúvidas sobre como aplicar, é só perguntar!"
    )

def generate_answer(
    question, context="", history=None, tipo_de_prompt=None, is_first_question=True
):
    cumprimento_detectado = is_greeting(question)
    pergunta_limpa = remove_greeting_from_question(question)

    # Blocos especiais DIDÁTICOS + LINK

    # 1. Plano de Ação
    PLANO_ACAO_KEYWORDS = [
        "plano de ação", "pdf plano de ação", "atividade da primeira semana",
        "material do onboarding", "ação consultório", "plano onboarding",
        "plano de ação consultório", "atividade plano", "baixar plano de ação"
    ]
    if any(x in pergunta_limpa for x in PLANO_ACAO_KEYWORDS) or \
        (question and any(x in question.lower() for x in PLANO_ACAO_KEYWORDS)):
        explicacao = (
            "O Plano de Ação é um roteiro prático para organizar seus primeiros passos no curso e iniciar sua transformação no consultório. "
            "Utilize esse material no onboarding para definir metas, identificar bloqueios e planejar ações concretas semana a semana."
        )
        return resposta_link_didatica("Plano de Ação do Consultório High Ticket", 
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EV6wZ42I9nhHpmnSGa4DHfEBaff0ewZIsmH_4LqLAI46eQ?e=gd5hR0", explicacao), []

    # 2. Patient Letter
    PATIENT_LETTER_KEYWORDS = [
        "patient letter", "carta patient letter", "pdf patient letter", "modelo patient letter", "baixar patient letter", "patient letter do curso"
    ]
    if any(x in pergunta_limpa for x in PATIENT_LETTER_KEYWORDS) or \
        (question and any(x in question.lower() for x in PATIENT_LETTER_KEYWORDS)):
        explicacao = (
            "A Patient Letter é um modelo de comunicação entre profissionais de saúde. Pode (e deve) ser enviada tanto para pacientes novos quanto antigos, sempre que houver encaminhamento, comunicação de acompanhamento ou atualizações relevantes. "
            "Você pode enviar a cada novo tratamento, retorno importante ou atualização clínica do paciente."
        )
        return resposta_link_didatica(
            "Patient Letter – Modelo Oficial",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EbdJ4rqiywhOjG0Yy3cDhjYBf04FMiNmoOXos4M5eZmoaA?e=90kaBp",
            explicacao
        ), []

    # 3. Guia do Curso
    GUIA_CURSO_KEYWORDS = [
        "guia do curso", "guia cht", "guia consultório high ticket",
        "manual do curso", "manual cht", "material de onboarding",
        "passos iniciais", "guia onboarding", "baixar guia do curso"
    ]
    if any(x in pergunta_limpa for x in GUIA_CURSO_KEYWORDS) or \
        (question and any(x in question.lower() for x in GUIA_CURSO_KEYWORDS)):
        explicacao = (
            "O Guia do Curso Consultório High Ticket orienta você nos primeiros passos após o onboarding, explicando como acessar materiais, participar da comunidade e organizar sua rotina de estudos para extrair o máximo do método."
        )
        return resposta_link_didatica(
            "Guia do Curso Consultório High Ticket",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EQZrQJpHXlVCsK1N5YdDIHEBHocn7FR2yQUHhydgN84yOw?e=GAut9r",
            explicacao
        ), []

    # 4. Dossiê 007
    DOSSIÊ_007_KEYWORDS = [
        "dossiê 007", "dossie 007", "dossiê captação", "dossie aula 5.8",
        "captação de pacientes", "estratégias 007", "baixar dossiê 007"
    ]
    if any(x in pergunta_limpa for x in DOSSIÊ_007_KEYWORDS) or \
        (question and any(x in question.lower() for x in DOSSIÊ_007_KEYWORDS)):
        explicacao = (
            "O Dossiê 007 reúne estratégias exclusivas para captação e fidelização de pacientes High Ticket, com roteiros, scripts e táticas para aplicar imediatamente no seu consultório."
        )
        return resposta_link_didatica(
            "Dossiê 007 – Captação de Pacientes High Ticket",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVdOpjU1frVBhApTKmmYAwgBFkbNggnj2Cp0w9luTajxgg?e=iQOnk0",
            explicacao
        ), []

    # 5. Health Plan (Canva)
    if "modelo no canva" in pergunta_limpa or "modelo health plan" in pergunta_limpa or "modelo healthplan" in pergunta_limpa or "modelo de health plan" in pergunta_limpa:
        explicacao = (
            "O modelo de Health Plan no Canva é totalmente editável e pode ser personalizado para cada paciente e especialidade. Utilize esse material para estruturar planos de acompanhamento e entregar ao paciente em cada etapa do tratamento."
        )
        return resposta_link_didatica(
            "Modelo de Health Plan no Canva",
            "https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview",
            explicacao
        ), []

    # 6. Playlist Spotify
    SPOTIFY_KEYWORDS = [
        "playlist spotify", "playlist no spotify", "música spotify", "spotify do curso", "link spotify", "playlist do curso"
    ]
    if any(x in pergunta_limpa for x in SPOTIFY_KEYWORDS) or \
        (question and any(x in question.lower() for x in SPOTIFY_KEYWORDS)):
        explicacao = (
            "Ouça a Playlist Oficial do Consultório High Ticket no Spotify para potencializar sua concentração, motivação e foco nos estudos e no consultório."
        )
        return (
            f"{explicacao}<br><br>"
            "<a class='chip' href='https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80' target='_blank'>🎵 Ouvir Playlist no Spotify</a><br>"
            "Se quiser recomendações de músicas para concentração ou foco nos estudos, é só pedir!"
        ), []

    # 7. Scripts da Secretária
    SECRETARIA_KEYWORDS = [
        "scripts da secretária", "script da secretária", "roteiro secretária",
        "pdf scripts secretária", "modelo de secretária", "secretaria", "secretária"
    ]
    if any(x in pergunta_limpa for x in SECRETARIA_KEYWORDS) or \
        (question and any(x in question.lower() for x in SECRETARIA_KEYWORDS)):
        explicacao = (
            "Os scripts da secretária são fundamentais para garantir um atendimento organizado, profissional e que gere segurança ao paciente desde o primeiro contato. Use esses roteiros para padronizar agendamentos, confirmações, orientações pré-consulta e reagendamentos. "
            "Você pode adaptar os scripts para a realidade do seu consultório e treinar sua secretária para aplicar cada situação."
        )
        return resposta_link_didatica(
            "Scripts da Secretária – Consultório High Ticket",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVgtSPvwpw9OhOS4CibHXGYB7KNAolar5o0iY2I2dOKCAw?e=LVZlX3",
            explicacao
        ), []

    # (restante da função continua igual...)

    is_chip = any(question.strip().lower() == c.lower() for c in CHIP_PERGUNTAS)
    mostrar_saudacao = is_first_question and not is_chip
    mostrar_pergunta_repetida = is_first_question and not is_chip

    saudacao = random.choice(GREETINGS) if mostrar_saudacao else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(pergunta_limpa if pergunta_limpa.strip() else question)
    pergunta_repetida = (
        f"<strong>Sua pergunta:</strong> \"{question}\"<br><br>" if mostrar_pergunta_repetida else ""
    )

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
    quick_replies = gerar_quick_replies(question, explicacao, history)

    resposta = ""
    if mostrar_saudacao:
        resposta += f"{saudacao}<br><br>{pergunta_repetida}{explicacao}<br><br>{fechamento}"
    else:
        resposta += f"{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies
