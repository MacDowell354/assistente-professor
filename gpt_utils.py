import os
import unicodedata
import re

OUT_OF_SCOPE_MSG = (
    "Sua pergunta demonstra interesse e vontade de aprender! No entanto, esse tema ainda não faz parte do conteúdo oficial do curso Consultório High Ticket. "
    "Recomendo focar nas estratégias, conceitos e práticas ensinadas nas aulas para transformar seu consultório. "
    "Sua dúvida será encaminhada à equipe pedagógica para avaliarmos uma possível inclusão em futuras atualizações. "
    "Continue participando!"
)

def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

CANONICAL_QA = {
    "explique em passos claros o conceito de posicionamento de alto valor ensinado no curso":
        "No curso Consultório High Ticket, posicionamento de alto valor é um conjunto de ações e mentalidade que fazem você ser reconhecido como referência no mercado. Os passos são: 1) Adote a mentalidade protagonista, não se compare aos colegas e valorize sua história. 2) Comunique de forma clara, evitando termos técnicos e mostrando o impacto do seu trabalho na vida do paciente. 3) Proporcione uma experiência diferenciada ao paciente em cada etapa, desde o contato até o pós-atendimento. 4) Atue com autoridade e autoconfiança, orientando e liderando com ética. 5) Valorize o seu trabalho, explique suas condutas e mostre que investir em saúde é prioridade. O resultado é ser visto como referência, atrair pacientes que valorizam seu serviço e ter uma agenda cheia de qualidade.",

    "quais são as principais dúvidas que alunos normalmente têm sobre captação de pacientes sem usar redes sociais":
        "As dúvidas mais comuns são: se é possível dobrar o faturamento sem Instagram ou anúncios, como criar indicações orgânicas, como transformar o atendimento em fonte de novas indicações, como lidar com concorrência em cidades pequenas, se é preciso investir em eventos ou brindes, como adaptar o método para cada especialidade, e como manter a agenda cheia sem depender só do boca a boca.",

    "faça uma revisão rápida dos pontos centrais do método de precificação estratégica":
        "Os pontos centrais do método de precificação estratégica são: 1) Mude sua mentalidade e valorize o seu trabalho. 2) Baseie o valor no resultado e transformação gerada, não no preço do colega. 3) Apresente o valor de forma clara, ética e segura, mostrando benefícios e diferenciais. 4) Mantenha coerência de preços e saiba recusar pacientes que não valorizam seu método. 5) Use o script e timing correto: o valor é apresentado como parte natural do plano. Assim, você dobra seu faturamento sem desvalorizar seu trabalho.",

    "como aplico o roteiro de atendimento high ticket na primeira consulta com um paciente novo":
        "Na primeira consulta, receba o paciente com acolhimento e atenção. Ouça atentamente suas necessidades, apresente seu diagnóstico e plano de ação de forma simples e humanizada, mostre sua autoridade ao indicar o melhor caminho, use gatilhos mentais do curso, explique o valor do acompanhamento com foco no resultado, e finalize com orientação clara sobre os próximos passos. Encante o paciente com pós-atendimento, reforçando o vínculo.",

    "eu só levantaria preço com o cliente na segunda sessão está certo isso":
        "Não está certo. Pelo método Consultório High Ticket, o valor do seu trabalho é apresentado já na primeira consulta, com naturalidade e clareza. Adiar a conversa sobre valores pode passar insegurança ao paciente. Mostre que o investimento faz parte do plano de cuidado, atraindo pacientes que valorizam seu método e evitando perda de tempo com quem não é o perfil ideal.",

    "me mostre uma estratégia offline para atrair pacientes de alto valor sem usar instagram ou anúncios":
        "Uma das principais estratégias offline é encantar o paciente desde o primeiro contato, criando uma experiência única e personalizada. Use o pós-atendimento para fortalecer o vínculo, invista em rede de indicações com outros profissionais, utilize o encantamento e surpreenda com atenção genuína. Esse conjunto de ações gera indicações espontâneas e lota sua agenda sem depender de redes sociais.",

    "como estruturo a apresentação do valor do health plan para que o paciente veja o retorno do investimento":
        "Explique que o Health Plan foi criado para facilitar a vida do paciente, oferecendo clareza e previsibilidade. Mostre os benefícios do acompanhamento, os resultados esperados e o impacto do plano na qualidade de vida do paciente. Associe o valor ao resultado, use exemplos do curso e apresente o investimento com segurança, sem justificativas. Mostre como investir na saúde é um ganho a longo prazo.",

    "me ajude a montar um health plan para um paciente com enxaqueca crônica":
        "Primeiro, faça uma anamnese detalhada para identificar gatilhos, hábitos e histórico do paciente. Explique de forma simples o diagnóstico, proponha ações personalizadas (tratamento clínico, orientações alimentares, rotinas de sono, técnicas para estresse), agende acompanhamentos periódicos e mostre que o Health Plan traz mais controle e previsibilidade. Apresente o investimento como parte do processo para reduzir crises e melhorar a vida do paciente.",

    "quais exercícios devo fazer para melhorar minhas costas em casa":
        "Sua pergunta demonstra interesse, mas esse tema não faz parte do conteúdo do curso Consultório High Ticket. Nosso foco é ajudar você a dobrar o faturamento do consultório com estratégias de posicionamento, valorização e captação de pacientes high ticket. Para recomendações de exercícios físicos, oriento buscar um profissional da área de saúde física ou fisioterapia."
}

CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]
    if context and len(context.strip()) > 20:
        return context.strip()
    return OUT_OF_SCOPE_MSG
