import glob 
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
    def __init__(self):
        self.db_path = os.path.join("/tmp", "career_agent.db")
        self._nuke_database()  # Método novo
        self.hf_token = self._validate_hf_token()
        self.conn = self._create_connection()
        self._init_db()
        self.client = self._init_client()
        self._init_tech_stacks()
        self._seed_database()

    def _nuke_database(self):
        """Remove completamente o banco de dados e arquivos temporários"""
        # Lista todos os arquivos relacionados
        temp_files = glob.glob(f"{self.db_path}*")  # Correto com o módulo importado
        
        for file_path in temp_files:
            try:
                os.remove(file_path)
                print(f"🗑️ Arquivo removido: {file_path}")
            except Exception as e:
                print(f"⚠️ Erro ao remover {file_path}: {str(e)}")
        
        print("✅ Limpeza do banco concluída")
    
        # Verificação final
        if not glob.glob(f"{self.db_path}*"):
            print("✅ Banco de dados e arquivos temporários totalmente removidos")
        else:
            print("❌ Aviso: Alguns arquivos residuais permaneceram")

    def _create_connection(self):
        """Cria conexão com verificação explícita"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Modo de escrita melhorado
        return conn

    def _clean_database(self):
        """Remove completamente o banco de dados existente"""
        db_path = os.path.join("/tmp", "career_agent.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Banco de dados antigo removido: {db_path}")    
        
    def _init_db(self):
        """Criação de tabela com verificação atômica"""
        with self.conn:  # Usando transação
            cursor = self.conn.cursor()
            
            # Verificação quântica do schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jobs'")
            table_sql = cursor.fetchone()
            
            expected_sql = """CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                company TEXT,
                skills TEXT,
                salary TEXT,
                link TEXT)"""
                
            if not table_sql or not table_sql[0].strip().upper() == expected_sql.strip().upper():
                print("🔄 Recriando tabela jobs...")
                cursor.execute("DROP TABLE IF EXISTS jobs")
                cursor.execute(expected_sql)
                self.conn.commit()
                
                # Verificação final
                cursor.execute("PRAGMA table_info(jobs)")
                columns = [col[1] for col in cursor.fetchall()]
                assert 'company' in columns, "❌ Coluna company ausente!"

    def _validate_hf_token(self):
        token = os.getenv("HF_TOKEN")
        if not token or not token.startswith("hf_"):
            raise ValueError("HF_TOKEN inválido ou ausente!")
        return token

    def _init_client(self):
        """Deve RETORNAR a instância do client"""
        try:
            return InferenceClient(
                model="HuggingFaceH4/zephyr-7b-beta",
                token=self.hf_token,
                timeout=30
            )
        except Exception as e:
            logger.error(f"Falha ao criar client: {str(e)}")
            raise RuntimeError("Serviço de IA indisponível") from e

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
        message_lower = message.lower()
        
        stack_keywords = {
            "Frontend": ["frontend", "front-end", "react", "javascript", "angular"],
            "Backend": ["back", "python", "java", "node", "api", "servidor"],
            "Data Science": ["dados", "data", "analista", "machine learning", "bi"]
        }
        
        for stack, keywords in stack_keywords.items():
            if any(kw in message_lower for kw in keywords):
                print(f"[DEBUG] Stack detectada: {stack}")  
                return stack
                
        print(f"[DEBUG] Stack não detectada, usando 'Geral'")
        return "Geral"  

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
                stack = self._detect_tech_stack(message)
                return {
                    "role": "assistant", 
                    "content": self._get_detailed_salary_info(stack)  
                }
                
            else:
                return {"role": "assistant", "content": self._general_response() or "Como posso ajudar?"}
            
        except (httpx.ReadTimeout, httpx.ConnectError) as e:
            logger.warning(f"Timeout na API: {str(e)}")
            fallback = self._local_fallback(message)  
            return {"role": "assistant", "content": fallback if fallback else "Sistema temporariamente indisponível"}  
    
    def safe_respond(self, message: str, history: List[List[str]]) -> Dict[str, str]:
        """Entry point seguro com validação completa"""
        # Verificação crítica do client
        if not hasattr(self, 'client') or self.client is None:
            logger.critical("Cliente de inferência não inicializado!")
            return {"role": "assistant", "content": "Sistema temporariamente indisponível"}
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

    def _get_detailed_salary_info(self, stack: str) -> str:
        # Dados atualizados e mais completos
        salary_data = {
            "Frontend": {
                "junior": "R$ 4.000 - 6.000",
                "pleno": "R$ 7.000 - 10.000",
                "senior": "R$ 11.000 - 15.000",
                "skills": ["React", "TypeScript", "Next.js", "Jest", "Webpack"],
                "fontes": ["Catho", "Glassdoor", "LoveMondays"]
            },
            "Backend": {
                "junior": "R$ 5.000 - 8.000",
                "pleno": "R$ 9.000 - 12.000",
                "senior": "R$ 13.000 - 18.000",
                "skills": ["Python", "Docker", "AWS", "PostgreSQL", "FastAPI"],
                "fontes": ["Catho", "Glassdoor"]
            },
            "Data": {
                "junior": "R$ 6.000 - 9.000",
                "pleno": "R$ 10.000 - 14.000",
                "senior": "R$ 15.000 - 22.000",
                "skills": ["Python", "Pandas", "Spark", "TensorFlow", "Power BI"],
                "fontes": ["Glassdoor", "LinkedIn"]
            }
        }
        
        if stack not in salary_data:
            return "⚠️ Área não reconhecida. Escolha entre: Frontend, Backend ou Data."
        
        data = salary_data[stack]
        response = (
            f"📊 **Médias Salariais para {stack}**\n\n"
            f"• Júnior: {data['junior']}\n"
            f"• Pleno: {data['pleno']}\n"
            f"• Sênior: {data['senior']}\n\n"
            f"🛠️ **Habilidades Essenciais:**\n"
            f"{', '.join(data['skills'])}\n\n"
            f"📈 **Fontes:** {', '.join(data['fontes'])}"
        )
        
        print(f"[DEBUG] Resposta salarial gerada:\n{response}")  # Log
        return response
        
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
        keyword_map =  keyword_map = {
            "VAGAS": ["vaga", "emprego", "oportunidades", "contratação", "linkedin"],
            "CURRICULO": ["currículo", "cv", "modelo", "resume", "formatar"],
            "SALARIO": ["salário", "remuneração", "ganho", "pagamento", "salariais", "média"],  
            "PLANO": ["plano", "carreira", "progressão", "trajetória", "objetivo"]
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

        print(f"[DEBUG] Mensagem: '{message}'")
        print(f"[DEBUG] Intenção detectada: {intent}")
        
        return intent        
            
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
        try:
            cursor = self.conn.cursor()
            
            # Verificação final antes da inserção
            cursor.execute("SELECT company FROM jobs LIMIT 1")
            jobs = [
                (1, "Desenvolvedor Frontend", "Tech Solutions", "React/TypeScript", "R$ 8.000", "https://exemplo.com/vaga1"),
                (2, "Engenheiro de Dados", "Data Corp", "Python/SQL", "R$ 12.000", "https://exemplo.com/vaga2")
            ]
            
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT INTO jobs (id, title, company, skills, salary, link) VALUES (?, ?, ?, ?, ?, ?)",
                jobs
            )
            self.conn.commit()
            print("Dados inseridos com sucesso")
            
        except sqlite3.OperationalError as e:
            print(f"FALHA CRÍTICA NO SCHEMA: {str(e)}")
            print("Estrutura atual da tabela:")
            cursor.execute("PRAGMA table_info(jobs)")
            for col in cursor.fetchall():
                print(f"Coluna {col[1]} ({col[2]})")
            raise RuntimeError("Problema de compatibilidade no banco de dados") from e
    
    @lru_cache(maxsize=100)
    def _query_llm(self, prompt: str) -> str:
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro API: {str(e)}")
            return ""

    def enhanced_respond(self, message: str, history: list) -> dict:
        return {"role": "assistant", "content": self._query_llm(message)}

    def _generate_resume_template(self, stack: str) -> str:
        return f"""
        📄 Modelo de Currículo - {stack}
        Habilidades: {', '.join(self.tech_stacks.get(stack, {}).get('skills', []))}
        """

if __name__ == "__main__":
    agent = CareerAgent()
    print(agent.client)  
    print(agent.conn)    