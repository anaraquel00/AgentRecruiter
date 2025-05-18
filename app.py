import gradio as gr
import logging
import os
from career_agent import CareerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_interface():
    try:
        agent = CareerAgent()
        with gr.Blocks(title="🚀 Mentor Tech") as app:
            gr.Markdown("# 🤖 Mentor de Carreiras em TI")
            
            gr.ChatInterface(
                fn=agent.enhanced_respond,
                examples=["Como criar um currículo para Python?"],
                type="messages"  
            )
            
        return app
    except Exception as e:
        logger.error(f"Erro crítico: {str(e)}")
        return gr.Blocks()

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False 
    )   