from career_agent import CareerAgent
import gradio as gr

def create_interface():
    agent = CareerAgent()
    
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