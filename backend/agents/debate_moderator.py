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

        You must output ONLY a valid JSON object matching this exact schema:
        {
            "persona_a_name": "Name of Persona A",
            "persona_b_name": "Name of Persona B",
            "arguments_a": [
                {
                    "point": "A strong, 2-sentence argument from Persona A's perspective.",
                    "logic_score": 85,
                    "evidence_score": 90,
                    "persuasion_score": 75
                },
                {
                    "point": "Another strong argument from Persona A.",
                    "logic_score": 80,
                    "evidence_score": 70,
                    "persuasion_score": 88
                }
            ],
            "arguments_b": [
                {
                    "point": "A strong, 2-sentence counter-argument from Persona B's perspective.",
                    "logic_score": 90,
                    "evidence_score": 85,
                    "persuasion_score": 80
                },
                {
                    "point": "Another strong argument from Persona B.",
                    "logic_score": 75,
                    "evidence_score": 80,
                    "persuasion_score": 95
                }
            ],
            "verdict": "A completely objective, 2-sentence summary of who made the stronger case and why. Do not sit on the fence."
        }

        Rules:
        - Scores must be integers between 0 and 100.
        - Exactly 2 arguments per persona.
        - The arguments MUST directly clash with each other.
        - Do NOT include markdown blocks (` ```json `). Return the raw JSON string.
        """

    def generate_debate(self, topic: str, persona_a: str, persona_b: str) -> dict:
        """Simulate a debate on a topic between two personas."""
        prompt = f"""
        Topic: {topic}
        Persona A: {persona_a}
        Persona B: {persona_b}
        
        Generate the debate JSON now.
        """
        
        try:
            raw_response = self.gemini.generate_json(prompt, system_instruction=self.system_prompt)
            return json.loads(raw_response, strict=False)
        except Exception as e:
            print(f"Error in Debate Moderator Agent: {e}")
            return {
                "persona_a_name": persona_a,
                "persona_b_name": persona_b,
                "arguments_a": [{"point": "Failed to generate argument.", "logic_score": 0, "evidence_score": 0, "persuasion_score": 0}],
                "arguments_b": [{"point": "Failed to generate argument.", "logic_score": 0, "evidence_score": 0, "persuasion_score": 0}],
                "verdict": "Debate engine offline due to error."
            }
