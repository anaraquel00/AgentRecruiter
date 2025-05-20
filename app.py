import sys
import gradio as gr
from career_agent import CareerAgent
import logging

# Configuração de logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_interface():
    agent = CareerAgent()
    
    def chat_fn(message: str, history: list):
        try:
            # Previne loops vazios
            if not message.strip():
                return history
            
            # Processa a resposta
            response = agent.safe_respond(message, history)
            return history + [(message, response["content"])]  # Formato correto
            
        except Exception as e:
            logging.error(f"Erro na interface: {str(e)}")
            return history + [(message, "⚠️ Erro temporário. Tente novamente em alguns segundos.")]

    # CSS Customizado 
    custom_css = """
    .gradio-container {background: #f8f9fa!important}
    .title {text-align: center; padding: 20px; 
            background: linear-gradient(135deg, #6B46C1 0%, #4299E1 100%); 
            color: white!important; border-radius: 10px}
    .dark .title {background: linear-gradient(135deg, #4B5563 0%, #1F2937 100%)!important}
    footer {visibility: hidden!important}
    """

    with gr.Blocks(title="🤖 Career Agent Pro", css=custom_css, theme=gr.themes.Soft()) as interface:
        # ===== Componentes =====
        chatbot = gr.Chatbot(
            height=500,
            label="Histórico da Conversa",
            type="messages"  # Novo formato obrigatório
        )
        
        msg = gr.Textbox(
            label="Sua Mensagem",
            placeholder="Ex: 'Como criar um currículo para Python?'",
            max_lines=3
        )
        
        # ===== Exemplos =====
        gr.Examples(
            examples=[
                ["Modelo de currículo para Backend Java"],
                ["Salário médio de Engenheiro de Dados"],
                ["Vagas de Python em São Paulo"]
            ],
            inputs=[msg],
            outputs=[chatbot],
            label="💡 Clique para carregar exemplos",
            fn=lambda x: chat_fn(x, [])
        )
        
        # ===== Ações =====
        msg.submit(
            fn=chat_fn,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            api_name="chat_query"  # Endpoint explícito
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