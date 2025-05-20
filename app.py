import sys
import gradio as gr
from career_agent import CareerAgent
import logging

# Configuração de logging
logging.basicConfig(
    stream=sys.stdout,  # Agora sys está definido
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
            return "Erro interno. Recarregue a página."

    # CSS Customizado 
    custom_css = """
    .gradio-container {background: #f8f9fa!important}
    .title {text-align: center; padding: 20px; background: linear-gradient(135deg, #6B46C1 0%, #4299E1 100%); color: white!important; border-radius: 10px}
    .description {font-size: 1.1em!important; color: #4a5568!important}
    footer {visibility: hidden!important}
    """

    with gr.Blocks(title="Career Agent Pro", css=custom_css, theme="soft") as interface:
        # ===== Declare todos os componentes PRIMEIRO =====
        chatbot = gr.Chatbot(height=500, label="Conversa") 
        msg = gr.Textbox(label="Sua Mensagem", placeholder="Digite sua pergunta...")
                
        # Exemplos
        gr.Examples(
            examples=[
                ["Como criar um currículo para Python?"],
                ["Qual o salário de um DevOps?"],
                ["Mostre vagas de Java"]
            ],
            inputs=[msg],  # ✅ Agora msg já está definido
            outputs=chatbot,
            label="📌 Exemplos de Perguntas"
        )

        msg.submit(
            fn=chat_fn,
            inputs=[msg, chatbot],
            outputs=chatbot,
            api_name="predict"
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