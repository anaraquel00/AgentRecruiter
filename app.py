import gradio as gr
import logging
import os
from typing import List
from career_agent import CareerAgent

# Configuração robusta de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_interface():
    try:
        logger.info("🚀 Inicializando serviço...")
        agent = CareerAgent()
        
        # Configuração à prova de erros
        with gr.Blocks(
            title="Mentor de Carreiras Tech",
            css=".gradio-container {max-width: 800px !important}"
        ) as app:
            
            gr.Markdown("# 🤖 Mentor de Carreiras em Tecnologia")
            
            # ChatInterface com configuração explícita
            gr.ChatInterface(
                fn=agent.safe_respond,
                examples=[
                    ["Como criar um currículo para Python?"],
                    ["Quais habilidades preciso para DevOps?"]
                ],
                type="messages",
                retry_btn=None,
                undo_btn=None,
                autofocus=True
            )
            
        logger.info("✅ Interface configurada com sucesso!")
        return app
        
    except Exception as e:
        logger.critical(f"⛔ Falha crítica na inicialização: {str(e)}")
        return gr.Blocks()

if __name__ == "__main__":
    try:
        app = create_interface()
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            show_api=False  
        )
    except Exception as e:
        logger.critical(f"Falha total: {str(e)}")
        raise