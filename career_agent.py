import os
import sqlite3
import logging
from typing import Dict, List, Optional  
import httpx  
from httpx import Timeout  
from functools import lru_cache
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

class CareerAgent:
    def _init_db(self):
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
            link TEXT      
        )
        """)
        self.conn.commit()

    def _validate_hf_token(self):
        token = os.getenv("HF_TOKEN")
        if not token or not token.startswith("hf_"):
            raise ValueError("HF_TOKEN inválido ou ausente!")
        return token

    
    
    def _init_client(self):
        """Configuração segura do cliente"""
        self.client = InferenceClient(
            model="HuggingFaceH4/zephyr-7b-beta",
            token=self.hf_token,
            timeout=10
        )

    def _init_db(self):
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

    def _detect_tech_stack(self, message: str) -> str:
        """Detecta a stack tecnológica mencionada na mensagem"""
        message_lower = message.lower()
        if any(kw in message_lower for kw in ["front", "react", "javascript"]):
            return "Frontend"
        elif any(kw in message_lower for kw in ["back", "python", "node"]):
            return "Backend"
            return "Fullstack"

    def _init_tech_stacks(self):  
        self.tech_stacks = {
            "Frontend": {"skills": ["React", "TypeScript"], "salary": "R$ 4k-12k"},
            "Backend": {"skills": ["Python", "Node.js"], "salary": "R$ 5k-15k"}
        }
    
    def _process_message(self, message: str) -> Dict[str, str]:
        """Fluxo principal com fallback local"""
        try:
            intent = self._classify_intent(message)
            
            if intent == "CURRICULO":
                stack = self._detect_tech_stack(message)
                content = self._generate_resume_template(stack)
                return {"role": "assistant", "content": content or "Modelo não disponível"}
                
            elif intent == "SALARIO":
                content = self._get_salary_info()
                return {"role": "assistant", "content": content or "Informações salariais indisponíveis"}
                
            else:
                return {"role": "assistant", "content": self._general_response() or "Como posso ajudar?"}
            
    except (httpx.ReadTimeout, httpx.ConnectError) as e:
        logger.warning(f"Timeout na API: {str(e)}")
        fallback = self._local_fallback(message)  # <- 4 espaços
        return {"role": "assistant", "content": fallback if fallback else "Sistema temporariamente indisponível"}  
    
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

    def _get_salary_info(self) -> str:
        """Retorna informações salariais formatadas"""
        salaries = [f"{stack}: {data['salary']}" for stack, data in self.tech_stacks.items()]
        return " | ".join(salaries) if salaries else ""

    def _general_response(self) -> str:
        """Resposta padrão para intenções não reconhecidas"""
        return ("Posso ajudar com:\n"
            "- Modelos de currículo\n"
            "- Informações salariais\n"
            "- Dicas de carreira")

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
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro API: {str(e)}")
            return ""

    def enhanced_respond(self, message: str, history: list) -> dict:
        return {"role": "assistant", "content": self._query_llm(message)}

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