import gradio as gr
from datetime import datetime

class CareerAgent:
    def __init__(self):
        self.tech_skills = {
            "Frontend": ["React", "TypeScript", "CSS"],
            "Backend": ["Python", "Node.js", "APIs REST"],
            "Data": ["SQL", "Pandas", "Machine Learning"],
            "DevOps": ["Docker", "AWS", "Terraform"]
        }
        
    def generate_response(self, message, history, system_message, max_tokens, temperature, top_p):
        # Processa a mensagem do usuário
        msg = message.lower()
        
        if "currículo" in msg or "resume" in msg:
            return self.generate_tech_resume()
        elif "plano de carreira" in msg or "career plan" in msg:
            return self.generate_career_plan()
        elif "habilidades" in msg or "skills" in msg:
            return self.list_tech_skills()
        else:
            return """🤖 Olá! Sou seu Assistente de Carreiras em Tech. Pergunte sobre:
- "Gerar currículo tech"
- "Criar plano de carreira"
- "Quais habilidades aprender?"
"""

    def generate_tech_resume(self):
        template = """
        **Nome:** [Seu Nome]  
        **Cargo:** [Cargo Tech]  
        **Localização:** [Cidade/Remoto]  
        
        ## 🛠️ Tech Stack  
        - **Frontend:** React, TypeScript  
        - **Backend:** Python, Node.js  
        - **DevOps:** Docker, AWS  
        
        ## 💼 Experiência  
        **Engenheiro de Software @ EmpresaX** (2022-Presente)  
        - Desenvolvi APIs usando FastAPI  
        - Otimizei queries SQL reduzindo tempo em 30%  
        
        ## 🎓 Formação  
        🎓 Ciência da Computação - USP (2021)  
        """
        return "📄 Modelo de Currículo Tech:\n" + template

    def generate_career_plan(self):
        plan = """
        🚀 **Plano de Carreira Tech - 5 Anos**:
        
        1️⃣ **Primeiro Ano**  
        - Dominar uma stack principal (ex: Python/Django)  
        - Contribuir para open-source  
        
        2️⃣ **Terceiro Ano**  
        - Especializar-se em cloud (AWS/GCP)  
        - Obter certificação profissional  
        
        3️⃣ **Quinto Ano**  
        - Almejar posições sênior/arquiteto  
        - Mentorar juniores  
        """
        return plan

    def list_tech_skills(self):
        skills_list = "\n".join(
            f"- **{area}:** {', '.join(skills)}" 
            for area, skills in self.tech_skills.items()
        )
        return "💻 Habilidades Tech por Área:\n" + skills_list

# Cria a interface
agent = CareerAgent()

demo = gr.ChatInterface(
    agent.generate_response,
    additional_inputs=[
        gr.Textbox("Você é um assistente de carreiras em tecnologia.", label="System Prompt"),
        gr.Slider(50, 1000, value=300, label="Max Tokens"),
        gr.Slider(0.1, 1.0, value=0.7, step=0.1, label="Temperature"),
        gr.Slider(0.1, 1.0, value=0.9, step=0.05, label="Top-p")
    ],
    title="🤖 Tech Career Bot",
    description="Gerador de currículos e planos de carreira para tecnologia"
)

if __name__ == "__main__":
    demo.launch()