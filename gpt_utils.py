import openai
import os
import json
import logging

# Configure logging básico (caso o app principal não tenha configurado)
logging.basicConfig(level=logging.INFO)

# Configura a chave de API da OpenAI a partir da variável de ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.warning("OPENAI_API_KEY não está definida. As chamadas à API OpenAI podem falhar por falta de autenticação.")

# Parâmetros opcionais de modelo e ajustes, com defaults
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1024"))

# Tenta importar bcrypt para recursos de autenticação; caso falhe, prossegue com aviso
try:
    import bcrypt
except ImportError as e:
    bcrypt = None
    logging.error("Falha ao importar módulo bcrypt: %s. A autenticação pode não funcionar corretamente.", e)

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """
    Verifica uma senha de texto plano em comparação com sua versão hash usando bcrypt.
    Se bcrypt não estiver disponível, emite um alerta e ignora a verificação (inseguro).
    """
    if bcrypt is None:
        logging.warning("Ignorando verificação de senha porque o bcrypt está indisponível.")
        # AVISO: Isso tratará qualquer senha como válida. Utilize apenas como paliativo em desenvolvimento.
        return True
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
    except Exception as e:
        logging.error("Erro durante verificação de senha: %s", e)
        return False

# Importa classes de erro da OpenAI para tratamento específico
try:
    from openai.error import AuthenticationError, RateLimitError, InvalidRequestError, OpenAIError
except ImportError:
    # Caso não seja possível importar, define aliases genéricos para evitar NameError
    AuthenticationError = RateLimitError = InvalidRequestError = OpenAIError = Exception

def generate_answer(user_question: str, system_prompt: str = None) -> str:
    """
    Gera uma resposta do modelo OpenAI para uma determinada pergunta do usuário.
    Opcionalmente inclui um prompt de sistema para contexto ou instruções adicionais.
    Retorna o texto da resposta ou uma mensagem de erro segura caso algo dê errado.
    """
    # Prepara a lista de mensagens para o chat (contexto + pergunta do usuário)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_question})
    
    # Chama a API OpenAI e trata exceções da chamada
    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except AuthenticationError as e:
        logging.error("OpenAI AuthenticationError: %s", e)
        return "Erro de autenticação ao conectar com o serviço de IA."
    except RateLimitError as e:
        logging.error("OpenAI RateLimitError: %s", e)
        return "A API de IA atingiu o limite de requisições. Por favor, tente novamente mais tarde."
    except InvalidRequestError as e:
        logging.error("OpenAI InvalidRequestError: %s", e)
        return "Falha na solicitação ao modelo de IA. Verifique os parâmetros e tente novamente."
    except OpenAIError as e:
        logging.error("OpenAI API error: %s", e)
        return "Ocorreu um erro ao obter a resposta do modelo de IA."
    except Exception as e:
        logging.exception("Erro inesperado ao chamar a API OpenAI: %s", e)
        return "Ocorreu um erro interno ao processar a resposta do assistente de IA."
    
    # Valida a estrutura da resposta recebida
    if response is None:
        logging.error("A API OpenAI não retornou nenhuma resposta (None).")
        return "Desculpe, não foi possível obter resposta do assistente no momento."
    if "choices" not in response or not response.get("choices"):
        logging.error("A API OpenAI retornou um formato inesperado: %s", response)
        return "Desculpe, a resposta do assistente não pôde ser interpretada."
    
    # Extrai o conteúdo da mensagem de resposta do assistente
    try:
        answer_content = response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error("Falha ao extrair o campo 'content' da resposta da OpenAI: %s", e)
        return "Desculpe, ocorreu um problema ao ler a resposta do assistente."
    
    if answer_content is None:
        answer_content = ""
    answer_content = answer_content.strip()
    
    if answer_content == "":
        logging.error("A OpenAI retornou conteúdo vazio para a pergunta: '%s'", user_question)
        return "Desculpe, o assistente não conseguiu gerar uma resposta para sua pergunta."
    
    # Remove blocos de código Markdown (``` ```), se presentes, em torno de conteúdo JSON
    if "```" in answer_content:
        start_idx = answer_content.find("```")
        end_idx = answer_content.rfind("```")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            # Extrai apenas o conteúdo dentro do bloco de código
            fenced_content = answer_content[start_idx+3:end_idx]
            answer_content = fenced_content.strip()
        # Remove indicador de linguagem (ex: "json") se estiver presente logo no início
        if answer_content.lower().startswith("json"):
            lines = answer_content.splitlines()
            if lines and lines[0].strip().lower() == "json":
                lines = lines[1:]
            answer_content = "\n".join(lines).strip()
    
    # Tenta interpretar a resposta como JSON, se aparentemente estiver em formato JSON
    parsed_data = None
    if answer_content.startswith("{") or answer_content.startswith("["):
        try:
            parsed_data = json.loads(answer_content)
        except json.JSONDecodeError as e:
            logging.error("JSON parse error for model response: %s. Content: %s", e, answer_content)
            parsed_data = None
    
    # Se o JSON foi interpretado com sucesso, formata a saída apropriadamente
    if parsed_data is not None:
        try:
            if isinstance(parsed_data, dict):
                # Se houver algum campo relevante, retorna apenas ele (e.g. 'answer' ou 'resposta')
                for key in ("answer", "resposta", "content", "message", "resultado"):
                    if key in parsed_data:
                        return str(parsed_data[key])
                # Caso nenhum dos campos esperados esteja presente, retorna o JSON inteiro formatado
                return json.dumps(parsed_data, ensure_ascii=False, indent=2)
            elif isinstance(parsed_data, list):
                # Se a resposta é uma lista, retorna o array JSON formatado
                return json.dumps(parsed_data, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error("Error processing parsed JSON output: %s", e)
            # Em caso de falha ao manipular o JSON, volta ao conteúdo bruto
            return answer_content
    
    # Se não for JSON ou se o parsing falhou, retorna o texto puro da resposta
    return answer_content
