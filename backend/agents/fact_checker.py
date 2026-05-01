"""
ElectaVerse — Fact Checker Agent
Uses Gemini to analyze claims and verify them against ECI guidelines and real-time live simulation context.
"""
import json
from services.gemini_service import GeminiService

class FactCheckerAgent:
    def __init__(self):
        self.gemini = GeminiService()
        self.system_prompt = """
        You are the ElectaVerse AI Fact Checker. 
        Your objective is to combat election-day misinformation in India by analyzing WhatsApp forwards, social media rumors, and claims.
        You possess deep knowledge of the Election Commission of India (ECI) mechanics, EVM/VVPAT rules, and general electoral law.
        
        You will receive a User Claim, and optionally, Live Simulation Context (which represents the objective reality right now).

        Analyze the claim strictly and provide a JSON response matching this schema:
        {
            "verdict": "TRUE" | "FALSE" | "MISLEADING",
            "confidence_score": 0 to 100,
            "reasoning": "A highly specific, 2-3 sentence explanation of why this claim is categorized this way.",
            "official_sources": ["Name of official source 1", "Name of official source 2"]
        }

        Rules:
        - If a claim contradicts the Live Simulation Context (e.g. claim says 'Voting closed', but context says 'ACTIVE_POLLING'), mark it FALSE.
        - If a claim relies on a known conspiracy (e.g., 'EVMs hacked via Bluetooth'), mark it FALSE. EVMs are standalone machines with no wireless chips.
        - If a claim has elements of truth but lacks crucial context (e.g. 'Voting stops exactly at 6 PM'), mark it MISLEADING (voters in line by 6 PM are allowed to vote).
        - Respond ONLY with the JSON object. Do not include markdown fences.
        """

    def verify_claim(self, claim: str, live_context: dict = None) -> dict:
        """Analyze a claim and return structured verdict."""
        prompt = f"User Claim to Verify:\n{claim}\n"
        
        if live_context:
            prompt += f"\nLive Objective Context (Use this to verify time-sensitive claims):\n"
            prompt += f"- Current Phase: {live_context.get('clock', {}).get('phase')}\n"
            prompt += f"- Current Time: {live_context.get('clock', {}).get('time_string')}\n"
            prompt += f"- Active Incidents: {live_context.get('open_incidents', 0)}\n"
            prompt += f"- Total Turnout: {live_context.get('turnout_percent')}\n"

        try:
            raw_response = self.gemini.generate_json(prompt, system_instruction=self.system_prompt)
            return json.loads(raw_response)
        except Exception as e:
            print(f"Error in Fact Checker Agent: {e}")
            return {
                "verdict": "ERROR",
                "confidence_score": 0,
                "reasoning": "Failed to connect to the AI verification service.",
                "official_sources": ["Election Commission of India"]
            }
