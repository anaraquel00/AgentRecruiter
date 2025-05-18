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
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro na API: {str(e)}")
            return self._local_fallback(prompt)

    def _local_fallback(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "currículo" in prompt_lower:
            return self._generate_resume_template("Fullstack")
        elif "salário" in prompt_lower or "salario" in prompt_lower:
            return "\n".join(
                f"- {role}: {data['salary']}" 
                for role, data in self.tech_stacks.items()
            )
        return "Como posso ajudar com sua carreira tech?"

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