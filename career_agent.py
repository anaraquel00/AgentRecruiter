import os
import sqlite3
from functools import lru_cache
from datetime import datetime
import logging
from typing import Dict, List
from huggingface_hub import InferenceClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CareerAgent:
    def __init__(self):
        """Configuração robusta para Hugging Face Inference API"""
        self.client = InferenceClient(
            model="HuggingFaceH4/zephyr-7b-beta",
            token=os.getenv("HF_TOKEN", "")  # Garanta que HF_TOKEN está nos Secrets
        )
        
        # Verificação crítica do token
        if not os.getenv("HF_TOKEN"):
            logger.error("🚫 HF_TOKEN não encontrado! Verifique os Secrets do Hugging Face")
        
        
        # Configuração do banco de dados
        self.db_path = os.path.join("/tmp", "career_agent.db")
        self._init_database()
        
        # Dados locais como fallback
        self.tech_stacks = {
            "Frontend": {"skills": ["React", "TypeScript", "CSS"], "salary": "R$ 4k-12k"},
            "Backend": {"skills": ["Python", "Node.js", "Java"], "salary": "R$ 5k-15k"},
            "Data": {"skills": ["SQL", "Pandas", "PyTorch"], "salary": "R$ 6k-18k"}
        }

    def _init_database(self):
        """Inicializa o banco de dados SQLite"""
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
        
        # Dados iniciais se o banco estiver vazio
        if cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            self._seed_database()
            
        self.conn.commit()

    def _seed_database(self):
        """Popula o banco com dados iniciais"""
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
        """Consulta otimizada para a API de chat do Hugging Face"""
        try:
            logger.info(f"Enviando prompt para {self.client.model}: {prompt[:50]}...")
            
            # Sintaxe corrigida para chat
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            # Debug detalhado
            logger.debug(f"Resposta completa da API: {response}")
            
            if not response or not response.choices:
                raise ValueError("Resposta vazia da API")
                
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro grave: {str(e)}")
            return ""


    def _local_fallback(self, prompt: str) -> str:
        """Respostas pré-definidas quando a API falha"""
        if "currículo" in prompt.lower():
            return self._generate_resume_template("Fullstack")
        elif "salário" in prompt.lower():
            return "💵 Faixas salariais médias:\n" + "\n".join(
                f"- {role}: {data['salary']}" 
                for role, data in self.tech_stacks.items()
            )
        else:
            return "🔧 Estou com limitações temporárias. Reformule sua pergunta."

    def enhanced_respond(self, message: str, history: list) -> dict:
        """
        Processa a mensagem do usuário e retorna uma resposta formatada
        Args:
            message: Última mensagem do usuário
            history: Histórico completo da conversa
        Returns:
            Dict no formato {role: "assistant", content: "texto"}
        """
        try:
            if intent == "VAGAS":
                return {
            "role": "assistant",
            "content": resposta,
            "type": "messages"  
        }
                
        except Exception as e:
            return {
            "role": "assistant",
            "content": f"Erro: {str(e)}",
            "type": "messages"
        }

    def _classify_intent(self, message: str) -> str:
        """Classifica a intenção usando o modelo LLM"""
        prompt = f"""<|system|>
        Classifique esta mensagem em: VAGAS, CURRICULO, SALARIO ou OUTROS.
        Mensagem: "{message}"
        Responda apenas com o tipo em MAIÚSCULAS.</s>
        <|assistant|>"""
        
        response = self._query_llm(prompt)
        return response.strip().split()[0] if response else "OUTROS"

if __name__ == "__main__":
    # Teste local
    agent = CareerAgent()
    print(agent.enhanced_respond("Quero dicas para meu currículo de backend", []))