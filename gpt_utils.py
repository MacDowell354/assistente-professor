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

def resposta_link_botao(material, url):
    return (
        f"<br><a class='chip' href='{url}' target='_blank'>📄 Baixar {material}</a>"
    )

def chamar_gpt(prompt):
    # Você pode ajustar aqui para usar o modelo certo (gpt-4o-mini ou gpt-3.5-turbo)
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
        return response.choices[0].message.content.strip()
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
        return response.choices[0].message.content.strip()

def generate_answer(
    question, context="", history=None, tipo_de_prompt=None, is_first_question=True
):
    cumprimento_detectado = is_greeting(question)
    pergunta_limpa = remove_greeting_from_question(question)

    # 1. Plano de Ação
    PLANO_ACAO_KEYWORDS = [
        "plano de ação", "pdf plano de ação", "atividade da primeira semana",
        "material do onboarding", "ação consultório", "plano onboarding",
        "plano de ação consultório", "atividade plano", "baixar plano de ação"
    ]
    if any(x in pergunta_limpa for x in PLANO_ACAO_KEYWORDS) or \
        (question and any(x in question.lower() for x in PLANO_ACAO_KEYWORDS)):
        snippet = search_transcripts_by_theme("plano de ação")
        prompt = (
            f"Com base no conteúdo abaixo do curso Consultório High Ticket, explique de forma didática como o médico pode usar o Plano de Ação para organizar o início da sua jornada, definir metas e planejar ações semanais. Seja prático e objetivo.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = resposta_link_botao("Plano de Ação do Consultório High Ticket", 
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EV6wZ42I9nhHpmnSGa4DHfEBaff0ewZIsmH_4LqLAI46eQ?e=gd5hR0")
        return f"{resposta_ia}{link}", []

    # 2. Patient Letter
    PATIENT_LETTER_KEYWORDS = [
        "patient letter", "carta patient letter", "pdf patient letter", "modelo patient letter", "baixar patient letter", "patient letter do curso"
    ]
    if any(x in pergunta_limpa for x in PATIENT_LETTER_KEYWORDS) or \
        (question and any(x in question.lower() for x in PATIENT_LETTER_KEYWORDS)):
        snippet = search_transcripts_by_theme("patient letter")
        prompt = (
            f"Com base no conteúdo do curso Consultório High Ticket abaixo, explique de forma prática e didática como, quando e para quem o médico deve enviar a Patient Letter. Responda considerando as melhores práticas ensinadas nas aulas. Cite exemplos e seja direto.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = resposta_link_botao(
            "Patient Letter – Modelo Oficial",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EbdJ4rqiywhOjG0Yy3cDhjYBf04FMiNmoOXos4M5eZmoaA?e=90kaBp"
        )
        return f"{resposta_ia}{link}", []

    # 3. Guia do Curso
    GUIA_CURSO_KEYWORDS = [
        "guia do curso", "guia cht", "guia consultório high ticket",
        "manual do curso", "manual cht", "material de onboarding",
        "passos iniciais", "guia onboarding", "baixar guia do curso"
    ]
    if any(x in pergunta_limpa for x in GUIA_CURSO_KEYWORDS) or \
        (question and any(x in question.lower() for x in GUIA_CURSO_KEYWORDS)):
        snippet = search_transcripts_by_theme("guia do curso")
        prompt = (
            f"Com base no curso Consultório High Ticket, explique para que serve o Guia do Curso, como utilizá-lo no onboarding e o que não pode deixar de ser feito nos primeiros passos. Seja didático e prático.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = resposta_link_botao(
            "Guia do Curso Consultório High Ticket",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EQZrQJpHXlVCsK1N5YdDIHEBHocn7FR2yQUHhydgN84yOw?e=GAut9r"
        )
        return f"{resposta_ia}{link}", []

    # 4. Dossiê 007
    DOSSIÊ_007_KEYWORDS = [
        "dossiê 007", "dossie 007", "dossiê captação", "dossie aula 5.8",
        "captação de pacientes", "estratégias 007", "baixar dossiê 007"
    ]
    if any(x in pergunta_limpa for x in DOSSIÊ_007_KEYWORDS) or \
        (question and any(x in question.lower() for x in DOSSIÊ_007_KEYWORDS)):
        snippet = search_transcripts_by_theme("dossiê 007")
        prompt = (
            f"Com base no conteúdo do curso Consultório High Ticket, explique de forma prática para que serve o Dossiê 007, como utilizá-lo na captação de pacientes e os benefícios de aplicar as estratégias sugeridas. Seja direto.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = resposta_link_botao(
            "Dossiê 007 – Captação de Pacientes High Ticket",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVdOpjU1frVBhApTKmmYAwgBFkbNggnj2Cp0w9luTajxgg?e=iQOnk0"
        )
        return f"{resposta_ia}{link}", []

    # 5. Health Plan (Canva)
    if "modelo no canva" in pergunta_limpa or "modelo health plan" in pergunta_limpa or "modelo healthplan" in pergunta_limpa or "modelo de health plan" in pergunta_limpa:
        snippet = search_transcripts_by_theme("health plan")
        prompt = (
            f"Com base no curso Consultório High Ticket, explique de forma didática como usar o modelo de Health Plan editável do Canva para estruturar o plano de tratamento do paciente. Dê dicas práticas de uso para médicos.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = resposta_link_botao(
            "Modelo de Health Plan no Canva",
            "https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview"
        )
        return f"{resposta_ia}{link}", []

    # 6. Playlist Spotify
    SPOTIFY_KEYWORDS = [
        "playlist spotify", "playlist no spotify", "música spotify", "spotify do curso", "link spotify", "playlist do curso"
    ]
    if any(x in pergunta_limpa for x in SPOTIFY_KEYWORDS) or \
        (question and any(x in question.lower() for x in SPOTIFY_KEYWORDS)):
        snippet = search_transcripts_by_theme("playlist")
        prompt = (
            f"Com base no curso Consultório High Ticket, explique a importância da playlist do Spotify para concentração, motivação e foco nos estudos do médico. Dê sugestões de uso.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = (
            "<br><a class='chip' href='https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80' target='_blank'>🎵 Ouvir Playlist no Spotify</a>"
        )
        return f"{resposta_ia}{link}", []

    # 7. Scripts da Secretária
    SECRETARIA_KEYWORDS = [
        "scripts da secretária", "script da secretária", "roteiro secretária",
        "pdf scripts secretária", "modelo de secretária", "secretaria", "secretária"
    ]
    if any(x in pergunta_limpa for x in SECRETARIA_KEYWORDS) or \
        (question and any(x in question.lower() for x in SECRETARIA_KEYWORDS)):
        snippet = search_transcripts_by_theme("scripts secretária")
        prompt = (
            f"Com base no curso Consultório High Ticket, explique de forma didática como os scripts da secretária ajudam na padronização do atendimento e na experiência do paciente, e como aplicar esses modelos no consultório médico. Seja prático.\n\n"
            f"Pergunta: {question}\n\n"
            f"Conteúdo do curso:\n{snippet}\n"
        )
        resposta_ia = chamar_gpt(prompt)
        link = resposta_link_botao(
            "Scripts da Secretária – Consultório High Ticket",
            "https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVgtSPvwpw9OhOS4CibHXGYB7KNAolar5o0iY2I2dOKCAw?e=LVZlX3"
        )
        return f"{resposta_ia}{link}", []

    # SEGUE fluxo normal se não for nenhum dos materiais especiais
    is_chip = any(question.strip().lower() == c.lower() for c in CHIP_PERGUNTAS)
    mostrar_saudacao = is_first_question and not is_chip
    mostrar_pergunta_repetida = is_first_question and not is_chip

    saudacao = random.choice(GREETINGS) if mostrar_saudacao else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(pergunta_limpa if pergunta_limpa.strip() else question)
    pergunta_repetida = (
        f"<strong>Sua pergunta:</strong> \"{question}\"<br><br>" if mostrar_pergunta_repetida else ""
    )

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

    explicacao = chamar_gpt(prompt)
    quick_replies = gerar_quick_replies(question, explicacao, history)

    resposta = ""
    if mostrar_saudacao:
        resposta += f"{saudacao}<br><br>{pergunta_repetida}{explicacao}<br><br>{fechamento}"
    else:
        resposta += f"{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies
