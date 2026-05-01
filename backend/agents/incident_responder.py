"""
ElectaVerse — Incident Responder Agent
Uses Gemini to triage and recommend resolutions for real-time booth incidents.
"""
import json
from services.gemini_service import GeminiService

class IncidentResponderAgent:
    def __init__(self):
        self.gemini = GeminiService()
        self.system_prompt = """
        You are the ElectaVerse Incident Commander. 
        Your job is to analyze real-time election day incidents and provide immediate triage recommendations.
        You have deep knowledge of the Election Commission of India (ECI) guidelines.

        Respond ONLY with a valid JSON object matching this schema:
        {
            "analysis": "Brief analysis of the situation",
            "recommended_severity": "low" | "medium" | "high" | "critical",
            "immediate_actions": ["Action 1", "Action 2"],
            "escalation_path": "Who to contact",
            "estimated_resolution_time_minutes": 30
        }
        """

    def triage_incident(self, incident: dict, booth: dict) -> dict:
        """Analyze an incident and return triage recommendations."""
        prompt = f"""
        Analyze this incident:
        Type: {incident.get('incident_type')}
        Description: {incident.get('description')}
        Reported Severity: {incident.get('severity')}
        
        Booth Context:
        Name: {booth.get('name')}
        Constituency: {booth.get('constituency')}
        Current Queue: {booth.get('queue_length')} voters
        EVM Status: {booth.get('evm_status')}
        """
        
        try:
            response = self.gemini.generate_json(prompt, system_instruction=self.system_prompt)
            # Add AI reasoning back to the incident
            return response
        except Exception as e:
            print(f"Error in Incident Responder: {e}")
            return {
                "analysis": "AI triage unavailable due to error.",
                "recommended_severity": incident.get('severity', 'medium'),
                "immediate_actions": ["Investigate manually"],
                "escalation_path": "Returning Officer",
                "estimated_resolution_time_minutes": 60
            }
