from tempfile import gettempdir
from huggingface_hub import InferenceClient
import gradio as gr # type: ignore
import random
from typing import List, Dict
from datetime import datetime
import sqlite3
from dotenv import load_dotenv # type: ignore
import os

class CareerAgent:
    def __init__(self):
        load_dotenv()
        self.client = InferenceClient(token=os.getenv("HF_TOKEN"))
        self.model = "mistralai/Mixtral-8x7B-Instruct-v0.1"

        # No Hugging Face, use o diretório temporário
        db_path = os.path.join(gettempdir(), "jobs.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_jobs_table()
        
        # Preencha com dados iniciais se necessário
        if os.path.getsize(db_path) == 0:
            self._seed_database()
        
        # Conecta ao banco de vagas (simulado)
        
        self._create_jobs_table()
        
        # Definindo atributos faltantes
        self.tech_stacks = {
            "Frontend": {"skills": ["React", "TypeScript", "Next.js"], "salario": "R$ 4k-15k"},
            "Backend": {"skills": ["Python", "Node.js", "Go"], "salario": "R$ 5k-18k"},
            "Data Science": {"skills": ["Python", "SQL", "TensorFlow"], "salario": "R$ 6k-20k"},
            "DevOps": {"skills": ["Docker", "Kubernetes", "AWS"], "salario": "R$ 7k-22k"}
        }
        
        self.salary_data = {
            "Júnior": {"min": 4000, "max": 6500},
            "Pleno": {"min": 7000, "max": 12000},
            "Sênior": {"min": 12000, "max": 25000}
        }

        self.job_boards = {
            "Indeed": "https://api.indeed.com/ads/apisearch"
        }
        

    def _query_llm(self, prompt):
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Erro na API do Hugging Face: {str(e)}")
            return self._local_fallback(prompt)  # Usar fallback local
     
    def _seed_database(self):
        cursor = self.conn.cursor()
        cursor.executemany(  # <-- Alinhar com cursor
           "INSERT INTO vagas VALUES (?, ?, ?, ?, ?, ?)",
           [
            (1, "Desenvolvedor Python", "Empresa X", "Python/Django", "R$ 8.000", "https://exemplo.com/vaga1"),
            (2, "Engenheiro de Dados", "Empresa Y", "Python/SQL", "R$ 12.000", "https://exemplo.com/vaga2")
           ]
        )
        self.conn.commit()    
        
    def _create_jobs_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY,
            titulo TEXT,
            empresa TEXT,
            stack TEXT,
            salario TEXT,
            link TEXT
        )
        """)
        self.conn.commit()

    def _query_gpt4(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            api_key=self.openai_key
        )
        return response.choices[0].message.content

    def get_real_jobs(self, stack: str):
        """Busca vagas reais de APIs (simulado)"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vagas WHERE stack LIKE ?", (f"%{stack}%",))
        return cursor.fetchall()

    def enhanced_respond(self, message: str, history: List[List[str]]) -> Dict[str, str]:
        gpt_prompt = f"""
        Analise esta mensagem e classifique a intenção:
        "{message}"
        Opções: 
        - CURRICULO
        - PLANO_CARREIRA 
        - CARTA
        - LINKEDIN
        - SALARIO
        - VAGAS
        - OUTROS
        Retorne apenas o tipo em MAIÚSCULAS.
        """
        intent = self._detect_intent(message)
        return self._handle_intent(intent, message)

        if intent == "VAGAS":
            return {
            "role": "assistant", 
            "content": self._format_jobs(jobs),
            "links": [job[5] for job in jobs]  # Opcional para rich content
        }
        else:
            return {"role": "assistant", "content": "Como posso ajudar?"}
    
    def _format_jobs(self, jobs):
        return "\n".join(
            f"🏢 **{job[1]}** @ {job[2]}\n"
            f"🛠️ {job[3]}\n"
            f"💵 {job[4]}\n"
            f"🔗 {job[5]}\n"
            for job in jobs
        )

    def respond(self, message, history, system_message, max_tokens, temperature):
        msg = message.lower()
        
        if any(p in msg for p in ["currículo", "resume"]):
            return self.generate_custom_resume(msg)
        elif any(p in msg for p in ["plano", "roadmap"]):
            return self.generate_career_roadmap(msg)
        elif any(p in msg for p in ["carta", "cover"]):
            return self.generate_cover_letter(msg)
        elif any(p in msg for p in ["linkedin", "perfil"]):
            return self.analyze_linkedin_profile(msg)
        elif any(p in msg for p in ["salário", "salary"]):
            return self.compare_salaries(msg)
        elif any(p in msg for p in ["habilidades", "skills"]):
            return self.list_tech_skills()
        else:
            return self.show_menu()

    def show_menu(self):
        menu = """🎯 **Menu Principal** (digite o número ou assunto):
        
1️⃣ "Currículo Tech" - Gere um modelo de currículo
2️⃣ "Plano de Carreira" - Roadmap personalizado
3️⃣ "Carta de Apresentação" - Modelo para vagas
4️⃣ "Análise LinkedIn" - Dicas para otimizar
5️⃣ "Comparar Salários" - Por stack e experiência
6️⃣ "Habilidades" - Lista por área tech
Exemplo: "Gere um currículo para backend pleno"
        """
        return menu

    def generate_custom_resume(self, prompt):
        # Lógica para detectar stack e nível
        stack = next((s for s in self.tech_stacks if s.lower() in prompt), "Fullstack")
        level = "Pleno" if "pleno" in prompt else "Júnior" if "júnior" in prompt else "Sênior"
        
        resume = f"""
📄 **CURRÍCULO TECH - {stack.upper()} {level}**  
**Nome:** [Seu Nome]  
**GitHub:** [seu-usuario]  
**Stack Principal:** {', '.join(self.tech_stacks[stack]['skills'][:3])}  
## 💼 Experiência  
**{stack} Developer @ [Empresa]**  
- {' '.join(random.choice([
    "Desenvolvi APIs REST com Python/Flask",
    "Criei dashboards com React e TypeScript",
    "Implementei pipelines de CI/CD"
]))}  
## 🛠️ Tech Stack  
{self.format_skills(stack)}  
💡 *Dica: Personalize com projetos reais do GitHub!*
        """
        return resume

    def generate_career_roadmap(self, prompt):
        years = 3 if "curto" in prompt else 5 if "médio" in prompt else 10
        roadmap = f"""
🚀 **ROADMAP TECH - {years} ANOS**  
1️⃣ **Primeiro Ano**  
- Dominar fundamentos de algoritmos  
- Construir 3 projetos no GitHub  
2️⃣ **Ano {years//2}**  
- Especializar-se em {random.choice(list(self.tech_stacks))}  
- Obter 1 certificação relevante  
3️⃣ **Ano {years}**  
- Alcançar nível Sênior  
- {' '.join(random.choice([
    "Publicar artigos técnicos",
    "Ministrar workshops",
    "Contribuir para open-source"
]))}  
        """
        return roadmap

    def generate_cover_letter(self, prompt):
        company = "Google" if "google" in prompt else "Startup" if "startup" in prompt else "Sua Empresa"
        letter = f"""
✉️ **CARTA PARA {company.upper()}**  
Prezados(as),  
Meu nome é [Seu Nome] e sou especialista em [Sua Stack].  
Ao ver a vaga para [Nome da Vaga], identifiquei compatibilidade com:  
- {random.choice(list(self.tech_stacks))} (3+ anos experiência)  
- Projeto relevante: [Descreva brevemente]  
Tenho grande interesse em contribuir para {company} porque...  
Atenciosamente,  
[Seu Nome]  
        """
        return letter

    def analyze_linkedin_profile(self, prompt):
        analysis = """
🔍 **ANÁLISE DE PERFIL LINKEDIN**  
✅ Pontos fortes:  
- Descrição clara da stack tech  
- Projetos com resultados mensuráveis  
⚠️ Para melhorar:  
- Adicione certificações na seção dedicada  
- Inclua números (ex: "Otimizei performance em 40%")  
💡 Dica premium:  
Use palavras-chave como "{sua stack} + {frameworks}" no título  
        """
        return analysis

    def compare_salaries(self, prompt):
        stack = next((s for s in self.tech_stacks if s.lower() in prompt), "Fullstack")
        comparison = f"""
💰 **SALÁRIOS EM {stack.upper()}**  
Júnior: R$ {self.salary_data['Júnior']['min']/1000}k-{self.salary_data['Júnior']['max']/1000}k  
Pleno: R$ {self.salary_data['Pleno']['min']/1000}k-{self.salary_data['Pleno']['max']/1000}k  
Sênior: R$ {self.salary_data['Sênior']['min']/1000}k-{self.salary_data['Sênior']['max']/1000}k+  
💡 Dica: Salários em FAANG podem ser 2-3x maiores  
        """
        return comparison

    def format_skills(self, stack):
        return "\n".join(f"- {skill}" for skill in self.tech_stacks[stack]["skills"])

    def list_tech_skills(self):
        return "\n".join(
            f"**{stack}** ({info['salario']}): {', '.join(info['skills'])}" 
            for stack, info in self.tech_stacks.items()
        )

# Configuração da Interface
agent = CareerAgent()

demo = gr.ChatInterface(
    agent.enhanced_respond,  # Mudei para usar enhanced_respond
    additional_inputs=[
        gr.Textbox("Você é um especialista em carreiras de tecnologia.", label="Contexto"),
        gr.Slider(100, 1000, value=400, label="Tamanho Máximo da Resposta")
    ],
    title="🚀 Super Mentor de Carreiras Tech",
    description="""Gere currículos, planos de carreira, cartas de apresentação 
    e análises de perfil especializadas em tecnologia"""
)

if __name__ == "__main__":
    demo.launch()