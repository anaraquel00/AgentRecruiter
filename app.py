import sys
import gradio as gr
from career_agent import CareerAgent
import logging

# Configuração do logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_interface():
    agent = CareerAgent()
    
    def chat_fn(message: str, history: list):
        try:
            response = agent.safe_respond(message, history)
            return response["content"]
        except Exception as e:
            logging.error(f"Erro na interface: {str(e)}")
            return "⚠️ Sistema temporariamente indisponível"

    # Interface SIMPLES e FUNCIONAL (versão original)
    interface = gr.ChatInterface(
        fn=chat_fn,
        examples=[
            "Modelo de currículo para Backend",
            "Salário de desenvolvedor Python",
            "Vagas de Java em São Paulo"
        ],
        title="🤖 Career Agent",
        description="Assistente de Carreira em TI",
        theme="soft",
        cache_examples=False
    )
    
    return interface

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )