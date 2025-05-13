import gradio as gr
import random
from datetime import datetime

class SuperCareerAgent:
    def __init__(self):
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
agent = SuperCareerAgent()

demo = gr.ChatInterface(
    agent.respond,
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