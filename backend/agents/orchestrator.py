"""
ElectaVerse — Agent Orchestrator
Classifies user intent and routes to the correct specialist agent.
Injects live simulation context into every prompt so agents have real-time awareness.
"""

import json
from services.gemini_service import GeminiService


class Orchestrator:
    """Routes user messages to the correct specialist agent based on intent."""

    AGENT_MAP = {
        'election_analyst': 'ElectionAnalyst — General election knowledge Q&A',
        'fact_checker': 'FactChecker — Verify claims, debunk misinformation',
        'incident_responder': 'IncidentResponder — Triage booth incidents',
        'queue_manager': 'QueueManager — Queue predictions and wait times',
    }

    def __init__(self):
        self.gemini = GeminiService()

    def classify_intent(self, message: str) -> str:
        """Use Gemini to classify which agent should handle this message."""
        if not self.gemini.is_available():
            return 'election_analyst'  # default fallback

        system = """You are an intent classifier for an election monitoring system.
Given a user message, respond with ONLY one of these agent names (nothing else):
- election_analyst  (for general election questions, processes, laws, history)
- fact_checker      (for verifying claims, checking if something is true/false)
- incident_responder (for reporting or asking about booth incidents, EVM issues)
- queue_manager     (for queue wait times, best time to vote, booth congestion)

Respond with ONLY the agent name, no explanation."""

        try:
            result = self.gemini.generate(message, system_instruction=system).strip().lower()
            # Clean up response
            for agent in self.AGENT_MAP:
                if agent in result:
                    return agent
            return 'election_analyst'
        except Exception:
            return 'election_analyst'

    def route_and_respond(self, message: str, live_context: dict, user_role: str) -> dict:
        """
        1. Classify intent
        2. Build real-time context string
        3. Route to specialist agent
        4. Return response with agent attribution
        """
        agent_name = self.classify_intent(message)
        context_str = self._build_context_string(live_context)

        # Build the role-aware system prompt
        if agent_name == 'election_analyst':
            response = self._election_analyst(message, context_str, user_role)
        elif agent_name == 'fact_checker':
            response = self._fact_checker(message, context_str, user_role)
        elif agent_name == 'incident_responder':
            response = self._incident_responder(message, context_str, user_role)
        elif agent_name == 'queue_manager':
            response = self._queue_manager(message, context_str, user_role)
        else:
            response = self._election_analyst(message, context_str, user_role)

        return {
            'agent': agent_name,
            'agent_label': self.AGENT_MAP.get(agent_name, 'ElectionAnalyst'),
            'response': response,
        }

    def _build_context_string(self, ctx: dict) -> str:
        """Convert live simulation state into a readable context block for agent prompts."""
        if not ctx:
            return "No live simulation data available."

        clock = ctx.get('clock', {})
        lines = [
            "=== LIVE ELECTION DATA (Real-Time) ===",
            f"Simulation Time: {clock.get('time_string', 'N/A')}",
            f"Election Phase: {clock.get('phase', 'N/A')}",
            f"Day Progress: {clock.get('progress_percent', 0)}%",
            f"Polling Active: {'Yes' if clock.get('is_polling_active') else 'No'}",
            f"Total Votes Cast: {ctx.get('total_votes', 0):,}",
            f"Total Registered Voters: {ctx.get('total_registered', 0):,}",
            f"Current Turnout: {ctx.get('turnout_percent', 0)}%",
            f"Active Booths: {ctx.get('active_booths', 0)} / {ctx.get('total_booths', 0)}",
            f"Average Queue Length: {ctx.get('avg_queue_length', 0)} voters",
            f"Max Queue Length: {ctx.get('max_queue_length', 0)} voters",
            f"Open Incidents: {ctx.get('open_incidents', 0)}",
            f"Critical Incidents: {ctx.get('critical_incidents', 0)}",
            f"Total Incidents Today: {ctx.get('total_incidents', 0)}",
            "=== END LIVE DATA ===",
        ]

        # Add top congested booths if available
        top_booths = ctx.get('top_congested_booths', [])
        if top_booths:
            lines.append("\nMost Congested Booths Right Now:")
            for b in top_booths[:5]:
                lines.append(f"  - {b['name']} ({b['constituency']}): Queue={b['queue_length']}, Votes={b['total_votes_cast']}")

        # Add recent incidents if available
        recent_incidents = ctx.get('recent_incidents', [])
        if recent_incidents:
            lines.append("\nRecent Incidents:")
            for inc in recent_incidents[:5]:
                lines.append(f"  - [{inc['severity'].upper()}] {inc['incident_type']} at {inc.get('booth_name','Unknown')}: {inc['description'][:80]}")

        return "\n".join(lines)

    # ── Specialist Agent Implementations ──

    def _election_analyst(self, message: str, context: str, role: str) -> str:
        system = f"""You are ElectaVerse's Election Analyst — India's most knowledgeable election expert.
You have deep expertise in: ECI procedures, EVM/VVPAT technology, Model Code of Conduct,
Lok Sabha / Rajya Sabha / State Assembly processes, electoral roll management, and Indian constitutional provisions for elections.

You are speaking to a user with the role: {role.upper()}.
- If voter: explain in simple terms, focus on rights and practical steps
- If official: use technical ECI terminology, reference SOPs and forms
- If observer: focus on legal framework, compliance, and monitoring protocols

IMPORTANT: You have access to LIVE election simulation data. Use it to make your answers contextual and grounded in what's happening RIGHT NOW.

{context}

Format your response in clean markdown. Use bullet points and headers for readability.
Be concise but thorough. If the live data is relevant to the question, reference it naturally."""

        return self.gemini.generate(message, system_instruction=system)

    def _fact_checker(self, message: str, context: str, role: str) -> str:
        system = f"""You are ElectaVerse's Fact Checker — a meticulous election misinformation analyst.
Your job is to analyze claims about Indian elections and provide structured verdicts.

You are speaking to a user with the role: {role.upper()}.

IMPORTANT: You have access to LIVE election data. Cross-reference claims against actual data when possible.

{context}

For every claim, structure your response as:
## Verdict: [TRUE / MISLEADING / FALSE / UNVERIFIABLE]
**Confidence:** [X]%

### Analysis
[Your detailed reasoning]

### Evidence
[Key facts supporting your verdict]

### What You Should Know
[Important context for the user]

Be rigorous. If a claim is partially true, mark it MISLEADING and explain why."""

        return self.gemini.generate(message, system_instruction=system)

    def _incident_responder(self, message: str, context: str, role: str) -> str:
        system = f"""You are ElectaVerse's Incident Responder — an election day crisis coordinator.
You understand ECI protocols for handling booth-level incidents including EVM malfunctions,
VVPAT issues, voter disputes, crowd control, accessibility problems, and power outages.

You are speaking to a user with the role: {role.upper()}.
- If voter: help them understand what to do and their rights
- If official: provide specific ECI SOP steps, form numbers, escalation paths
- If observer: explain documentation and reporting requirements

IMPORTANT: You have access to LIVE incident data. Reference active incidents when relevant.

{context}

Structure your response with:
- **Severity Assessment**
- **Immediate Actions** (numbered steps)
- **Escalation Path** (who to contact)
- **Estimated Resolution**"""

        return self.gemini.generate(message, system_instruction=system)

    def _queue_manager(self, message: str, context: str, role: str) -> str:
        system = f"""You are ElectaVerse's Queue Manager — a real-time queue analytics expert.
You understand Poisson arrival models, throughput dynamics, time-of-day patterns,
and can make data-driven predictions about wait times and optimal voting windows.

You are speaking to a user with the role: {role.upper()}.

IMPORTANT: You have access to LIVE queue and booth data. Use the actual numbers to make predictions.

{context}

When asked about queues or wait times:
1. Reference the ACTUAL current data (average queue, max queue, specific booth data)
2. Analyze the current time vs. typical peak/lull patterns (peaks at 9 AM and 5 PM, lull at 1 PM)
3. Give a specific recommendation with reasoning
4. If relevant, suggest alternative booths or times

Format in clear markdown with specific numbers from the live data."""

        return self.gemini.generate(message, system_instruction=system)
