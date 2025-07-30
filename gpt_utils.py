import os
import re
import random
from openai import OpenAI, OpenAIError

TRANSCRIPTS_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")
client = OpenAI()

OUT_OF_SCOPE_MSG = (
    "Desculpe, ainda não tenho informações suficientes sobre esse tema específico do curso. "
    "Por favor, envie outra pergunta ou consulte o material da aula."
)

GREETINGS = [
    "Olá, Doutor(a), seja muito bem-vindo(a)!",
    "Oi, Doutor(a), tudo bem? Como posso ajudar?",
    "Bem-vindo(a) de volta, Doutor(a)! Pronto(a) para evoluir seu consultório?",
    "Olá, Doutor(a)! Estou aqui para apoiar você no seu crescimento."
]

CLOSINGS = [
    "Ficou com alguma dúvida sobre esta aula, Doutor(a)?",
    "Deseja aprofundar algum ponto, seguir para a próxima aula, voltar, repetir ou escolher outro módulo?",
    "Se quiser, escolha uma opção rápida abaixo ou pergunte de novo!",
    "Se quiser ir para outra aula, módulo ou tema, é só pedir, Doutor(a).",
    "Essa resposta foi útil? Clique em 👍 ou 👎."
]

AULAS_POR_MODULO = {
    0: ['0.1'],
    1: ['1.1', '1.2', '1.3', '1.4', '1.5'],
    2: ['2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9'],
    3: ['3.1', '3.2', '3.3', '3.4', '3.5'],
    4: ['4.1', '4.2', '4.3', '4.4', '4.5'],
    5: ['5.1', '5.2', '5.3', '5.4', '5.5'],
    6: ['6.1', '6.2', '6.3', '6.4', '6.5'],
    7: ['7.1', '7.2', '7.3', '7.4', '7.5', '7.6', '7.7', '7.8', '7.9'],
}

def gerar_quick_replies(question, explicacao, history=None, progresso=None, contexto_extra=False):
    opcoes = []
    if contexto_extra:
        opcoes = [
            "Começar pelo módulo 00 (introdução)",
            "Quero iniciar o curso do início",
            "Ir para o menu do curso",
            "Ir para a aula 7.1 sobre Health Plan",
            "Tenho outra dúvida"
        ]
    else:
        opcoes = ["Aprofundar esta aula", "Próxima aula", "Tenho outra dúvida"]
        if progresso:
            modulo = progresso.get('modulo', 0)
            opcoes.append("Voltar para aula anterior")
            opcoes.append("Repetir esta aula")
            opcoes.append("Escolher módulo ou aula específica")
            if modulo < 7:
                opcoes.append("Ir para o próximo módulo")
            if modulo > 0:
                opcoes.append("Ir para o módulo anterior")
    return opcoes

def resposta_link(titulo, url, icone="📄"):
    return f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"

def resposta_link_externo(titulo, url, icone="🔗"):
    return f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"

def detectar_cenario(pergunta: str) -> str:
    pergunta = pergunta.lower()
    if any(p in pergunta for p in ["quero fazer o curso completo", "começar do início", "me ensina tudo", "fazer o curso com você", "menu", "ver módulos", "ver o curso", "ver estrutura"]):
        return "curso_completo"
    elif re.search(r'\bm[oó]dulo\s*\d+\b', pergunta) or re.search(r'\baula\s*\d+\.\d+\b', pergunta):
        return "navegacao_especifica"
    elif any(p in pergunta for p in ["voltar", "retornar", "anterior", "repetir aula"]):
        return "voltar"
    elif any(p in pergunta for p in ["tenho uma dúvida", "tenho outra dúvida", "minha dúvida", "não entendi", "duvida", "dúvida", "me explica", "poderia explicar", "por que", "como", "o que", "quais", "qual", "explique", "me fale", "exemplo", "caso prático", "me mostre", "me explique", "?"]):
        return "duvida_pontual"
    elif any(p in pergunta for p in ["exemplo prático", "me dá um exemplo", "passo a passo", "como fazer isso", "como faço", "me ensina", "ensinar", "me mostre como"]):
        return "exemplo_pratico"
    else:
        return "geral"

def encontrar_modulo_aula(pergunta):
    pergunta = pergunta.lower()
    m_modulo = re.search(r'\bm[oó]dulo\s*(\d+)\b', pergunta)
    m_aula = re.search(r'\baula\s*(\d+\.\d+)\b', pergunta)
    modulo = None
    aula = None
    if m_modulo:
        modulo = int(m_modulo.group(1))
    if m_aula:
        aula = m_aula.group(1)
    return modulo, aula

