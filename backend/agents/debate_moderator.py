"""
ElectaVerse — Debate Moderator Agent
Simulates high-stakes policy debates between two distinct AI personas.
"""
import json
from services.gemini_service import GeminiService

class DebateModeratorAgent:
    def __init__(self):
        self.gemini = GeminiService()
        self.system_prompt = """
        You are the ElectaVerse Debate Moderator for the "Prompt Wars" Arena.
        Your job is to simulate a fierce, highly intellectual, and objective debate between two specific AI Personas on a given Indian electoral or policy topic.

        Instead of JSON, you must format your response exactly in this Markdown structure so it can be streamed to the audience:

        # Debate: [Topic]

        ## Red Corner: [Persona A Name]
        **Argument 1:** [Strong, 2-sentence argument]
        *(Logic: 85/100, Evidence: 90/100, Persuasion: 75/100)*

        **Argument 2:** [Another strong argument]
        *(Logic: 80/100, Evidence: 70/100, Persuasion: 88/100)*

        ---

        ## Blue Corner: [Persona B Name]
        **Argument 1:** [Strong, 2-sentence counter-argument]
        *(Logic: 90/100, Evidence: 85/100, Persuasion: 80/100)*

        **Argument 2:** [Another strong argument]
        *(Logic: 75/100, Evidence: 80/100, Persuasion: 95/100)*

        ---

        ## Moderator Verdict
        [A completely objective, 2-sentence summary of who made the stronger case and why. Do not sit on the fence.]
        """

    def generate_debate_stream(self, topic: str, persona_a: str, persona_b: str):
        """Simulate a debate and stream the markdown output."""
        prompt = f"Topic: {topic}\\nPersona A: {persona_a}\\nPersona B: {persona_b}\\n\\nGenerate the debate now."
        
        for chunk in self.gemini.generate_stream(prompt, system_instruction=self.system_prompt, agent='debate_moderator'):
            yield chunk
