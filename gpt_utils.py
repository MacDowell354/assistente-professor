import os
import json
from openai import OpenAI, OpenAIError
from pypdf import PdfReader

# -----------------------------
# CONFIGURAÇÃO DE AMBIENTE
# -----------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")
client = OpenAI(api_key=api_key)

# -----------------------------
# MENSAGEM PADRÃO PARA FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# CARREGA TRANSCRIÇÕES E PDFs
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

TRANSCRIPT_PATH = os.path.join(BASE_DIR, "transcricoes.txt")
_raw_txt = open(TRANSCRIPT_PATH, encoding="utf-8").read()

PDF1_PATH = os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf")
_raw_pdf1 = ""
try:
    reader1 = PdfReader(PDF1_PATH)
    _raw_pdf1 = "\n\n".join(page.extract_text() or "" for page in reader1.pages)
except:
    _raw_pdf1 = ""

PDF2_PATH = os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf")
_raw_pdf2 = ""
try:
    reader2 = PdfReader(PDF2_PATH)
    _raw_pdf2 = "\n\n".join(page.extract_text() or "" for page in reader2.pages)
except:
    _raw_pdf2 = ""

# Combina tudo para gerar um resumo (usado para classificação)
_combined = _raw_txt + "\n\n" + _raw_pdf1 + "\n\n" + _raw_pdf2
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":
                "Você é um resumidor especialista em educação. "
                "Resuma em até 300 palavras todo o conteúdo do curso 'Consultório High Ticket', "
                "incluindo o Plano de Ação (1ª Semana) e o Guia do Curso, para servir de base na classificação."
            },
            {"role": "user", "content": _combined}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# MAPA DE KEYWORDS PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao": ["revisão", "revisao", "revise", "resumir"],
    "precificacao": ["precificação", "precificacao", "precificar", "preço", "valor", "faturamento"],
    "health_plan": ["health plan", "valor do health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital": ["offline", "sem usar instagram", "sem instagram", "sem anúncios", "sem anuncios"],
    "aplicacao": ["como aplico", "aplicação", "aplico", "roteiro", "aplicação"],
    "faq": ["quais", "dúvidas", "duvidas", "pergunta frequente"],
    "explicacao": ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao": ["plano de ação", "primeira semana", "1ª semana"],
    "guia": ["guia do curso", "passo a passo", "CHT21"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS (Guia + Plano de Ação)
# -----------------------------
CANONICAL_QA = {
    # Guia do Curso
    "quais são os quatro passos iniciais descritos no guia do curso consultório high ticket para começar a participação?":
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo exclusivo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em \"Participar\".",
    "o que o participante deve fazer após entrar na área de membros para dar o primeiro passo no desafio health plan?":
        "1. <strong>Clicar em \"Participar\"</strong> no módulo Desafio Health Plan.<br>"
        "2. <strong>Fechar</strong> a janela de confirmação.<br>"
        "3. Clicar novamente em <strong>\"Participar\"</strong> na próxima tela.",
    "como é estruturado o mapa de atividades do desafio health plan em termos de fases e prazos?":
        "O Desafio Health Plan é dividido em três fases, sem considerar datas específicas:<br>"
        "<strong>Fase 1 – Missão inicial:</strong> assistir módulos 1–6 e preencher quiz;<br>"
        "<strong>Fase 2 – Masterclass e envio do Health Plan:</strong> participar da masterclass e enviar seu primeiro plano;<br>"
        "<strong>Fase 3 – Missões semanais:</strong> enviar planners semanais e concluir atividades de encerramento.",
    "caso o participante enfrente uma situação crítica, qual procedimento deve ser adotado para solicitar suporte?":
        "Em situação crítica, envie e-mail para <strong>ajuda@nandamac.com</strong> com assunto 'S.O.S Crise'. A equipe retornará em até 24h.",
    "onde e como o participante deve tirar dúvidas sobre o método do curso?":
        "Dúvidas sobre o método devem ser postadas exclusivamente na <strong>Comunidade</strong> da Área de Membros. Não use Direct, WhatsApp ou outros canais.",

    # Plano de Ação (1ª Semana)
    "nanda, no exercício de bloqueios com dinheiro, como faço para escolher qual bloqueio priorizar e definir minha atitude dia do chega?":
        "Primeiro, identifique qual sentimento de culpa ao cobrar mais te afeta (\"Síndrome do Sacerdote\"). "
        "Escolha esse bloqueio como prioritário. Em 'Onde quero chegar', escreva uma ação concreta, "
        "por exemplo: \"A partir de hoje, afirmarei meu valor em cada consulta.\"",
    "na parte de autoconfiança profissional, o que devo escrever como atitude para não deixar certas situações me abalar?":
        "Liste duas situações que abalaram sua confiança. Em 'Onde quero chegar', defina uma atitude transformadora, "
        "por exemplo: \"Sempre que receber críticas, realizarei autoavaliação e buscarei feedback construtivo.\"",
    "como eu uso a atividade de nicho de atuação para saber se devo mudar meu foco e quais ações listar?":
        "Descreva seu posicionamento atual (pontos fortes e lacunas) e defina seu nicho ideal (pacientes sonhos). "
        "Liste ações com prazo, por exemplo: \"Especializar em [X] em 3 meses.\"",
    "no valor da consulta e procedimentos, como encontro referências de mercado e defino meus valores atuais e ideais?":
        "Liste seus valores atuais, pesquise médias de mercado via associações ou colegas, "
        "e defina valores ideais justificando seu diferencial, como: \"R$ 300 por sessão de fisioterapia clínica.\"",
    "ainda não tenho pacientes particulares. qual estratégia de atração de pacientes high ticket devo priorizar e como executar na agenda?":
        "Reserve na agenda um bloco fixo (ex.: toda segunda das 8h às 10h) para enviar 5 mensagens personalizadas ao Mercado X "
        "usando o script do curso. Ao iniciar atendimentos, implemente a Patient Letter com convites impressos para potenciais pacientes High Ticket."
}

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
        "com tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula de **Posicionamento High Ticket**.<br><br>"
    ),
    "faq": (
        "<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. "
        "Use exemplos práticos e aplique o método passo a passo."
    ),
    "revisao": (
        "<strong>Objetivo:</strong> Fazer uma revisão rápida dos pontos centrais do método de precificação estratégica. "
        "Use exatamente seis bullets, cada um iniciando com verbo de ação e título em negrito: "
        "**Identificar Pacientes Potenciais**, **Determinar Valores**, **Elaborar o Health Plan**, "
        "**Preparar a Apresentação**, **Comunicar o Valor** e **Monitorar Resultados**. "
        "Após o título de cada bullet, adicione uma breve explicação de uma linha. "
        "E **certifique-se de mencionar o benefício de dobrar o faturamento e fidelizar pacientes** em pelo menos dois desses bullets.<br><br>"
    ),
    "aplicacao": (
        "<strong>Objetivo:</strong> Aplicar o roteiro de atendimento High Ticket na primeira consulta. "
        "Use exatamente seis bullets, cada um iniciando com verbo de ação e estes títulos em negrito:<br>"
        "➡ **Abertura da Consulta:** Garanta acolhimento profissional, transmitindo exclusividade e empatia.<br>"
        "➡ **Mapear Expectativas:** Pergunte objetivos e preocupações do paciente, construindo rapport.<br>"
        "➡ **Elaborar Health Plan:** Explique o **Health Plan** personalizado, detalhando etapas e investimento.<br>"
        "➡ **Validar Compromisso:** Confirme entendimento do paciente e mencione potencial de dobrar faturamento.<br>"
        "➡ **Usar Two-Options:** Ofereça duas opções de pacote, reduzindo objeções e gerando segurança.<br>"   
        "➡ **Agendar Follow-up:** Marque retorno imediato para manter engajamento e fidelizar pacientes.<br><br>"
    ),
    "correcao": (
        "<strong>Objetivo:</strong> Corrigir gentilmente qualquer confusão ou prática equivocada do aluno, "
        "apontando a abordagem correta conforme o método High Ticket. Mostre por que o ajuste sugerido pode trazer melhores resultados, "
        "especialmente em termos de posicionamento, fidelização ou faturamento.<br><br>"
    ),
    "capitacao_sem_marketing_digital": (
        "<strong>Objetivo:</strong> Mostrar uma **estratégia 100% offline** do método Consultório High Ticket para atrair pacientes "
        "de alto valor sem usar Instagram ou anúncios, passo a passo:<br>"
        "➡ **Encantamento de pacientes atuais:** Envie um convite VIP impresso ou bilhete manuscrito;<br>"
        "➡ **Parcerias com profissionais de saúde:** Conecte-se com médicos, fisioterapeutas, nutricionistas e psicólogos;<br>"
        "➡ **Cartas personalizadas com proposta VIP:** Envie convites impressos destacando diferenciais;<br>"
        "➡ **Manutenção via WhatsApp (sem automação):** Grave e envie mensagem de voz após a consulta;<br>"
        "➡ **Construção de autoridade silenciosa:** Colete depoimentos reais e imprima folhetos;<br>"
        "➡ **Fidelização e indicações espontâneas:** Implemente o programa “Indique um amigo VIP”.<br><br>"
        "Com essa sequência você <strong>dobra seu faturamento</strong> e conquista pacientes de alto valor sem depender de redes sociais ou anúncios."
    ),
    "precificacao": (
        "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica do Consultório High Ticket. "
        "Use bullets iniciando com verbo de ação, mantenha **Health Plan** em inglês, e destaque como dobrar faturamento, "
        "fidelizar pacientes e priorizar o bem-estar do paciente.<br><br>"
    ),
    "health_plan": (
        "<strong>Objetivo:</strong> Estruturar a apresentação de valor do **Health Plan** para demonstrar o retorno sobre o investimento. "
        "Use passos sequenciais, inclua benefícios tangíveis e histórias de sucesso para emocionar o paciente.<br><br>"
    ),
    "plano_de_acao": (
        "<strong>Objetivo:</strong> Auxiliar o aluno a completar o **Plano de Ação (1ª Semana)**, "
        "abordando etapas como **Bloqueios com dinheiro**, **Autoconfiança**, **Nicho**, **Valor dos serviços**, "
        "**Convênios vs Particulares**, **Ambiente do consultório** e **Ações de atração high ticket**.<br><br>"
    ),
    "guia": (
        "<strong>Objetivo:</strong> Explorar o **Guia do Curso Consultório High Ticket**, "
        "apresentando o passo a passo sugerido no documento com clareza sequencial.<br><br>"
    ),
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()
    if "exercício" in lower_q or "exercicios" in lower_q:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}
    for tipo, keywords in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in keywords):
            return {"scope": "IN_SCOPE", "type": tipo}
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, "
        "responda apenas um JSON com duas chaves: scope ('IN_SCOPE'/'OUT_OF_SCOPE') e type (nome do template).\n\n"
        f"Resumo do curso:\n{COURSE_SUMMARY}\n\nPergunta:\n{question}"
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": payload}]
        )
        return json.loads(r.choices[0].message.content)
    except:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(question: str, context: str = "", history: str = None) -> str:
    key = question.strip().lower()
    if key in CANONICAL_QA:
        return CANONICAL_QA[key]
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG
    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto relevante:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"
    try:
        r2 = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        r2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
    return r2.choices[0].message.content