def atualizar_progresso(pergunta: str, progresso: dict) -> dict:
    if not progresso:
        return {'modulo': 0, 'aula': '0.1', 'etapa': 1, 'aguardando_duvida': False, 'visao_geral': True}

    pergunta_lower = pergunta.strip().lower()
    modulo_nav, aula_nav = encontrar_modulo_aula(pergunta)
    if modulo_nav is not None and modulo_nav in AULAS_POR_MODULO:
        progresso['modulo'] = modulo_nav
        if aula_nav and aula_nav in AULAS_POR_MODULO.get(modulo_nav, []):
            progresso['aula'] = aula_nav
        else:
            progresso['aula'] = AULAS_POR_MODULO[modulo_nav][0]
        progresso['etapa'] = 1
        progresso['visao_geral'] = False
        progresso['aguardando_duvida'] = False
        return progresso
    elif aula_nav:
        for m, aulas in AULAS_POR_MODULO.items():
            if aula_nav in aulas:
                progresso['modulo'] = m
                progresso['aula'] = aula_nav
                progresso['etapa'] = 1
                progresso['visao_geral'] = False
                progresso['aguardando_duvida'] = False
                return progresso

    if any(p in pergunta_lower for p in ["voltar", "retornar", "anterior"]):
        modulo = progresso['modulo']
        aula_atual = progresso['aula']
        aulas = AULAS_POR_MODULO.get(modulo, [])
        idx = aulas.index(aula_atual) if aula_atual in aulas else 0
        if idx > 0:
            progresso['aula'] = aulas[idx-1]
            progresso['etapa'] = 1
        else:
            if modulo > 0:
                progresso['modulo'] = modulo - 1
                progresso['aula'] = AULAS_POR_MODULO[modulo-1][-1]
                progresso['etapa'] = 1
        progresso['visao_geral'] = False
        progresso['aguardando_duvida'] = False
        return progresso

    if "repetir" in pergunta_lower:
        progresso['etapa'] = 1
        progresso['aguardando_duvida'] = False
        progresso['visao_geral'] = False
        return progresso

    if any(p in pergunta_lower for p in ["próxima aula", "avançar", "continuar", "pode avançar"]):
        modulo = progresso['modulo']
        aula_atual = progresso['aula']
        aulas = AULAS_POR_MODULO.get(modulo, [])
        idx = aulas.index(aula_atual) if aula_atual in aulas else 0
        if idx < len(aulas)-1:
            progresso['aula'] = aulas[idx+1]
            progresso['etapa'] = 1
        else:
            if modulo < 7:
                progresso['modulo'] = modulo + 1
                progresso['aula'] = AULAS_POR_MODULO[modulo+1][0]
                progresso['etapa'] = 1
        progresso['visao_geral'] = False
        progresso['aguardando_duvida'] = False
        return progresso

    if pergunta_lower in ["sim", "sim desejo", "quero sim", "vamos", "ok"]:
        if progresso.get('visao_geral', False):
            progresso['visao_geral'] = False
            progresso['modulo'] = 0
            progresso['aula'] = '0.1'
            progresso['etapa'] = 1
        elif progresso.get('etapa', 1) < 3:
            progresso['etapa'] += 1
        else:
            progresso['aguardando_duvida'] = True
    elif pergunta_lower in ["não", "nao", "não tenho dúvida", "nao tenho duvida"]:
        if progresso.get('aguardando_duvida'):
            progresso['aguardando_duvida'] = False
            modulo = progresso['modulo']
            aula_atual = progresso['aula']
            aulas = AULAS_POR_MODULO.get(modulo, [])
            idx = aulas.index(aula_atual) if aula_atual in aulas else 0
            if idx < len(aulas)-1:
                progresso['aula'] = aulas[idx+1]
            else:
                if modulo < 7:
                    progresso['modulo'] = modulo + 1
                    progresso['aula'] = AULAS_POR_MODULO[modulo+1][0]
            progresso['etapa'] = 1
            progresso['visao_geral'] = False
    return progresso

