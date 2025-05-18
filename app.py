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
                "Como criar um currículo para Desenvolvedor BackEnd?",
                "Quais habilidades aprender em Java?"
            ]
        )
        
        gr.Markdown("""## 💡 Dicas:
            - Pergunte sobre **currículos** ou **planos de carreira**
            - Explore **habilidades** em diferentes áreas""")
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(server_name="0.0.0.0", server_port=7860)