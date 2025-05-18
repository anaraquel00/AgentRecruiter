import os
import sqlite3
import logging
from typing import Dict, List
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

class CareerAgent:
    def __init__(self):
        # 1. Inicialize TODOS os atributos primeiro
        self.hf_token = None  # ← Inicialização explícita
        self.db_path = os.path.join("/tmp", "career_agent.db")
        self.client = None
        self.conn = None
        self.tech_stacks = {}
        
        # 2. Ordem correta de inicialização
        self._validate_and_set_hf_token()  # Define self.hf_token
        self._init_client()                # Usa self.hf_token
        self._init_tech_stacks()           # Dados locais
        self._init_db()                    # Banco de dados

    def _validate_and_set_hf_token(self):
        """Valida e define o token corretamente"""
        token = os.getenv("HF_TOKEN")
        if not token or not token.startswith("hf_"):
            raise ValueError("HF_TOKEN inválido ou ausente!")
        self.hf_token = token  # ← Atribuição correta

    def _init_client(self):
        """Configuração segura do cliente"""
        self.client = InferenceClient(
            model="HuggingFaceH4/zephyr-7b-beta",
            token=self.hf_token,
            timeout=10
        )

    def _init_db(self):
        """Inicialização robusta do banco"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY,
                    title TEXT
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Erro DB: {str(e)}")
            raise
        
        if cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            self._seed_database()
        self.conn.commit() 

    def _process_message(self, message: str) -> Dict[str, str]:
        """Fluxo principal com fallback local"""
        try:
            intent = self._classify_intent(message)
            
            if intent == "CURRICULO":
                stack = self._detect_tech_stack(message)
                return self._generate_resume(stack)
                
            elif intent == "SALARIO":
                return {"role": "assistant", "content": self._get_salary_info()}
                
            else:
                return {"role": "assistant", "content": self._general_response()}
                
        except InferenceTimeoutError:
            logger.warning("Timeout na API, usando fallback")
            return {"role": "assistant", "content": self._local_fallback(message)}    

    def safe_respond(self, message: str, history: List[List[str]]) -> Dict[str, str]:
        """Entry point seguro com validação completa"""
        try:
            # Validação de entrada
            if not isinstance(message, str) or len(message.strip()) < 2:
                return {"role": "assistant", "content": "Por favor, formule melhor sua pergunta"}
            
            # Circuit breaker
            return self._process_message(message.lower())
            
        except Exception as e:
            logger.error(f"Erro crítico: {str(e)}")
            return {"role": "assistant", "content": "Sistema temporariamente indisponível"}

    @lru_cache(maxsize=100)
    def _classify_intent(self, message: str) -> str:
        """Classificação de intenção com retry"""
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": f"Classifique: {message}"}],
                max_tokens=50,
                temperature=0.3,
                stop_sequences=["</s>"]
            )
            return response.choices[0].message.content.strip().upper()[:10]
        except Exception:
            return "OUTROS"

    def _local_fallback(self, message: str) -> str:
        """Respostas locais pré-definidas"""
        if any(kw in message for kw in ["currículo", "cv"]):
            return "📄 Modelo de currículo:\n- Habilidades técnicas\n- Experiência profissional"
        return "Como posso ajudar com sua carreira tech?"

    
    def _seed_database(self):
        jobs = [
            (1, "Desenvolvedor Frontend", "Tech Solutions", "React/TypeScript", "R$ 8.000", "https://exemplo.com/vaga1"),
            (2, "Engenheiro de Dados", "Data Corp", "Python/SQL", "R$ 12.000", "https://exemplo.com/vaga2")
        ]
        self.conn.executemany(
            "INSERT INTO jobs (id, title, company, skills, salary, link) VALUES (?, ?, ?, ?, ?, ?)",
            jobs
        )

    
    @lru_cache(maxsize=100)
    def _query_llm(self, prompt: str) -> str:
        """Consulta com timeout e validação"""
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7,
                stop_sequences=["</s>"] 
            )
            
            if not response or not response.choices:
                logger.error("Resposta vazia da API")
                return ""
                
            return response.choices[0].message.content.strip()
            
        except InferenceTimeoutError as e:
            logger.warning("Timeout na API")
            raise
        except Exception as e:
            logger.error(f"Falha na API: {str(e)}")
            return ""

    def enhanced_respond(self, message: str, history: List[List[str]]) -> Dict[str, str]:
        try:
            intent = self._classify_intent(message)
            
            if intent == "VAGAS":
                return {"role": "assistant", "content": self._handle_jobs_query(message)}
            elif intent == "CURRICULO":
                return {"role": "assistant", "content": self._generate_resume_template(message)}
            else:
                return {"role": "assistant", "content": self._handle_general_query(message)}
                
        except Exception as e:
            logger.error(f"Erro: {str(e)}")
            return {"role": "assistant", "content": "Ocorreu um erro. Tente novamente."}

    def _classify_intent(self, message: str) -> str:
        prompt = f"""Classifique esta mensagem:
        Mensagem: "{message}"
        Opções: VAGAS, CURRICULO, SALARIO, OUTROS
        Responda apenas com a opção em MAIÚSCULAS."""
        
        response = self._query_llm(prompt).strip()
        return response if response in ["VAGAS", "CURRICULO", "SALARIO"] else "OUTROS"

    def _generate_resume_template(self, stack: str) -> str:
        return f"""
        📄 Modelo de Currículo - {stack}
        Habilidades: {', '.join(self.tech_stacks.get(stack, {}).get('skills', []))}
        """

if __name__ == "__main__":
    agent = CareerAgent()
    print(agent.safe_respond("Preciso de ajuda com meu currículo", []))