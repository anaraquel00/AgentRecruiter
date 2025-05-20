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
    
    # Custom CSS para melhorar o visual
    custom_css = """
    footer {visibility: hidden}
    .title {text-align: center; font-family: 'Roboto', sans-serif; color: #2d3436; 
            background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%); padding: 20px!important; border-radius: 10px}
    .description {font-size: 1.1em!important; color: #636e72!important; padding: 15px 25px!important}
    .gradio-container {background: #f8f9fa!important}
    """

    with gr.Blocks(css=custom_css, theme="soft") as interface:
        # Header Estilizado
        gr.HTML("""
        <div class="title">
            <h1>🤖 Career Agent Pro</h1>
            <p style="font-size: 0.9em">Seu Consultor de Carreira em IA</p>
        </div>
        """)

        # Área do Chat
        chatbot = gr.Chatbot(height=500, label="Sessão de Conversa")
        msg = gr.Textbox(label="Sua Mensagem", placeholder="Digite sua pergunta...")
        
        # Exemplos em Accordion
        with gr.Accordion("📌 Exemplos de Perguntas", open=False):
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

        # Botões de Ação
        with gr.Row():
            clear_btn = gr.Button("🧹 Limpar Chat")
            submit_btn = gr.Button("🚀 Enviar Pergunta", variant="primary")

        # Footer Informativo
        gr.HTML("""
        <div class="footer" style="text-align: center; padding: 15px; color: #636e72">
            <p>Powered by HuggingFace 🤗 | v1.2.0 | Ética em IA ⚖️</p>
        </div>
        """)

        # Lógica de Interação
        msg.submit(fn=chat_fn, inputs=[msg, chatbot], outputs=[chatbot])
        submit_btn.click(fn=chat_fn, inputs=[msg, chatbot], outputs=[chatbot])
        clear_btn.click(lambda: None, None, chatbot, queue=False)

    return interface