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
        """verify_claim should return dict with verdict, confidence, reasoning."""
        mock_instance = MagicMock()
        mock_instance.generate_json.return_value = json.dumps({
            'verdict': 'FALSE',
            'confidence_score': 95,
            'reasoning': 'EVMs have no wireless chips.',
            'official_sources': ['ECI Official Guidelines'],
        })
        MockGemini.return_value = mock_instance

        from agents.fact_checker import FactCheckerAgent
        agent = FactCheckerAgent()
        agent.gemini = mock_instance
        result = agent.verify_claim('EVMs can be hacked via Bluetooth')

        assert result['verdict'] == 'FALSE'
        assert result['confidence_score'] == 95
        assert 'reasoning' in result

    @patch('agents.fact_checker.GeminiService')
    def test_verify_claim_with_live_context(self, MockGemini):
        """verify_claim should incorporate live context into the prompt."""
        mock_instance = MagicMock()
        mock_instance.generate_json.return_value = json.dumps({
            'verdict': 'FALSE',
            'confidence_score': 90,
            'reasoning': 'Context shows voting is active.',
            'official_sources': [],
        })
        MockGemini.return_value = mock_instance

        from agents.fact_checker import FactCheckerAgent
        agent = FactCheckerAgent()
        agent.gemini = mock_instance

        context = {
            'clock': {'phase': 'ACTIVE_POLLING', 'time_string': '10:00 AM'},
            'open_incidents': 2,
            'turnout_percent': 35.5,
        }
        result = agent.verify_claim('Voting has been stopped', context)
        assert result['verdict'] == 'FALSE'

    @patch('agents.fact_checker.GeminiService')
    def test_error_returns_error_verdict(self, MockGemini):
        """Agent should return ERROR verdict when Gemini fails."""
        mock_instance = MagicMock()
        mock_instance.generate_json.side_effect = Exception('API quota exceeded')
        MockGemini.return_value = mock_instance

        from agents.fact_checker import FactCheckerAgent
        agent = FactCheckerAgent()
        agent.gemini = mock_instance
        result = agent.verify_claim('Some claim')

        assert result['verdict'] == 'ERROR'
        assert result['confidence_score'] == 0


# ═══════════════════════════════════════════
# DebateModerator Agent Tests
# ═══════════════════════════════════════════

class TestDebateModerator:
    """Test the Debate Moderator agent."""

    @patch('agents.debate_moderator.GeminiService')
    def test_generate_debate_returns_structure(self, MockGemini):
        """generate_debate should return proper debate JSON structure."""
        mock_instance = MagicMock()
        mock_instance.generate_json.return_value = json.dumps({
            'persona_a_name': 'Policy Hawk',
            'persona_b_name': 'Democracy Dove',
            'arguments_a': [{'point': 'Arg 1', 'logic_score': 85, 'evidence_score': 90, 'persuasion_score': 75}],
            'arguments_b': [{'point': 'Counter 1', 'logic_score': 80, 'evidence_score': 85, 'persuasion_score': 88}],
            'verdict': 'Persona A made the stronger case.',
        })
        MockGemini.return_value = mock_instance

        from agents.debate_moderator import DebateModeratorAgent
        agent = DebateModeratorAgent()
        agent.gemini = mock_instance
        result = agent.generate_debate('EVM Security', 'Policy Hawk', 'Democracy Dove')

        assert 'persona_a_name' in result
        assert 'arguments_a' in result
        assert 'verdict' in result

    @patch('agents.debate_moderator.GeminiService')
    def test_error_returns_fallback(self, MockGemini):
        """Agent should return fallback when Gemini fails."""
        mock_instance = MagicMock()
        mock_instance.generate_json.side_effect = Exception('API error')
        MockGemini.return_value = mock_instance

        from agents.debate_moderator import DebateModeratorAgent
        agent = DebateModeratorAgent()
        agent.gemini = mock_instance
        result = agent.generate_debate('Topic', 'A', 'B')

        assert result['persona_a_name'] == 'A'
        assert result['persona_b_name'] == 'B'
        assert 'offline' in result['verdict'].lower() or 'error' in result['verdict'].lower()


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
