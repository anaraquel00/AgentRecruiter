import gradio as gr
import logging
import os
from career_agent import CareerAgent

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_interface():
    try:
        logger.info("🚀 Iniciando inicialização...")
        agent = CareerAgent()
        
        with gr.Blocks(title="🤖 Mentor Tech") as app:
            gr.Markdown("# 🚀 Mentor de Carreiras em Tecnologia")
            
            # Interface simplificada e compatível
            chatbot = gr.ChatInterface(
                fn=agent.enhanced_respond,
                examples=[
                    "Como criar um currículo para Python?",
                    "Quero um plano de carreira em Frontend"
                ]
            )
            
            gr.Markdown("### 💡 Dicas: Pergunte sobre vagas, salários ou planos de carreira")
        
        logger.info("✅ Interface construída com sucesso!")
        return app
        
    except Exception as e:
        logger.critical(f"⛔ Falha crítica: {str(e)}")
        # Fallback seguro
        return gr.Blocks().launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    app = create_interface()
    app.launch()