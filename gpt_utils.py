import os
import re
import unicodedata
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
    "Essa pergunta é muito boa, mas no momento ela está "
    "<strong>fora do conteúdo abordado nas aulas do curso Consultório High Ticket</strong>. "
    "Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# NORMALIZAÇÃO DE CHAVE
# -----------------------------
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# -----------------------------
# LEITURA DE ARQUIVOS PDF
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def read_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

# Carrega transcrições e PDFs
_raw_txt  = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "5.8 - Dossiê 007 - (3)[1].pdf"))
_raw_pdf4 = read_pdf(os.path.join(BASE_DIR, "Papelaria e brindes  lista de links e indicações.pdf"))

# -----------------------------
# PALAVRAS-CHAVE PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "retorno do investimento", "canva"],
    "capitacao_sem_marketing_digital": ["offline", "sem instagram", "sem anúncios", "sem redes sociais"],
    "aplicacao":                      ["como aplico", "aplicação", "roteiro"],
    "faq":                            ["quais", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  ["plano de ação", "primeira semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"],
    "dossie":                         ["dossiê 007", "acao 1", "acao 2", "acao 3", "orientações finais"],
    "papelaria":                      ["jo malone", "importadoras", "cafeteiras", "chocolates", "chás"],
    "playlist":                       ["playlist", "spotify"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS
# -----------------------------
CANONICAL_QA = {
    # — Health Plan (Canva) —
    "onde encontro o link do formulario para criar no canva o health plan personalizado para o paciente":
        "Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link ativo: "
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?"
        "utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview\" target=\"_blank\">"
        "Formulário Health Plan (Canva)</a>. "
        "Ele também está disponível diretamente na Aula 10.4 do curso Consultório High Ticket.",

    # — Captação sem redes sociais —
    "e possivel atrair pacientes sem usar redes sociais":
        "Sim! Um dos pilares do curso Consultório High Ticket é justamente mostrar que "
        "é possível atrair pacientes fiéis e de alto valor sem depender de redes sociais. "
        "A Nanda ensina estratégias presenciais, indicações qualificadas, posicionamento de autoridade "
        "e um método validado que funciona offline, baseado em relacionamento e experiência. "
        "Você aprenderá tudo isso nas aulas, especialmente nas que tratam de captação sem marketing digital.",

    # — Comunidade —
    "como entro na comunidade high ticket":
        "A Comunidade High Ticket Doctors está dentro da plataforma do curso. Assim que você receber "
        "o e-mail com o título “Chegou seu acesso”, cadastre sua senha. Depois de logado, preencha seu perfil "
        "e entre na Comunidade para tirar dúvidas sobre o método, fazer networking e participar das oficinas.",

    # — Suporte urgente —
    "se eu tiver um problema urgente durante o curso como solicito suporte rapidamente":
        "Em caso de urgência no curso, envie um e-mail para **ajuda@nandamac.com** com o assunto “S.O.S Crise” "
        "para receber suporte em até 24 h úteis.",

    # — Dúvidas metodológicas —
    "onde devo postar minhas duvidas sobre o metodo do curso":
        "Todas as dúvidas metodológicas devem ser postadas exclusivamente na Comunidade da Área de Membros. "
        "Não use Direct, WhatsApp ou outros canais para questionar o método; assim sua pergunta fica visível "
        "a todos e recebe resposta mais rápida.",

    # — Plano de Ação (1ª Semana) —
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino minha atitude dia do chega":
        "Identifique qual sentimento de culpa ao cobrar mais te afeta (a “Síndrome do Sacerdote”) e coloque-o como bloqueio prioritário. "
        "Em ‘Onde quero chegar’, escreva uma ação concreta, por exemplo: “A partir de hoje, afirmarei meu valor em cada consulta.”",

    "na parte de autoconfianca profissional o que devo escrever como atitude para nao deixar certas situacoes me abalar":
        "Liste duas experiências que minaram sua confiança. "
        "Em ‘Onde quero chegar’, defina uma ação transformadora, por exemplo: “Sempre que receber uma crítica, realizarei uma sessão de feedback construtivo com um colega.”",

    "como uso a atividade de nicho de atuacao para definir meu foco e listar as acoes necessarias":
        "Posicionamento Atual: descreva seus pontos fortes e lacunas. "
        "Nicho Ideal: defina quem são seus “pacientes-sonho”. "
        "Ações: liste etapas específicas com prazo, por exemplo: “Especializar em [X] em 3 meses.”, “Criar pacote online de avaliação inicial até o próximo mês.”, “Revisar site e materiais de comunicação em 2 semanas.”",

    "no valor da consulta e procedimentos como encontro referencias de mercado e defino meus valores atuais e ideais":
        "Anote seus preços atuais e pesquise médias de associações ou colegas. "
        "Defina seus valores ideais justificando seu diferencial, por exemplo: “R$ 300 por sessão de fisioterapia clínica, pois ofereço acompanhamento personalizado e relatório de progresso.”",

    "ainda nao tenho pacientes particulares qual estrategia de atracao high ticket devo priorizar e como executar na agenda":
        "Reserve um bloco fixo na agenda (ex.: toda segunda, das 8h–10h) para:\n"
        "1. Enviar 5 mensagens personalizadas a potenciais pacientes do seu nicho, usando o script do curso.\n"
        "2. Após iniciar atendimentos, implemente a Patient Letter: envie um convite impresso com seu nome, valor e benefícios, para reforçar o contato.",

    # — Papelaria & Brindes —
    "onde encontro produtos jo malone no brasil":
        "Você pode encontrar os aromas de ambiente Jo Malone no Brasil diretamente no site oficial:\n"
        "https://www.jomalone.com.br\n"
        "Lá estão disponíveis colônias como Blackberry & Bay, Wood Sage & Sea Salt, Lime Basil & Mandarin e Nectarine Blossom & Honey, além de velas e sabonetes.",

    "quais importadoras posso usar para comprar produtos que nao encontro no brasil":
        "Para produtos que não são facilmente encontrados aqui, você pode recorrer a importadoras como:\n"
        "• Easy to go Orlando: https://easytogoorlando.com/\n"
        "Ou fazer pedidos em grandes marketplaces internacionais, como a Amazon.",

    "quais marcas de cafeteiras foram mencionadas na aula":
        "As marcas de cafeteiras recomendadas durante o módulo são:\n"
        "• Delonghi\n"
        "• Nespresso\n"
        "• Breville",

    "onde posso comprar os chocolates indicados no curso":
        "Os chocolates mencionados foram:\n"
        "• Läderach\n"
        "• Daim\n"
        "Você os encontra em chocolaterias especializadas ou através de lojas online/importadoras.",

    "quais opcoes de chas foram indicadas no material":
        "Foram indicados dois tipos de chá:\n"
        "• New English Teas Vintage Victorian Round Tea Caddy\n"
        "• Twinings Earl Grey Loose Tea Tins",

    # — Playlist Spotify —
    "onde posso acessar a playlist do consultorio high ticket":
        "Você pode ouvir nossa playlist oficial diretamente no Spotify: "
        "<a href=\"https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?"  
        "si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80\" target=\"_blank\">"
        "Playlist Consultório High Ticket (Spotify)</a>",

    "qual e o link da playlist recomendada na aula 4 17 do modulo 4":
        "Na aula 4.17 do Módulo 4 – A Jornada do Paciente High Ticket, indicamos esta playlist: "
        "<a href=\"https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?"
        "si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80\" target=\"_blank\">"
        "Playlist Consultório High Ticket (Spotify)</a>",

    "como eu ouco a playlist do curso consultorio high ticket":
        "Basta abrir o link da playlist no app ou site do Spotify e clicar em “Play”. Está disponível em: "
        "<a href=\"https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?"
        "si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80\" target=\"_blank\">"
        "Playlist Consultório High Ticket (Spotify)</a>",

    "em que aula e mencionada a playlist do consultorio high ticket":
        "Falamos da playlist na Aula 4.17 do Módulo 4 – A Jornada do Paciente High Ticket. "
        "<a href=\"https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?"
        "si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80\" target=\"_blank\">"
        "Playlist Consultório High Ticket (Spotify)</a>",

    "como encontro a playlist do consultorio high ticket no spotify":
        "Procure por “Consultório High Ticket” no Spotify ou acesse diretamente por este link: "
        "<a href=\"https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?"
        "si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80\" target=\"_blank\">"
        "Playlist Consultório High Ticket (Spotify)</a>",

    # — SCRIPTS DA SECRETÁRIA – CONSULTÓRIO HIGH TICKET —
    "como mensurar o impacto do desconto concedido a pacientes antigos na fidelizacao e no faturamento do consultorio":
        "Para mensurar o impacto do desconto concedido a pacientes antigos na fidelização e no faturamento do consultório, siga estas etapas:\n\n"
        "1. Defina métricas-chave:\n"
        "- Retenção de pacientes: percentual de pacientes antigos que retornam após o desconto.\n"
        "- Ticket médio: valor médio faturado por paciente antes e depois da promoção.\n"
        "- Lifetime Value (LTV): projeção de receita trazida por esses pacientes ao longo de meses.\n\n"
        "2. Colete dados: registre em planilha ou sistema de gestão cada desconto aplicado (paciente, data, valor).\n\n"
        "3. Compare períodos: avalie as métricas nos 3–6 meses antes do desconto vs. 3–6 meses depois.\n\n"
        "4. Analise qualitativamente: aplique pesquisa de satisfação aos pacientes contemplados para entender percepção de valor.\n\n"
        "5. Ajuste a política: se o desconto aumentar retorno sem corroer margem, mantenha; caso contrário, redefina critérios ou patamares de desconto.",

    "quais criterios a secretaria deve usar para decidir quando colocar um novo paciente na lista de espera versus sugerir outra data":
        "A secretária deve considerar os seguintes critérios:\n\n"
        "1. Urgência clínica: priorize casos com dor aguda ou necessidade imediata.\n"
        "2. Perfil do paciente:\n"
        "- Pacientes antigos: lista de espera exclusiva com retorno em até 24 h.\n"
        "- Pacientes novos: avalie flexibilidade de agenda e informe prazo realista.\n"
        "3. Janela de disponibilidade:\n"
        "- Se puder em até 48 h, ofereça lista de espera;\n"
        "- Caso contrário, sugira próxima data fixa confirmada.\n"
        "4. Comunicação clara: informe prazo máximo de resposta (até 24 h) e confirme presença.\n"
        "5. Confirmação de compromisso: inclua na lista somente se o paciente aceitar as condições.",

    "na pratica como aplicar a tecnica de espelhamento com pacientes dificieis sem parecer artificial ou forcado":
        "Para aplicar espelhamento com naturalidade:\n\n"
        "1. Ouça ativamente e identifique palavras-chave usadas pelo paciente.\n"
        "2. Repita trechos curtos:\n"
        "- Paciente: “Estou com muita ansiedade antes do tratamento.”\n"
        "- Você: “Ansiedade antes do tratamento?”\n"
        "3. Use tom calmo e pausado para demonstrar empatia.\n"
        "4. Combine com perguntas abertas: “E o que mais você sente em relação a isso?”\n"
        "5. Seja genuíno: espelhe apenas o que realmente captar, evitando frases decoradas.",

    "quais sao os cuidados para elaborar o lembrete de consulta dois dias antes de forma clara e profissional sem ser invasivo":
        "Cuidados para lembrete de consulta 2 dias antes:\n\n"
        "1. Mensagem personalizada: inclua nome do paciente e do profissional.\n"
        "2. Dados essenciais: dia da semana, data e horário exatos.\n"
        "3. Tom cordial e breve:\n"
        "   Ex: “Tudo certo para nossa consulta na terça-feira, 12/05, às 14 h?”\n"
        "4. Ofereça opção de reagendar: “Se precisar alterar, responda esta mensagem.”\n"
        "5. Evite excesso de texto: 2–3 frases.\n"
        "6. Canal apropriado: SMS ou WhatsApp em horário hábil.",

    "como registrar e acompanhar faltas sem aviso para minimizar o numero de noshows e manter um relacionamento positivo com o paciente":
        "Para registrar e acompanhar faltas sem aviso:\n\n"
        "1. Protocolo de registro: anote data e horário do no-show no sistema imediatamente.\n"
        "2. Follow-up no mesmo dia com mensagem empática:\n"
        "   “Olá [Nome], sentimos sua falta hoje. Está tudo bem?”\n"
        "3. Classificação de risco: identifique pacientes com faltas recorrentes para contato telefônico.\n"
        "4. Ofereça reagendamento: sugira duas opções de data no follow-up.\n"
        "5. Analise padrões: gere relatório mensal de faltas para identificar tendências.\n"
        "6. Ajuste lembretes: se faltar após SMS, inclua lembrete extra por WhatsApp horas antes.",


    # — Correções de Perguntas Não Respondidas —
    "como estruturar o primeiro contato do paciente via direct ou mensagem para garantir empatia e direcionarlo corretamente":
        "Saudação personalizada: use o nome do paciente e mencione a conexão com a Nanda ("Oie, sou amiga da Nanda...").\n"
        "Tom caloroso e de autoridade: demonstre entusiasmo ("vai ser um prazer te atender!").\n"
        "Chamada à ação clara: envie o link para agendamento com a assistente ("clique neste link para marcar com a Ana").\n"
        "Detalhes técnicos: oriente sobre o formato do link (55=país, 21=área) para evitar erros.\n"
        "Toque de relacionamento: encerre com uma menção informal e simpática ("Manda um beijão para ela!").",

    "o que dizer quando o paciente quer alternativas de tratamento sem marcar nova consulta":
        "Reconhecimento da solicitação: “Entendo que você queira alternativas...”\n"
        "Explicação técnica: informe que “por foto não dá para reavaliar a pele com segurança”.\n"
        "Justificativa de valor: reforce a importância da avaliação presencial para qualidade do tratamento.\n"
        "Próximo passo claro: “Vamos agendar uma consulta e eu apresento todas as opções.”\n"
        "Gatilho de urgência suave: “Assim podemos iniciar o melhor protocolo para você o quanto antes.”",

    "como responder a objecao achei caro seguindo o script high ticket":
        "Espelhamento suave: “Você sentiu que o investimento está acima do esperado?”\n"
        "Reforço de valor: aponte benefícios tangíveis (“Este protocolo inclui X procedimentos exclusivos…”).\n"
        "Comparação de custo-benefício: “Em quanto tempo você espera ver o resultado? Nosso método costuma gerar retorno em Y meses.”\n"
        "Pergunta exploratória: “O que achou mais relevante na proposta até agora?”\n"
        "Oferta de opções: “Posso parcelar no Pix em até 3x, se ajudar no seu planejamento.”",
}

# Pré-normaliza chaves
CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo "
    "do curso <strong>Consultório High Ticket</strong>. Responda como uma professora experiente, "
    "ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. "
        "Use uma linguagem clara e didática, com tópicos ou passos. Evite genéricos.<br><br>"
    ),
    "faq": (
        "<strong>Objetivo:</strong> Responder de forma direta a dúvidas frequentes do curso. "
        "Use exemplos práticos e mencione etapas conforme o material."
    )
}

# -----------------------------
# CLASSIFICADOR
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if lower in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# GERADOR DE RESPOSTA
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)

    # 1) Resposta canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) Classifica escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) Monta prompt dinâmico
    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += (
        f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br>"
        f"<strong>🧠 Resposta:</strong><br>"
    )

    # 4) Chama OpenAI com fallback
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
    return r.choices[0].message.content
