import gradio as gr
import logging
from career_agent import CareerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_interface():
    try:
        agent = CareerAgent()
        with gr.Blocks() as app:
            gr.Markdown("# 🤖 Mentor de Carreiras Tech")
            gr.ChatInterface(
                fn=agent.enhanced_respond,
                examples=["Como criar um currículo para Python?"],
                type="messages"
            )
        return app
    except Exception as e:
        logger.critical(f"Falha crítica: {str(e)}")
        return gr.Blocks()

if __name__ == "__main__":
    app = create_interface()
    app.launch(server_name="0.0.0.0", server_port=7860, show_error=True)