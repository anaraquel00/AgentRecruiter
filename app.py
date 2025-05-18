from asyncio import create_task
from datetime import datetime
from dotenv import load_dotenv # type: ignore
load_dotenv()  # Carrega antes de importar outras classes

from career_agent import CareerAgent
import gradio as gr

def create_app():
    agent = CareerAgent()
    
    with gr.Blocks() as app:
        gr.Markdown("# 🤖 Mentor de Carreiras Tech")
        
        gr.ChatInterface(
            fn=agent.enhanced_respond,
            examples=[
                "Como criar um currículo para DevOps?",
                "Quais habilidades aprender para Data Science?"
            ]
        )
        
        gr.Markdown("""## 💡 Dicas:
            - Pergunte sobre **currículos** ou **planos de carreira**
            - Explore **habilidades** em diferentes áreas""")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()