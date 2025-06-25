import os
from openai import OpenAI, OpenAIError

# -----------------------------
# CONFIGURAÇÃO DE AMBIENTE
# -----------------------------
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError('❌ Variável de ambiente OPENAI_API_KEY não encontrada.')

client = OpenAI(api_key=api_key)

# -----------------------------
# MENSAGEM PADRÃO PARA FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    'Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso '
    'Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>'
    'Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. '
    'Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório.'
)

# -----------------------------
# CARREGA E RESUME TRANSCRIÇÕES (1× NO STARTUP)
# -----------------------------
TRANSCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'transcricoes.txt')
_raw = open(TRANSCRIPT_PATH, encoding='utf-8').read()
try:
    res = client.chat.completions.create(
        model='gpt-4',
        messages=[
            {'role': 'system', 'content': (
                'Você é um resumidor especialista em educação. Resuma em até 300 palavras o conteúdo do curso '
                '“Consultório High Ticket”, para servir de base para classificação de escopo.')},
            {'role': 'user', 'content': _raw}
        ]
    )
    COURSE_SUMMARY = res.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ''  # Se falhar, evita bloquear o fluxo

# -----------------------------
# CLASSIFICADOR DE ESCOPO
# -----------------------------
def is_in_scope(question: str) -> bool:
    '''Retorna True se a pergunta estiver dentro do escopo do curso.'''
    try:
        resp = client.chat.completions.create(
            model='gpt-4',
            messages=[
                {'role': 'system', 'content': (
                    'Você é um classificador de escopo. Com base neste resumo de curso, responda apenas IN_SCOPE ou OUT_OF_SCOPE:')},
                {'role': 'user', 'content': f'Resumo do curso:\n{COURSE_SUMMARY}\n\nPergunta:\n{question}'}
            ]
        )
        label = resp.choices[0].message.content.strip().upper()
        return label == 'IN_SCOPE'
    except OpenAIError:
        return False

# -----------------------------
# LÓGICA DE GERAÇÃO DE RESPOSTA
# -----------------------------

def generate_answer(
    question: str,
    context: str = '',
    history: str = None,
    tipo_de_prompt: str = 'explicacao'
) -> str:
    # 1) Classificação de escopo automática
    if not is_in_scope(question):
        return OUT_OF_SCOPE_MSG

    # 2) Detecção de captação offline
    termos_offline = ['sem usar instagram', 'sem instagram', 'sem anúncios', 'sem anuncios', 'offline']
    if any(term in question.lower() for term in termos_offline):
        tipo_de_prompt = 'capitacao_sem_marketing_digital'

    # 3) Detecção de mensagens automáticas
    termos_mensagem_auto = [
        'mensagem automática', 'whatsapp', 'resposta automática',
        'fim de semana', 'fora do horário', 'responder depois', 'robô'
    ]
    if any(t in question.lower() for t in termos_mensagem_auto):
        return (
            'Olá, querida! Vamos esclarecer isso com base no que a própria Nanda orienta no curso:<br><br>'
            '📌 A Nanda não recomenda o uso de <strong>mensagens automáticas genéricas</strong> no WhatsApp...<br><br>'
            'Se quiser, posso te ajudar a montar uma mensagem mais humana e acolhedora agora mesmo. Deseja isso?'
        )

    # 4) Verificação de contexto para tipos que exigem
    tipos_que_exigem_contexto = {'explicacao', 'faq', 'revisao', 'correcao', 'precificacao'}
    if tipo_de_prompt in tipos_que_exigem_contexto and not context.strip():
        return OUT_OF_SCOPE_MSG

    # 5) Identidade da IA e templates
    identidade = (
        '<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso '
        '<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>'
    )
    prompt_variacoes = {
        'explicacao': (
            '<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, '
            'com tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula de **Posicionamento High Ticket**.<br><br>'
        ),
        'faq': (
            '<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. '
            'Use exemplos práticos e aplique o método passo a passo.'
        ),
        'revisao': (
            '<strong>Objetivo:</strong> Fazer uma revisão rápida dos pontos centrais do método de precificação estratégica. '
            'Use exatamente seis bullets...<br><br>'
        ),
        'aplicacao': (
            '<strong>Objetivo:</strong> Aplicar o roteiro de atendimento High Ticket na primeira consulta. '
            'Use exatamente seis bullets...<br><br>'
        ),
        'correcao': (
            '<strong>Objetivo:</strong> Corrigir gentilmente qualquer confusão ou prática equivocada...<br><br>'
        ),
        'capitacao_sem_marketing_digital': (
            '<strong>Objetivo:</strong> Mostrar uma **estratégia 100% offline** do método Consultório High Ticket para atrair pacientes de alto valor sem usar Instagram ou anúncios, passo a passo:<br>'
            '➡ **Encantamento de pacientes atuais:** Envie um convite VIP impresso...<br>'
            '➡ **Parcerias com profissionais de saúde:** Conecte-se com médicos...<br>'
            '➡ **Cartas personalizadas com proposta VIP:**...<br>'
            '➡ **Manutenção via WhatsApp (sem automação):**...<br>'
            '➡ **Construção de autoridade silenciosa:**...<br>'
            '➡ **Fidelização e indicações espontâneas:**...<br><br>'
            'Com essa sequência... você **dobra seu faturamento** e conquista pacientes de alto valor **sem depender de redes sociais ou anúncios**.'
        ),
        'precificacao': (
            '<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica...<br><br>'
        ),
        'health_plan': (
            '<strong>Objetivo:</strong> Ensinar o aluno a montar o **Health Plan**...<br><br>'
        )
    }

    # 6) Monta prompt completo
    if tipo_de_prompt == 'capitacao_sem_marketing_digital':
        contexto_para_prompt = ''
    else:
        contexto_para_prompt = (
            f"<br><br><strong>📚 Contexto relevante:</strong><br>{context}<br>" if context.strip() else ''
        )
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, prompt_variacoes['explicacao']) + contexto_para_prompt
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 7) Chama o GPT
    try:
        response = client.chat.completions.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': prompt}]
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}]
        )
    return response.choices[0].message.content
