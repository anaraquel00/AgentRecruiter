import gradio as gr
from career_agent import CareerAgent

# Configuração segura do Gradio
def create_app():
    agent = CareerAgent()
    
    def gradio_wrapper(message: str, history: List[List[str]]):
        response = agent.safe_respond(message, history)
        # Garantir formato válido para o Chatbot
        if not response["content"]:
            response["content"] = "Resposta não disponível no momento"
        return response["content"]
    
    # Configurar exemplos válidos
    examples = [
        ["Como fazer um currículo para backend?"],
        ["Quais são as vagas disponíveis?"],
        ["Qual o salário médio para frontend?"]
    ]
    
    interface = gr.ChatInterface(
        fn=gradio_wrapper,
        examples=examples,
        title="Career Agent",
        description="Assistente de Carreira em TI",
        # Configurações críticas
        cache_examples=False,
        retry_btn=None,
        undo_btn=None
    )
    
    return interface

if __name__ == "__main__":
    app = create_app()
    # Configuração de deploy segura
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False,
        max_threads=100,
        prevent_thread_lock=True
    )