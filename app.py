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
            return history + [(message, response["content"])]
        except Exception as e:
            return history + [(message, "⚠️ Erro no processamento")]

    # CSS Customizado (AGORA DEFINIDO!)
    custom_css = """
    .gradio-container {background: #f8f9fa!important}
    .title {text-align: center; padding: 20px; background: linear-gradient(135deg, #6B46C1 0%, #4299E1 100%); color: white!important; border-radius: 10px}
    .description {font-size: 1.1em!important; color: #4a5568!important}
    footer {visibility: hidden!important}
    """

    with gr.Blocks(title="Career Agent Pro", css=custom_css, theme="soft") as interface:
        # Header
        gr.Markdown("""
        <div class="title">
            <h1>🤖 Career Agent Pro</h1>
            <p>Soluções Inteligentes para Sua Carreira Tech</p>
        </div>
        """)
        
        # Chat
        chatbot = gr.Chatbot(
            height=500,
            label="Conversa",
            type="messages"
        )
                
        # Exemplos
        gr.Examples(
            examples=[
                ["Como criar um currículo para backend Java?"],
                ["Qual a média salarial para cientista de dados?"],
                ["Mostre vagas de Python em São Paulo"],
                ["Plano de carreira para desenvolvedor fullstack"]
            ],
            inputs=msg,
            label="Clique para carregar exemplos"
        )
        
        # Botões
        with gr.Row():
            gr.Button("🧹 Limpar").click(lambda: None, None, chatbot)
            gr.Button("🚀 Enviar", variant="primary").click(chat_fn, [msg, chatbot], chatbot)

    return interface

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False
    )