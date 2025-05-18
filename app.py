from career_agent import CareerAgent
import gradio as gr
    

def create_interface():
    try:
        agent = CareerAgent()
        logger.info("✅ Agente inicializado com sucesso!")
        # ... restante do código
    except Exception as e:
        logger.error(f"Falha na inicialização: {str(e)}")
        raise
    
    with gr.Blocks(title="🚀 Mentor de Carreiras Tech") as app:
        gr.Markdown("# 🤖 Mentor de Carreiras Tech")
        gr.ChatInterface(
            fn=agent.enhanced_respond,
            examples=[
                "Como criar um currículo para DevOps?",
                "Quais habilidades preciso para Data Science?"
            ]
        )
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch()