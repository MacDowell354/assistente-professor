import os
import json
from openai import OpenAI, OpenAIError

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
# CARREGA E RESUME TRANSCRIÇÕES (1× NO STARTUP)
# -----------------------------
TRANSCRIPT_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")
_raw = open(TRANSCRIPT_PATH, encoding="utf-8").read()
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um resumidor especialista em educação. "
                    "Resuma em até 300 palavras o conteúdo do curso “Consultório High Ticket” "
                    "para servir de base na classificação de escopo e tipo de prompt."
                )
            },
            {"role": "user", "content": _raw}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# LISTA DE PALAVRAS FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_KEYWORDS = [
    "exercício", "exercicios", "costas", "coluna", "dor", "em casa"
]

# -----------------------------
# MAPA DE KEYWORDS PARA TIPO DE PROMPT
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revisao", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificacao", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "valor do health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital":["offline", "sem usar instagram", "sem instagram", "sem anúncios", "sem anuncios"],
    "aplicacao":                      ["como aplico", "aplicação", "aplico", "roteiro"],
    "faq":                            ["quais", "dúvidas", "duvidas", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"]
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()

    # 0) Detecção imediata de perguntas fora de escopo
    if any(kw in lower_q for kw in OUT_OF_SCOPE_KEYWORDS):
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

    # 1) Match rápido por palavras-chave de tipo
    for tipo, keywords in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in keywords):
            return {"scope": "IN_SCOPE", "type": tipo}

    # 2) Fallback inteligente via GPT
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, "
        "responda **apenas** um JSON com duas chaves:\n"
        "  • scope: 'IN_SCOPE' ou 'OUT_OF_SCOPE'\n"
        "  • type: nome de um template (ex: 'explicacao', 'health_plan', 'precificacao', etc)\n\n"
        f"Resumo do curso:\n{COURSE_SUMMARY}\n\n"
        f"Pergunta:\n{question}\n\n"
        "Exemplo de resposta válida:\n"
        '{ "scope": "IN_SCOPE", "type": "health_plan" }'
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": payload}]
        )
        return json.loads(r.choices[0].message.content)
    except (OpenAIError, json.JSONDecodeError):
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

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
        "➡ **Fidelização e indicações espontâneas:** Implemente o programa “Indique um amigo VIP”;<br><br>"
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
    )
}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None
) -> str:
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    tipo = cls["type"]
    if tipo == "capitacao_sem_marketing_digital":
        contexto_para_prompt = ""
    else:
        contexto_para_prompt = (
            f"<br><br><strong>📚 Contexto relevante:</strong><br>{context}<br>"
            if context.strip() else ""
        )

    prompt = identidade + prompt_variacoes[tipo] + contexto_para_prompt
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
