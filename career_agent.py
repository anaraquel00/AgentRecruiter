import os
import sqlite3
import glob
import logging
import httpx
import threading
from huggingface_hub import InferenceClient
from functools import lru_cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CareerAgent:
    def __init__(self):
        self.db_path = os.path.abspath("/tmp/career_agent.db")  
        self._nuke_database()
        self.hf_token = self._validate_hf_token()
        self.local = threading.local()  
        self._init_db_once() 
        
        self.client = self._init_client()
        self._init_tech_stacks()
        logger.info("CareerAgent inicializado com sucesso!")

    def _get_conn(self):
        """Retorna a conexão da thread atual"""
        if not hasattr(self.local, "conn") or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.execute("PRAGMA foreign_keys = 1")
            self.local.conn.execute("PRAGMA journal_mode = WAL")
        return self.local.conn    

    def _nuke_database(self):
        """Destruição total do banco com verificação em 3 níveis"""
        # Nível 1: Remoção padrão
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.info(f"Removido banco principal: {self.db_path}")
        
        # Nível 2: Arquivos temporários do SQLite
        temp_files = glob.glob(f"{self.db_path}*")
        for f in temp_files:
            try:
                os.remove(f)
                logger.info(f"Removido arquivo temporário: {f}")
            except Exception as e:
                logger.error(f"Falha ao remover {f}: {str(e)}")
        
        # Nível 3: Verificação final
        if any(os.path.exists(f) for f in [self.db_path] + temp_files):
            raise RuntimeError("FALHA CRÍTICA: Não foi possível limpar o banco!")

    def _create_connection(self):
        """Cria conexão com configurações de desempenho e verificação"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = 1")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _init_db_once(self):
        """Executado apenas na thread principal"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS jobs")
            cursor.execute("""
                CREATE TABLE jobs (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    skills TEXT,
                    salary TEXT,
                    link TEXT
                )
            """)
            logger.debug("Tabela 'jobs' criada com sucesso!")
            self._seed_initial_data(conn)  # ← Seed acontece aqui
        finally:
            conn.close()  

    def _clean_database(self):
        """Remove completamente o banco de dados existente"""
        db_path = os.path.join("/tmp", "career_agent.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Banco de dados antigo removido: {db_path}")    
        
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

    def _detect_tech_stack(self, message: str) -> str:
        message_lower = message.lower()
        logger.debug(f"Detectando stack para: '{message_lower}'")
        
        stack_keywords = {
            "Frontend": ["frontend", "front-end", "react", "javascript", "angular"],
            "Backend": ["backend", "back-end", "python", "java", "node", "api", "api rest", "api restfull", "servidor"],
            "Data Science": ["dados", "data", "analista", "machine learning", "bi"]
        }
        
        for stack, keywords in stack_keywords.items():
            if any(kw in message_lower for kw in keywords):
                logger.debug(f"Stack detectada: {stack}")
                return stack
                
        logger.debug("Stack não detectada, usando 'Geral'")
        return "Geral" 

    def _init_tech_stacks(self):  
        self.tech_stacks = {
            "Frontend": {
                "skills": ["Angular", "React", "Node.js", " Vue.js", "TypeScript", "Next.js", "Jest"],
                "salary": "R$ 3.500 - R$ 14.000",
                "dicas": ["Domine componentização", "Aprimore acessibilidade"]
            },
            "Backend": {
                "skills": ["Python", "Java", "FastAPI", "API Rest", "APIs RESTfull", "Docker", "PostgreSQL"],
                "salary": "R$ 3.000 - R$ 16.000",
                "dicas": ["Estude arquitetura limpa", "Aprenda Kubernetes", "Aprenda fundamentos de Python", "Aprenda Java POO"]
            },
            "Data Science": {
                "skills": ["Python", "MySQL", "PosteGreSQL", "MongoDB", "Pandas", "MLflow", "Spark"],
                "salary": "R$ 5.000 - R$ 20.000",
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

            elif intent == "PREREQ":  
                stack = self._detect_tech_stack(message)  
                return {  
                    "role": "assistant",  
                    "content": self._get_requirements(stack)  
                }     
                
            elif intent == "SALARIO":
                stack = self._detect_tech_stack(message)
                return {
                    "role": "assistant", 
                    "content": self._get_detailed_salary_info(stack)  
                }

            elif intent == "VAGAS":
                tech = self._detect_tech_stack(message)  
                jobs = self._get_jobs(tech)
                
                if not jobs:
                    return {"role": "assistant", "content": "⚠️ Nenhuma vaga encontrada para esta stack"}
                
                response = "🚀 **Vagas Encontradas:**\n"
                for job in jobs:
                    response += (
                        f"• **{job['title']}** ({job['company']})\n"
                        f"  💰 {job['salary']} | 🛠️ {job['skills']}\n"
                        f"  🔗 {job['link']}\n"
                    )
                return {"role": "assistant", "content": response}
            
            else:
                return {"role": "assistant", "content": self._general_response() or "Como posso ajudar?"}
            
        except (httpx.ReadTimeout, httpx.ConnectError) as e:
            logger.warning(f"Timeout na API: {str(e)}")
            fallback = self._local_fallback(message)  
            return {"role": "assistant", "content": fallback if fallback else "Sistema temporariamente indisponível"}  
    
    def safe_respond(self, message: str, history: List[List[str]]) -> Dict[str, str]:
        """Entry point seguro com validação completa"""
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

    def _get_requirements(self, stack: str) -> str:  
        stack_data = self.tech_stacks.get(stack, {})  
        
        # Verifica se a stack existe e tem dados
        if not stack_data:
            logger.error(f"Stack {stack} não encontrada no tech_stacks!")
            return "⚠️ Stack não reconhecida."
            
        # Garante que 'skills' e 'dicas' existem
        skills = stack_data.get("skills", [])
        dicas = stack_data.get("dicas", [])
        
        # Log dos dados encontrados
        dicas_formatadas = "\n- ".join(stack_data.get('dicas', []))
    
        # Constrói a resposta
        response = (
            f"📚 **Pré-requisitos para {stack}**\n\n"
            f"🛠️ Habilidades Técnicas:\n-" 
            f"- {', '.join(stack_data.get('skills', []))}\n\n"
            f"🚀 Dicas de Estudo:\n-" 
            f"- {dicas_formatadas}\n\n"
            f"💡 **Dica Bônus:** Pratique projetos reais!"
        )
        return response 

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

    def _get_jobs(self, skill: str) -> List[Dict]:
        try:
            conn = self._get_conn()  
            cursor = conn.cursor()   

            # Obter habilidades da stack (ex: ["Java", "Python"] para Backend)
            skills = self.tech_stacks.get(stack, {}).get('skills', [])
            if not skills:
                return []
            
            # Criar termos de busca: "%java%", "%python%", etc.
            search_terms = [f"%{skill.lower()}%" for skill in skills]
            
            query = f"""
                SELECT title, company, skills, salary, link 
                FROM jobs 
                WHERE LOWER(skills) LIKE ? 
                ORDER BY salary DESC
            """, (f"%{skill.lower()}%",))

            cursor.execute(query, search_terms)
            return [
                {"title": row[0], "company": row[1], "skills": row[2], 
                 "salary": row[3], "link": row[4]}
                for row in cursor.fetchall()
            ]
                        
        except Exception as e:
            logger.error(f"Erro ao buscar vagas: {str(e)}")
            return []                
        
    @lru_cache(maxsize=100)
    def _classify_intent(self, message: str) -> str:
        """
        Classifica a intenção do usuário com fallback robusto.
        Retorna uma das opções: VAGAS, CURRICULO, SALARIO, PLANO, OUTROS
        """
        # Limpeza básica da mensagem
        cleaned_msg = message.lower().strip()
        logger.debug(f"Classificando intenção para mensagem: '{cleaned_msg}'")
        
        # Fallback rápido para mensagens muito curtas
        if len(cleaned_msg) < 3:
            return "OUTROS"
        
        # Dicionário de palavras-chave para fallback local
        keyword_map =  keyword_map = {
            "VAGAS": ["vaga", "emprego", "python", "oportunidade", "contratando", "java", "angular", "react"],
            "CURRICULO": ["currículo", "cv", "modelo", "resume", "formatar"],
            "PREREQ": ["pré-requisitos", "requisitos", "habilidades necessárias", "habilidades técnicas", "o que preciso saber"], 
            "SALARIO": ["salário", "remuneração", "ganho", "pagamento", "salariais", "média"],  
            "PLANO": ["plano", "carreira", "progressão", "trajetória", "objetivo"]
        }
        
        for intent, keywords in keyword_map.items():
            if any(kw in cleaned_msg for kw in keywords):
                logger.debug(f"Intenção detectada via keywords: {intent}")
                return intent
            
        # Se não encontrou, usa o LLM para classificação refinada
        try:
            prompt = f"""Analise esta mensagem e classifique a intenção:
    
            Mensagem: "{message}"
    
            Opções (responda APENAS com a palavra-chave correspondente):
            - VAGAS: Perguntas sobre vagas, oportunidades ou processos seletivos)   
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

    
    def _seed_initial_data(self, conn):  
        try:
            cursor = conn.cursor()
            
            # Verificação final antes da inserção
            cursor.execute("SELECT company FROM jobs LIMIT 1")
            jobs = [
                (1, "Desenvolvedor Frontend", "Tech Solutions", "React/TypeScript", "R$ 8.000", "https://exemplo.com/vaga1"),
                (2, "Engenheiro de Dados", "Data Corp", "Python/SQL", "R$ 12.000", "https://exemplo.com/vaga2"),
                (3, "Cientista de Dados", "AI Tech", "Python/Pandas", "R$ 15.000", "https://exemplo.com/vaga3"),
                (4, "Arquiteto Backend", "Cloud Systems", "Java/Micronaut/AWS", "R$ 18.000", "https://exemplo.com/arquiteto"),
                (5, "Desenvolvedor Java Pleno", "Tech Innovations", "Java/Spring/Hibernate", "R$ 12.000", "https://exemplo.com/java")
            ]
            
            cursor.executemany(
                "INSERT INTO jobs (id, title, company, skills, salary, link) VALUES (?, ?, ?, ?, ?, ?)",
                jobs
            )
            conn.commit()
            logger.info(f"Dados iniciais inseridos: {len(jobs)} vagas") 
                      
        except Exception as e:
            logger.error(f"Falha ao inserir dados: {str(e)}")
            raise    
        
    
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