# BLOCO DE MÓDULOS E AULAS (com MÓDULO 00)
BLOCO_MODULOS = """
módulo 00 (módulo 0) – COMECE POR AQUI
0.1. boas-vindas, mentalidade, postura, organização, networking, plantão de dúvidas, desafio dos supercomprometidos, regras do curso

módulo 01 – mentalidade high ticket: como desenvolver uma mente preparada para atrair pacientes high ticket
1.1. introdução – a mentalidade do especialista high ticket: o primeiro passo para dobrar o faturamento do consultório
1.2. como quebrar bloqueios com dinheiro e valorizar seu trabalho no consultório high ticket
1.3. como desenvolver autoconfiança profissional e se tornar autoridade no consultório high ticket
1.4. concorrência: como se diferenciar e construir valorização profissional
1.5. boas práticas no atendimento: o caminho mais rápido para o consultório high ticket

módulo 02 – senso estético high ticket: como transformar sua imagem e ambiente para atrair pacientes que valorizam
2.1. o senso estético high ticket
2.2. mulheres: senso estético high ticket x cafona
2.3. homens no consultório high ticket: senso estético, imagem e escolhas que atraem ou afastam pacientes
2.4. senso estético high ticket na decoração: o que priorizar e o que evitar no consultório
2.5. papelaria e brindes
2.6. como fazer o paciente se sentir especial e gerar mais valor na percepção dele
2.7. checklist: o que você precisa mudar hoje no seu consultório para dobrar o faturamento com o senso estético
2.8. como tornar a primeira impressão do paciente inesquecível
2.9. o que é cafona no consultório e afasta paciente high ticket

módulo 03 – posicionamento presencial high ticket: como construir autoridade sem redes sociais
3.1. posicionamento presencial high ticket: estratégias para construir autoridade e valor no consultório
3.2. você é um cnpj: riscos, proteção jurídica e postura profissional no consultório high ticket
3.3. como causar uma boa primeira impressão no consultório high ticket
3.4. como causar uma boa impressão pessoal no consultório high ticket: educação, pontualidade e respeito
3.5. posicionamento em eventos sociais e exposição na mídia: comportamento e limites para fortalecer sua autoridade e atrair pacientes high ticket

módulo 04 – a jornada do paciente high ticket: como transformar atendimento em encantamento e fidelização
4.1. a jornada do paciente high ticket: conceito e regras de ouro para o consultório
4.2. o que o paciente nunca te falará: detalhes essenciais para encantar pacientes high ticket
4.3. secretária e assistente virtual high ticket: funções, riscos e boas práticas para consultórios lucrativos
4.4. o primeiro contato: como organizar e profissionalizar a marcação de consultas desde o início
4.5. marcação de consulta high ticket: como organizar horários, valor e scripts para reduzir faltas e valorizar seu atendimento

módulo 05 – estratégias de captação e fidelização: como atrair pacientes high ticket sem tráfego ou redes sociais
5.1. passo a passo completo para atrair e reter pacientes high ticket com o método consultório high ticket
5.2. o impacto do lifetime value do paciente high ticket no crescimento do consultório
5.3. como nichar o consultório para atrair pacientes high ticket
5.4. estratégias práticas de networking para atração de pacientes high ticket
5.5. estratégias para atrair pacientes high ticket ao começar do absoluto zero

módulo 06 – estratégias de vendas high ticket: como apresentar e fechar tratamentos de alto valor com ética
6.1. os passos fundamentais para dobrar o faturamento do consultório com vendas high ticket
6.2. como migrar dos convênios para o atendimento particular de forma segura e organizada
6.3. como aumentar o valor da sua consulta de forma estratégica e segura
6.4. como e quando dar descontos para pacientes high ticket: estratégia ética e eficaz
6.5. técnica alanis – como usar apresentação visual para vencer objeções e fechar tratamentos high ticket

módulo 07 – estratégias por especialidade
7.1. saúde das crianças – estratégias para consultórios pediátricos high ticket
7.2. saúde feminina – estratégias high ticket para ginecologia, obstetrícia e saúde da mulher
7.3. saúde do idoso – estratégias high ticket para geriatria e atenção ao idoso
7.4. cirurgiões – como apresentar valor, orçamento e experiência high ticket
7.5. doenças sérias – como conduzir pacientes em situações críticas no consultório high ticket
7.6. profissionais com atendimento misto – estratégias para consultórios com diferentes públicos
7.7. profissionais com baixa rotatividade – estratégias para retorno e fidelização
7.8. profissionais da estética – estratégias para consultórios estéticos e de autocuidado
7.9. nutricionistas – estratégias high ticket para emagrecimento, nutrologia e endocrinologia
"""

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    if history and isinstance(history, list) and len(history) > 0:
        ultimo_item = history[-1]
        progresso = ultimo_item.get('progresso', None)
        if not progresso:
            progresso = {'modulo': 0, 'aula': '0.1', 'etapa': 1, 'aguardando_duvida': False, 'visao_geral': True}
    else:
        progresso = {'modulo': 0, 'aula': '0.1', 'etapa': 1, 'aguardando_duvida': False, 'visao_geral': True}

    progresso = atualizar_progresso(question, progresso)
    modulo = progresso.get('modulo', 0)
    aula = progresso.get('aula', '0.1')
    etapa = progresso.get('etapa', 1)
    aguardando_duvida = progresso.get('aguardando_duvida', False)
    visao_geral = progresso.get('visao_geral', False)

    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)
    cenario = detectar_cenario(question)

    mensagem_generica = question.strip().lower()
    saudacoes_vagas = [
        "olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "pode me ajudar?", "oi, tudo bem?",
        "olá bom dia", "tudo bem?", "tudo certo?", "como vai?", "você pode me ajudar?", "me ajuda?", "olá, boa noite"
    ]
    apresentacoes_vagas = ["meu nome é
