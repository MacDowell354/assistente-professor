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
    "Baixar Plano de Ação", "Baixar Guia do Curso", "Baixar Dossiê 007", "Baixar Check-list"
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
    tema_checklist = False

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
    CHECKLIST_KEYWORDS = [
        "check-list consultório", "checklist consultório", "checklist high ticket",
        "check-list high ticket", "checklist aula 6.8", "baixar check-list", "checklist cht"
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
                elif any(x in q for x in CHECKLIST_KEYWORDS):
                    tema_checklist = True
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
        elif any(x in q for x in CHECKLIST_KEYWORDS):
            tema_checklist = True

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
    if tema_checklist:
        replies += ["Baixar Check-list"]
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
    ESSENCIAIS = [
        "modelo no canva", "baixar plano de ação", "baixar guia do curso", "baixar dossiê 007", "baixar check-list"
    ]
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

def generate_answer(
    question, context="", history=None, tipo_de_prompt=None, is_first_question=True
):
    cumprimento_detectado = is_greeting(question)
    pergunta_limpa = remove_greeting_from_question(question)

    # --- Bloco especial: PDF Plano de Ação ---
    PLANO_ACAO_KEYWORDS = [
        "plano de ação", "pdf plano de ação", "atividade da primeira semana",
        "material do onboarding", "ação consultório", "plano onboarding",
        "plano de ação consultório", "atividade plano", "baixar plano de ação"
    ]
    pergunta_baixar_plano = any(x in pergunta_limpa for x in PLANO_ACAO_KEYWORDS) or \
        (question and any(x in question.lower() for x in PLANO_ACAO_KEYWORDS))
    if pergunta_baixar_plano or (question.strip().lower() == "baixar plano de ação"):
        resposta = (
            "<strong>Plano de Ação do Consultório High Ticket</strong><br>"
            "Esse material faz parte do onboarding do curso e é essencial para você organizar seus próximos passos.<br><br>"
            "<b>O que você vai encontrar nesse PDF:</b><br>"
            "- Reflexão sobre bloqueios financeiros e autoconfiança<br>"
            "- Definição de nicho de atuação e ajustes de posicionamento<br>"
            "- Planejamento de ações práticas para atrair pacientes High Ticket já na primeira semana<br>"
            "- Exercícios para transformar sua mentalidade e o consultório<br><br>"
            "<a class='chip' href='https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EV6wZ42I9nhHpmnSGa4DHfEBaff0ewZIsmH_4LqLAI46eQ?e=gd5hR0' target='_blank'>📄 Baixar Plano de Ação do Consultório High Ticket</a><br><br>"
            "Você também pode baixar esse PDF dentro do módulo de onboarding, na sua área de alunos.<br>"
            "Se tiver dificuldade para acessar, me avise que envio suporte!"
        )
        return resposta, []

    # --- Bloco especial: PDF Guia do Curso ---
    GUIA_CURSO_KEYWORDS = [
        "guia do curso", "guia cht", "guia consultório high ticket",
        "manual do curso", "manual cht", "material de onboarding",
        "passos iniciais", "guia onboarding", "baixar guia do curso"
    ]
    pergunta_guia_curso = any(x in pergunta_limpa for x in GUIA_CURSO_KEYWORDS) or \
        (question and any(x in question.lower() for x in GUIA_CURSO_KEYWORDS))
    if pergunta_guia_curso or (question.strip().lower() == "baixar guia do curso"):
        resposta = (
            "<strong>Guia do Curso Consultório High Ticket</strong><br>"
            "Esse material é essencial para te orientar nos primeiros passos do curso, desde o onboarding até as tarefas e integração na comunidade.<br><br>"
            "<b>O que você encontra nesse guia:</b><br>"
            "- Passo a passo para assistir à aula de onboarding<br>"
            "- Como entrar no grupo de avisos da sua turma<br>"
            "- Como acessar a área de membros e comunidade<br>"
            "- Detalhes sobre o Desafio Health Plan<br>"
            "- Como participar das atividades da primeira semana<br>"
            "- Canais de suporte e regras de uso<br><br>"
            "<a class='chip' href='https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EQZrQJpHXlVCsK1N5YdDIHEBHocn7FR2yQUHhydgN84yOw?e=GAut9r' target='_blank'>📄 Baixar Guia do Curso Consultório High Ticket</a><br><br>"
            "Você também pode encontrar esse PDF fixado no módulo de onboarding da sua área de alunos.<br>"
            "Se precisar de ajuda para acessar, me avise por aqui!"
        )
        return resposta, []

    # --- Bloco especial: PDF Dossiê 007 ---
    DOSSIÊ_007_KEYWORDS = [
        "dossiê 007", "dossie 007", "dossiê captação", "dossie aula 5.8",
        "captação de pacientes", "estratégias 007", "baixar dossiê 007"
    ]
    pergunta_dossie_007 = any(x in pergunta_limpa for x in DOSSIÊ_007_KEYWORDS) or \
        (question and any(x in question.lower() for x in DOSSIÊ_007_KEYWORDS))
    if pergunta_dossie_007 or (question.strip().lower() == "baixar dossiê 007"):
        resposta = (
            "<strong>Dossiê 007 – Captação de Pacientes High Ticket</strong><br>"
            "Esse material especial faz parte da Aula 5.8 do curso e reúne 3 estratégias comprovadas para você captar, reter e fidelizar pacientes High Ticket de forma ética e lucrativa.<br><br>"
            "<b>O que você encontra nesse PDF:</b><br>"
            "- Networking inteligente com outros profissionais da saúde para gerar indicações<br>"
            "- Scripts prontos para confirmação e remarcação de consultas (elimine faltas e remarcações)<br>"
            "- Scripts e estratégias para reativar pacientes antigos<br>"
            "- Técnicas de encantamento, reciprocidade e presentes memoráveis para fidelizar<br><br>"
            "<a class='chip' href='https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EVdOpjU1frVBhApTKmmYAwgBFkbNggnj2Cp0w9luTajxgg?e=iQOnk0' target='_blank'>📄 Baixar Dossiê 007 – Captação de Pacientes High Ticket</a><br><br>"
            "Esse PDF está disponível na Aula 5.8 do Módulo 5 e pode ser baixado sempre que precisar.<br>"
            "Se tiver qualquer dúvida para aplicar as ações, pode me perguntar por aqui!"
        )
        return resposta, []

    # --- Bloco especial: PDF Check-list Consultório High Ticket ---
    CHECKLIST_KEYWORDS = [
        "check-list consultório", "checklist consultório", "checklist high ticket",
        "check-list high ticket", "checklist aula 6.8", "baixar check-list", "checklist cht"
    ]
    pergunta_checklist = any(x in pergunta_limpa for x in CHECKLIST_KEYWORDS) or \
        (question and any(x in question.lower() for x in CHECKLIST_KEYWORDS))
    if pergunta_checklist or (question.strip().lower() == "baixar check-list"):
        resposta = (
            "<strong>Check-list do Consultório High Ticket</strong><br>"
            "Esse material prático da Aula 6.8 traz uma lista detalhada de ajustes para transformar seu consultório em um ambiente High Ticket, desde atendimento e linguagem até ambiente físico e equipe.<br><br>"
            "<b>O que você encontra neste check-list:</b><br>"
            "- Adaptação da linguagem para encantar e fidelizar pacientes<br>"
            "- Scripts e rotinas para atendimento High Ticket<br>"
            "- Padrão visual e organização do ambiente<br>"
            "- Brindes, política de descontos, apresentação de valores<br>"
            "- Check-list por etapas: atendimento, ambiente, posicionamento digital e mais<br><br>"
            "<a class='chip' href='https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EaV1U2Y-6CZHoVL8DhxYDXQBeMienn2uZG4Qsruo1sBcuw?e=pTXlmu' target='_blank'>📄 Baixar Check-list do Consultório High Ticket</a><br><br>"
            "Esse PDF está disponível na Aula 6.8 e pode ser baixado a qualquer momento.<br>"
            "Se quiser detalhar algum item ou receber dicas práticas para aplicar cada etapa, é só perguntar!"
        )
        return resposta, []

    # Evita saudação/repetição para chips
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
