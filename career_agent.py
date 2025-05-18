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
            "Frontend": {
                "skills": ["React", "TypeScript", "Next.js", "Jest"],
                "salary": "R$ 4.500 - R$ 14.000",
                "dicas": ["Domine componentização", "Aprimore acessibilidade"]
            },
            "Backend": {
                "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
                "salary": "R$ 6.000 - R$ 16.000",
                "dicas": ["Estude arquitetura limpa", "Aprenda Kubernetes"]
            },
            "Data Science": {
                "skills": ["Python", "Pandas", "MLflow", "Spark"],
                "salary": "R$ 8.000 - R$ 20.000",
                "dicas": ["Domine visualização de dados", "Pratique feature engineering"]
            }
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
            fallback = self._local_fallback(message)  
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
        """Respostas personalizadas"""
        return (
            "🎯 Serviços disponíveis:\n\n"
            "1. 🔍 Análise de currículo\n"
            "2. 💰 Pesquisa salarial\n"
            "3. 📌 Vagas personalizadas\n"
            "4. 🚀 Planos de carreira\n\n"
            "Como posso ajudar você hoje?"
        )

    @lru_cache(maxsize=100)
    def _classify_intent(self, message: str) -> str:
        """
        Classifica a intenção do usuário com fallback robusto.
        Retorna uma das opções: VAGAS, CURRICULO, SALARIO, PLANO, OUTROS
        """
        # Limpeza básica da mensagem
        cleaned_msg = message.lower().strip()
        
        # Fallback rápido para mensagens muito curtas
        if len(cleaned_msg) < 3:
            return "OUTROS"
        
        # Dicionário de palavras-chave para fallback local
        keyword_map = {
            "VAGAS": ["vaga", "emprego", "oportunidad", "contrataç"],
            "CURRICULO": ["currículo", "cv", "modelo", "resume"],
            "SALARIO": ["salário", "remuneraç", "ganho", "pagamento"],
            "PLANO": ["plano", "carreira", "progressão", "trajetória"]
        }
        
        # Primeiro verifica por palavras-chave locais (rápido)
        for intent, keywords in keyword_map.items():
            if any(keyword in cleaned_msg for keyword in keywords):
                return intent
        
        # Se não encontrou, usa o LLM para classificação refinada
        try:
            prompt = f"""Analise esta mensagem e classifique a intenção:
    
            Mensagem: "{message}"
    
            Opções (responda APENAS com a palavra-chave correspondente):
            - VAGAS: Perguntas sobre vagas, oportunidades ou processos seletivos
            - CURRICULO: Pedidos relacionados à criação ou revisão de currículos
            - SALARIO: Consultas sobre faixas salariais ou benefícios
            - PLANO: Orientação sobre planejamento de carreira
            - OUTROS: Qualquer outro assunto não listado
    
            Intenção:"""
            
            response = self._query_llm(prompt).strip().upper()
            
            # Validação da resposta do LLM
            valid_intents = ["VAGAS", "CURRICULO", "SALARIO", "PLANO"]
            return response if response in valid_intents else "OUTROS"
            
        except Exception as e:
            logger.error(f"Erro na classificação: {str(e)}")
            return "OUTROS"  
            
    def _local_fallback(self, message: str) -> str:
        """Respostas de fallback melhoradas"""
        if any(kw in message.lower() for kw in ["currículo", "cv", "modelo"]):
            return ("📝 **Modelo de Currículo Tech:**\n"
                    "- Seção de Skills Técnicas\n"
                    "- Projetos Relevantes\n"
                    "- Certificações\n"
                    "- Experiência Profissional (com métricas)")
                    
        elif any(kw in message.lower() for kw in ["salário", "remuneração"]):
            return "💵 Consulte salários por stack:\n- Frontend: R$ 4k-12k\n- Backend: R$ 5k-15k"
            
        return "🌟 Conte-me mais sobre seus objetivos profissionais!"

    
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