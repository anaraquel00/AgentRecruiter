import gradio as gr
import logging
import os
from career_agent import CareerAgent

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_interface():
    try:
        logger.info("Inicializando CareerAgent...")
        agent = CareerAgent()
        logger.info("✅ Agente inicializado com sucesso!")
        
        with gr.Blocks(title="🚀 Mentor Tech") as app:
            gr.Markdown("# 🤖 Mentor de Carreiras em TI")
            
            gr.ChatInterface(
                fn=agent.enhanced_respond,
                examples=[
                    "Como criar um currículo para Python?",
                    "Quero um plano de carreira em Frontend"
                ],
                retry_btn=None
            )
            
            gr.Markdown("### 💡 Dicas:\n- Pergunte sobre salários\n- Peça análise de currículo")
        
        return app
        
    except Exception as e:
        logger.error(f"⛔ Falha crítica: {str(e)}", exc_info=True)
        return gr.Blocks()  # Fallback seguro

if __name__ == "__main__":
    app = create_interface()
    app.launch(server_name="0.0.0.0", server_port=7860)