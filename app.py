import gradio as gr
import logging
import os
import CareerAgent from career_agent 

def create_interface():
    try:
        agent = CareerAgent()
        with gr.Blocks(title="🚀 Mentor Tech", analytics_enabled=False) as app:  # ← Desativa analytics
            gr.Markdown("# 🤖 Mentor de Carreiras em TI")
            
            # Configuração explícita do tipo messages
            chat_interface = gr.ChatInterface(
                fn=agent.enhanced_respond,
                examples=[
                    "Como criar um currículo para Python?",
                    "Quais vagas para Backend?"
                ],
                additional_inputs=None,  # ← Remove inputs extras
                type="messages"  # ← Especifica formato moderno
            )
            
        return app
    except Exception as e:
        logger.error(f"Falha crítica: {str(e)}")
        return gr.Blocks()