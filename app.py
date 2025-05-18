import gradio as gr
from career_agent import CareerAgent
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_interface():
    agent = CareerAgent()
    
    def chat_fn(message: str, history: list):
        try:
            response = agent.safe_respond(message, history)
            # Garante que o conteúdo nunca seja vazio
            if not response.get("content"):
                response["content"] = "Não consegui processar sua solicitação. Tente novamente."
            return response["content"]
        except Exception as e:
            logging.error(f"Erro na interface: {str(e)}")
            return "Ocorreu um erro interno. Por favor, recarregue a página."

    interface = gr.ChatInterface(
        fn=chat_fn,
        examples=[
            ["Como criar um currículo para backend?"],
            ["Quais as médias salariais para frontend?"],
            ["Me mostre vagas de Python"]
        ],
        title="🤖 Career Agent",
        description="Assistente de Carreira em Tecnologia",
        theme="soft",
        cache_examples=False  # Importante para evitar os erros de cache
    )
    
    return interface

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False
    )