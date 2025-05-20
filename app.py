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
            return response["content"]
        except Exception as e:
            logging.error(f"Erro na interface: {str(e)}")
            return "Erro interno. Recarregue a página."

    # Custom CSS omitido para brevidade (mantenha igual ao anterior)
    
    with gr.Blocks(title="Career Agent Pro", css=custom_css, theme="soft") as interface:
        gr.Markdown("# 🤖 Career Agent Pro")
        
        # Componentes
        chatbot = gr.Chatbot(height=500)
        msg = gr.Textbox(label="Sua Mensagem", placeholder="Ex: 'Preciso de um modelo de currículo para backend'")
        
        # Exemplos
        gr.Examples(
            examples=[
                ["Como criar um currículo para backend Java?"],
                ["Qual a média salarial para cientista de dados?"],
                ["Mostre vagas de Python em São Paulo"],
                ["Plano de carreira para desenvolvedor fullstack"]
            ],
            inputs=msg
        )
        
        # Ações
        msg.submit(
            fn=chat_fn,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            api_name="predict"
        )
        
        # Botões
        with gr.Row():
            gr.Button("Limpar").click(lambda: None, None, chatbot)

    return interface  

if __name__ == "__main__":
    app = create_interface()
    app.launch(  
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )