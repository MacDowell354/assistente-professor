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
    "Olá, Profissional da Saúde, seja muito bem-vindo(a)!",
    "Oi, Profissional da Saúde, tudo bem? Como posso ajudar?",
    "Bem-vindo(a) de volta! Pronto(a) para evoluir no consultório?",
    "Olá! Estou aqui para apoiar você na sua evolução como profissional da saúde."
]

CLOSINGS = [
    "Se quiser um exemplo prático ou modelo, clique nos botões abaixo.",
    "Tem outro desafio no seu consultório? Me conte ou clique em Novo Tema.",
    "Se quiser aprofundar, escolha uma opção rápida ou pergunte de novo!",
    "Quer mudar de assunto? Só digitar ‘novo tema’.",
    "Essa resposta te ajudou? Clique em 👍 ou 👎."
]

# BLOCO DE MÓDULOS (exatamente igual ao seu, só para busca e referência)
BLOCO_MODULOS = """
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

def gerar_quick_replies(question, explicacao, history=None):
    return [
        "Quero um exemplo prático",
        "Me explique passo a passo",
        "Tenho uma dúvida sobre esse tema"
    ]

def resposta_link(titulo, url, icone="📄"):
    return f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"

def resposta_link_externo(titulo, url, icone="🔗"):
    return f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"

def detectar_cenario(pergunta: str) -> str:
    pergunta = pergunta.lower()
    if any(p in pergunta for p in ["quero fazer o curso completo", "começar do início", "me ensina tudo", "fazer o curso com você"]):
        return "curso_completo"
    elif any(p in pergunta for p in ["quero começar pelo módulo", "me mostra o módulo", "ver o módulo", "começar módulo"]):
        return "modulo_especifico"
    elif any(p in pergunta for p in ["assisti", "já vi a aula", "tenho uma dúvida", "não entendi", "poderia explicar melhor"]):
        return "duvida_pontual"
    elif any(p in pergunta for p in ["exemplo prático", "me dá um exemplo", "passo a passo", "como fazer isso"]):
        return "exemplo_pratico"
    else:
        return "geral"

def atualizar_progresso(pergunta: str, progresso: dict) -> dict:
    if not progresso:
        return {'modulo': 1, 'aula': '1.1', 'etapa': 1, 'aguardando_duvida': False}
    if progresso.get('aguardando_duvida'):
        if pergunta.lower().strip() in ["não", "nao", "não tenho dúvida", "nao tenho duvida", "pode avançar", "avançar", "continuar"]:
            progresso['aguardando_duvida'] = False
            modulo = progresso['modulo']
            num_atual = float(progresso['aula'])
            num_proxima = round(num_atual + 0.1, 1)
            progresso['aula'] = f"{modulo}.{int(num_proxima * 10) % 10}"
            progresso['etapa'] = 1
        # Se disser "sim" ou perguntar, a IA continua na mesma aula, mesma etapa
    elif pergunta.lower().strip() in ["sim", "sim desejo", "quero sim", "vamos", "ok"]:
        if progresso['etapa'] == 1:
            progresso['etapa'] = 2
        elif progresso['etapa'] == 2:
            progresso['etapa'] = 3
        else:
            progresso['aguardando_duvida'] = True
    return progresso

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    # RECUPERA PROGRESSO DO HISTÓRICO
    if history and isinstance(history, list) and len(history) > 0:
        ultimo_item = history[-1]
        progresso = ultimo_item.get('progresso', None)
        if not progresso:
            progresso = {'modulo': 1, 'aula': '1.1', 'etapa': 1, 'aguardando_duvida': False}
    else:
        progresso = {'modulo': 1, 'aula': '1.1', 'etapa': 1, 'aguardando_duvida': False}

    progresso = atualizar_progresso(question, progresso)
    modulo = progresso.get('modulo', 1)
    aula = progresso.get('aula', '1.1')
    etapa = progresso.get('etapa', 1)
    aguardando_duvida = progresso.get('aguardando_duvida', False)

    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)
    cenario = detectar_cenario(question)

    if cenario == "curso_completo":
        explicacao = (
            f"{saudacao}<br><br>"
            "O curso Consultório High Ticket é composto por 7 módulos, cada um trazendo competências-chave para o crescimento do seu consultório e sua carreira como profissional da saúde.<br><br>"
            "<b>Confira os módulos:</b><br>"
            "<b>Módulo 01 – mentalidade high ticket: como desenvolver uma mente preparada para atrair pacientes high ticket</b><br>"
            "<b>Módulo 02 – senso estético high ticket: como transformar sua imagem e ambiente para atrair pacientes que valorizam</b><br>"
            "<b>Módulo 03 – posicionamento presencial high ticket: como construir autoridade sem redes sociais</b><br>"
            "<b>Módulo 04 – a jornada do paciente high ticket: como transformar atendimento em encantamento e fidelização</b><br>"
            "<b>Módulo 05 – estratégias de captação e fidelização: como atrair pacientes high ticket sem tráfego ou redes sociais</b><br>"
            "<b>Módulo 06 – estratégias de vendas high ticket: como apresentar e fechar tratamentos de alto valor com ética</b><br>"
            "<b>Módulo 07 – estratégias por especialidade</b><br><br>"
            "Vamos começar pelo módulo 01?<br><br>"
            "<b>Aulas do módulo 01:</b><br>"
            "1.1. introdução – a mentalidade do especialista high ticket: o primeiro passo para dobrar o faturamento do consultório<br>"
            "1.2. como quebrar bloqueios com dinheiro e valorizar seu trabalho no consultório high ticket<br>"
            "1.3. como desenvolver autoconfiança profissional e se tornar autoridade no consultório high ticket<br>"
            "1.4. concorrência: como se diferenciar e construir valorização profissional<br>"
            "1.5. boas práticas no atendimento: o caminho mais rápido para o consultório high ticket<br><br>"
            "Deseja iniciar agora a aula 1.1? (Responda 'sim' para começar ou escolha outro módulo.)"
        )
        quick_replies = gerar_quick_replies(question, explicacao, history)
        return explicacao, quick_replies, progresso

    # Aguardando dúvida de aula antes de avançar
    if aguardando_duvida:
        explicacao = (
            "Antes de concluir esta aula, ficou alguma dúvida sobre o conteúdo apresentado? "
            "Se precisar de explicação adicional, é só perguntar! "
            "Se estiver tudo claro, responda 'não' para avançarmos para a próxima aula."
        )
        quick_replies = gerar_quick_replies(question, explicacao, history)
        return explicacao, quick_replies, progresso

    # Fluxo padrão para as aulas
    if etapa == 1:
        instruction = f"Você está iniciando a aula {aula} do módulo {modulo}. Apresente o objetivo da aula, de forma didática e acolhedora, usando SEMPRE o título da aula exatamente como está no bloco oficial, e tratando o usuário como profissional da saúde."
    elif etapa == 2:
        instruction = f"Você está na parte intermediária da aula {aula} do módulo {modulo}. Aprofunde o conteúdo com exemplos práticos, aplicações clínicas e orientações detalhadas para profissionais da saúde. Use o título da aula exatamente como está no bloco oficial."
    else:
        instruction = (
            f"Você está concluindo a aula {aula} do módulo {modulo}. Recapitule os principais aprendizados de forma sucinta. "
            "Pergunte se ficou alguma dúvida ou se o profissional da saúde quer uma explicação extra ANTES de considerar a aula concluída. "
            "Só avance para a próxima aula se o aluno responder 'não'."
        )
        progresso['aguardando_duvida'] = True

    prompt = f"""{instruction}

Você é a professora Nanda Mac.ia, uma inteligência artificial altamente didática, criada especificamente para ensinar e tirar dúvidas de profissionais da saúde que estudam o Curso Online Consultório High Ticket, ministrado por Nanda Mac Dowell.

Leia atentamente o histórico da conversa antes de responder, compreendendo o contexto exato da interação atual para garantir precisão na sua resposta.

IMPORTANTE: Sempre cite o nome do módulo e título da aula exatamente como está na estrutura abaixo. Não adapte, não resuma, não traduza.

ESTRUTURA COMPLETA DO CURSO – MÓDULOS E AULAS:

{BLOCO_MODULOS}

Histórico da conversa anterior:
{history}

Pergunta atual do profissional da saúde:
'{question}'

Utilize o conteúdo adicional abaixo, se relevante:
{context}
    """

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

    if saudacao:
        resposta = f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"
    else:
        resposta = f"{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies, progresso
