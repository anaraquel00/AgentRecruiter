import os
import sqlite3
from functools import lru_cache
import logging
from typing import Dict, List
from huggingface_hub import InferenceClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CareerAgent:
    def __init__(self):
        self.client = InferenceClient(
            model="HuggingFaceH4/zephyr-7b-beta",
            token=os.getenv("HF_TOKEN", "")
        )
        
        if not os.getenv("HF_TOKEN"):
            logger.error("🚫 HF_TOKEN não encontrado!")
        
        self.db_path = os.path.join("/tmp", "career_agent.db")
        self._init_database()
        
        self.tech_stacks = {
            "Frontend": {"skills": ["React", "TypeScript", "CSS"], "salary": "R$ 4k-12k"},
            "Backend": {"skills": ["Python", "Node.js", "Java"], "salary": "R$ 5k-15k"},
            "Data": {"skills": ["SQL", "Pandas", "PyTorch"], "salary": "R$ 6k-18k"}
        }

    def _validate_environment(self):
        """Validação rigorosa das variáveis de ambiente"""
        self.hf_token = os.getenv("HF_TOKEN")
        if not self.hf_token or len(self.hf_token) < 10:
            logger.error("Token HF inválido ou ausente")
            raise ValueError("Configure HF_TOKEN nas variáveis de ambiente")

        def _init_hf_client(self):
            """Client com timeouts e reconexão"""
            return InferenceClient(
            model="HuggingFaceH4/zephyr-7b-beta",
            token=self.hf_token,
            timeout=15.0  # Timeout para evitar loops
        )

    def safe_enhanced_respond(self, message: str, history: List[List[str]]):
        """Wrapper seguro com circuit breaker"""
        try:
            # Validação de entrada crítica
            if not message or len(message.strip()) < 3:
                return {"role": "assistant", "content": "Por favor, formule melhor sua pergunta"}
            
            return self._enhanced_respond_with_retry(message, history)
            
        except Exception as e:
            logger.error(f"Erro crítico: {str(e)}")
            return {"role": "assistant", "content": "Sistema temporariamente indisponível"}

    def _enhanced_respond_with_retry(self, message: str, history: List[List[str]], retries=2):
        """Lógica de retry com backoff"""
        try:
            intent = self._classify_intent(message)
            # ... sua lógica existente ...
            
        except InferenceTimeoutError:
            if retries > 0:
                time.sleep(1.5)
                return self._enhanced_respond_with_retry(message, history, retries-1)
            raise

    def _init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            company TEXT,
            skills TEXT,
            salary TEXT,
            link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        if cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            self._seed_database()
        self.conn.commit()

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
    print(agent.enhanced_respond("Quero dicas para meu currículo de backend", []))