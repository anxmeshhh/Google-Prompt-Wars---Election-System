"""
ElectaVerse — Election Analyst Agent
Contextual AI assistant for timeline phases and voter guide steps.
Uses Gemini with rich system prompts containing phase/step data.
"""

from services.gemini_service import GeminiService


class ElectionAnalystAgent:
    """Answers voter questions about election phases and guide steps with deep context."""

    def __init__(self):
        self.gemini = GeminiService()

    def answer_phase_question(self, phase: dict, question: str, user_role: str) -> str:
        """Answer a question about a specific election phase, tailored to the user's role."""
        system_prompt = f"""You are ElectaVerse's Election Analyst — an expert on Indian electoral processes.
You are answering a question from a user with the role: {user_role.upper()}.

The user is viewing this election phase:
- Phase: {phase['title']}
- Description: {phase['description']}
- Duration: {phase['duration_info']}
- Key Activities: {', '.join(phase.get('key_activities', []))}

Tailor your answer specifically for a {user_role}:
- If voter: focus on what they need to DO and their rights
- If official: focus on procedural duties, ECI SOPs, and compliance
- If observer: focus on monitoring responsibilities and legal framework

Keep your answer concise (2-4 paragraphs), factual, and actionable. Use bullet points where helpful.
Reference ECI guidelines when applicable. Format in markdown."""

        return self.gemini.generate(question, system_instruction=system_prompt)

    def answer_guide_question(self, step: dict, question: str, user_role: str) -> str:
        """Answer a question about a specific voter guide step, tailored to the user's role."""
        system_prompt = f"""You are ElectaVerse's Election Analyst — an expert on Indian voting procedures.
You are answering a question from a user with the role: {user_role.upper()}.

The user is viewing this voter guide step:
- Step {step['step_number']}: {step['title']}
- Description: {step['description']}
- Required Documents: {', '.join(step.get('documents_required', []))}
- Tips: {', '.join(step.get('tips', []))}

Tailor your answer specifically for a {user_role}:
- If voter: focus on practical steps, rights, and what to expect
- If official: focus on booth management, SOPs, and regulatory duties
- If observer: focus on compliance verification, documentation, and reporting

Keep your answer concise (2-4 paragraphs), factual, and actionable. Use bullet points where helpful.
Reference ECI guidelines when applicable. Format in markdown."""

        return self.gemini.generate(question, system_instruction=system_prompt)
