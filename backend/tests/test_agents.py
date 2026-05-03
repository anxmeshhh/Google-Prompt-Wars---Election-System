"""
ElectaVerse — AI Agent Tests
Tests for all 5 agents with mocked Gemini API responses.
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ═══════════════════════════════════════════
# FactChecker Agent Tests
# ═══════════════════════════════════════════

class TestFactChecker:
    """Test the Fact Checker agent."""

    @patch('agents.fact_checker.GeminiService')
    def test_verify_claim_returns_verdict_structure(self, MockGemini):
        """verify_claim_stream should yield markdown chunks."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["## Verdict: FALSE\n", "**Confidence Score:** 95%\n"])
        MockGemini.return_value = mock_instance

        from agents.fact_checker import FactCheckerAgent
        agent = FactCheckerAgent()
        agent.gemini = mock_instance
        chunks = list(agent.verify_claim_stream('EVMs can be hacked via Bluetooth'))

        assert len(chunks) == 2
        assert "FALSE" in chunks[0]
        assert "95%" in chunks[1]

    @patch('agents.fact_checker.GeminiService')
    def test_verify_claim_with_live_context(self, MockGemini):
        """verify_claim_stream should incorporate live context into the prompt."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["## Verdict: FALSE"])
        MockGemini.return_value = mock_instance

        from agents.fact_checker import FactCheckerAgent
        agent = FactCheckerAgent()
        agent.gemini = mock_instance

        context = {
            'clock': {'phase': 'ACTIVE_POLLING', 'time_string': '10:00 AM'},
            'open_incidents': 2,
            'turnout_percent': 35.5,
        }
        chunks = list(agent.verify_claim_stream('Voting has been stopped', context))
        assert "FALSE" in chunks[0]

    @patch('agents.fact_checker.GeminiService')
    def test_error_returns_error_verdict(self, MockGemini):
        """Agent should handle Gemini stream failures gracefully or raise."""
        mock_instance = MagicMock()
        # In a real generator, if an exception is raised, it bubbles up.
        # We can simulate this by having generate_stream raise an exception when iterated.
        def mock_stream(*args, **kwargs):
            raise Exception('API quota exceeded')
        mock_instance.generate_stream.side_effect = mock_stream
        MockGemini.return_value = mock_instance

        from agents.fact_checker import FactCheckerAgent
        agent = FactCheckerAgent()
        agent.gemini = mock_instance
        
        # Stream methods just yield what the generator yields, so they will raise the Exception
        import pytest
        with pytest.raises(Exception, match='API quota exceeded'):
            list(agent.verify_claim_stream('Some claim'))


# ═══════════════════════════════════════════
# DebateModerator Agent Tests
# ═══════════════════════════════════════════

class TestDebateModerator:
    """Test the Debate Moderator agent."""

    @patch('agents.debate_moderator.GeminiService')
    def test_generate_debate_returns_structure(self, MockGemini):
        """generate_debate_stream should yield markdown chunks."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["# Debate: EVM Security\n", "## Red Corner: Policy Hawk\n"])
        MockGemini.return_value = mock_instance

        from agents.debate_moderator import DebateModeratorAgent
        agent = DebateModeratorAgent()
        agent.gemini = mock_instance
        chunks = list(agent.generate_debate_stream('EVM Security', 'Policy Hawk', 'Democracy Dove'))

        assert len(chunks) == 2
        assert "EVM Security" in chunks[0]
        assert "Policy Hawk" in chunks[1]

    @patch('agents.debate_moderator.GeminiService')
    def test_error_returns_fallback(self, MockGemini):
        """Agent should bubble up stream exceptions."""
        mock_instance = MagicMock()
        def mock_stream(*args, **kwargs):
            raise Exception('API error')
        mock_instance.generate_stream.side_effect = mock_stream
        MockGemini.return_value = mock_instance

        from agents.debate_moderator import DebateModeratorAgent
        agent = DebateModeratorAgent()
        agent.gemini = mock_instance
        
        import pytest
        with pytest.raises(Exception, match='API error'):
            list(agent.generate_debate_stream('Topic', 'A', 'B'))


# ═══════════════════════════════════════════
# IncidentResponder Agent Tests
# ═══════════════════════════════════════════

class TestIncidentResponder:
    """Test the Incident Responder agent."""

    @patch('agents.incident_responder.GeminiService')
    def test_triage_returns_structure(self, MockGemini):
        """triage_incident should return analysis and actions."""
        mock_instance = MagicMock()
        mock_instance.generate_json.return_value = {
            'analysis': 'EVM malfunction detected.',
            'recommended_severity': 'critical',
            'immediate_actions': ['Replace EVM', 'Notify DEO'],
            'escalation_path': 'District Election Officer',
            'estimated_resolution_time_minutes': 45,
        }
        MockGemini.return_value = mock_instance

        from agents.incident_responder import IncidentResponderAgent
        agent = IncidentResponderAgent()
        agent.gemini = mock_instance

        incident = {'incident_type': 'EVM_MALFUNCTION', 'description': 'EVM not working', 'severity': 'critical'}
        booth = {'name': 'Booth 1', 'constituency': 'Delhi', 'queue_length': 50, 'evm_status': 'faulty'}
        result = agent.triage_incident(incident, booth)

        assert 'analysis' in result
        assert 'recommended_severity' in result

    @patch('agents.incident_responder.GeminiService')
    def test_error_returns_fallback(self, MockGemini):
        """Agent should return fallback when Gemini fails."""
        mock_instance = MagicMock()
        mock_instance.generate_json.side_effect = Exception('Error')
        MockGemini.return_value = mock_instance

        from agents.incident_responder import IncidentResponderAgent
        agent = IncidentResponderAgent()
        agent.gemini = mock_instance

        incident = {'incident_type': 'EVM_MALFUNCTION', 'description': 'Test', 'severity': 'high'}
        booth = {'name': 'B1', 'constituency': 'D', 'queue_length': 10, 'evm_status': 'faulty'}
        result = agent.triage_incident(incident, booth)

        assert result['recommended_severity'] == 'high'
        assert 'Investigate manually' in result['immediate_actions']


# ═══════════════════════════════════════════
# ElectionAnalyst Agent Tests
# ═══════════════════════════════════════════

class TestElectionAnalyst:
    """Test the Election Analyst agent."""

    @patch('agents.election_analyst.GeminiService')
    def test_answer_phase_question(self, MockGemini):
        """answer_phase_question should return a string response."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "During active polling, voters should..."
        MockGemini.return_value = mock_instance

        from agents.election_analyst import ElectionAnalystAgent
        agent = ElectionAnalystAgent()
        agent.gemini = mock_instance

        phase = {
            'title': 'Active Polling',
            'description': 'Voters cast ballots',
            'duration_info': '7 AM - 6 PM',
            'key_activities': ['Voting', 'Queue management'],
        }
        result = agent.answer_phase_question(phase, 'What should I do?', 'voter')
        assert isinstance(result, str)
        assert len(result) > 0

    @patch('agents.election_analyst.GeminiService')
    def test_answer_guide_question(self, MockGemini):
        """answer_guide_question should return role-tailored response."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "As an official, you should verify..."
        MockGemini.return_value = mock_instance

        from agents.election_analyst import ElectionAnalystAgent
        agent = ElectionAnalystAgent()
        agent.gemini = mock_instance

        step = {
            'step_number': 1,
            'title': 'Arrive at Booth',
            'description': 'Go to your assigned booth',
            'documents_required': ['Voter ID'],
            'tips': ['Arrive early'],
        }
        result = agent.answer_guide_question(step, 'What documents?', 'official')
        assert isinstance(result, str)
