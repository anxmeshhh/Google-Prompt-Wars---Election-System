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

        Analyze the claim strictly and provide a detailed markdown response containing:
        1. An explicit Verdict (TRUE, FALSE, or MISLEADING).
        2. A Confidence Score (0-100%).
        3. Detailed Reasoning.
        4. Official Sources.

        Format exactly like this:
        ## Verdict: [YOUR VERDICT]
        **Confidence Score:** [SCORE]%

        ### Reasoning
        [Your reasoning here]

        ### Official Sources
        - [Source 1]
        - [Source 2]

        Rules:
        - If a claim contradicts the Live Simulation Context, mark it FALSE.
        - If a claim relies on a known conspiracy, mark it FALSE.
        - If a claim has elements of truth but lacks crucial context, mark it MISLEADING.
        """

    def verify_claim_stream(self, claim: str, live_context: dict = None):
        """Stream the markdown analysis of a claim."""
        prompt = f"User Claim to Verify:\\n{claim}\\n"
        
        if live_context:
            prompt += f"\\nLive Objective Context (Use this to verify time-sensitive claims):\\n"
            prompt += f"- Current Phase: {live_context.get('clock', {}).get('phase')}\\n"
            prompt += f"- Current Time: {live_context.get('clock', {}).get('time_string')}\\n"
            prompt += f"- Active Incidents: {live_context.get('open_incidents', 0)}\\n"
            prompt += f"- Total Turnout: {live_context.get('turnout_percent')}\\n"

        for chunk in self.gemini.generate_stream(prompt, system_instruction=self.system_prompt, agent='fact_checker'):
            yield chunk
