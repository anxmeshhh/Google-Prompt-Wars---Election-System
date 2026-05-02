"""
ElectaVerse — Data Model Tests
Tests for Booth and Incident dataclass serialization, status computation, and edge cases.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.booth import Booth, create_booth, CITY_COORDS
from models.incident import Incident, Severity, IncidentType, INCIDENT_TEMPLATES


# ═══════════════════════════════════════════
# Booth Model Tests
# ═══════════════════════════════════════════

class TestBoothModel:
    """Test the Booth dataclass."""

    def test_to_dict_has_all_fields(self, sample_booth):
        """Serialized dict should contain all expected keys."""
        d = sample_booth.to_dict()
        expected_keys = {
            'id', 'name', 'constituency', 'lat', 'lng',
            'queue_length', 'throughput_rate', 'evm_status',
            'vvpat_status', 'total_votes_cast', 'is_active',
            'registered_voters', 'turnout_percent',
            'estimated_wait_minutes', 'status', 'incident_count',
        }
        assert set(d.keys()) == expected_keys

    def test_status_healthy(self):
        """Booth with low queue should have 'healthy' status."""
        booth = Booth(id='B1', name='T', constituency='C', lat=0, lng=0, queue_length=10)
        assert booth._compute_status() == 'healthy'

    def test_status_warning(self):
        """Booth with queue > 40 should have 'warning' status."""
        booth = Booth(id='B1', name='T', constituency='C', lat=0, lng=0, queue_length=41)
        assert booth._compute_status() == 'warning'

    def test_status_danger(self):
        """Booth with queue > 80 should have 'danger' status."""
        booth = Booth(id='B1', name='T', constituency='C', lat=0, lng=0, queue_length=81)
        assert booth._compute_status() == 'danger'

    def test_status_critical_faulty_evm(self):
        """Booth with faulty EVM should have 'critical' status."""
        booth = Booth(id='B1', name='T', constituency='C', lat=0, lng=0, evm_status='faulty')
        assert booth._compute_status() == 'critical'

    def test_status_critical_faulty_vvpat(self):
        """Booth with faulty VVPAT should have 'critical' status."""
        booth = Booth(id='B1', name='T', constituency='C', lat=0, lng=0, vvpat_status='faulty')
        assert booth._compute_status() == 'critical'

    def test_turnout_percent(self, sample_booth):
        """Turnout percentage should be calculated correctly."""
        sample_booth.total_votes_cast = 600
        sample_booth.registered_voters = 1200
        d = sample_booth.to_dict()
        assert d['turnout_percent'] == 50.0

    def test_estimated_wait_minutes(self, sample_booth):
        """Wait time should be calculated from queue and throughput."""
        d = sample_booth.to_dict()
        # queue=25, throughput=25/hr = 0.417/min → 25/0.417 ≈ 60 min
        assert d['estimated_wait_minutes'] > 0

    def test_default_values(self):
        """Booth should have sensible defaults."""
        booth = Booth(id='B1', name='T', constituency='C', lat=0, lng=0)
        assert booth.queue_length == 0
        assert booth.evm_status == 'operational'
        assert booth.is_active is True
        assert booth.incidents == []

    def test_create_booth_factory(self):
        """create_booth factory should produce valid booths."""
        booth = create_booth(1, 'New Delhi')
        assert booth.id.startswith('BOOTH-NEW-')
        assert booth.constituency == 'New Delhi'
        assert booth.registered_voters >= 800
        assert booth.registered_voters <= 1500

    def test_city_coords_present(self):
        """All constituencies should have coordinate mappings."""
        assert len(CITY_COORDS) >= 10
        assert 'New Delhi' in CITY_COORDS
        assert 'Mumbai North' in CITY_COORDS


# ═══════════════════════════════════════════
# Incident Model Tests
# ═══════════════════════════════════════════

class TestIncidentModel:
    """Test the Incident dataclass."""

    def test_to_dict_has_all_fields(self, sample_incident):
        """Serialized dict should contain all expected keys."""
        d = sample_incident.to_dict()
        expected_keys = {
            'id', 'booth_id', 'booth_name', 'constituency',
            'incident_type', 'severity', 'description', 'status',
            'ai_recommendation', 'ai_severity_override',
            'reported_at', 'resolved_at', 'resolution_notes',
            'estimated_resolution_minutes',
        }
        assert set(d.keys()) == expected_keys

    def test_default_id_format(self, sample_incident):
        """Default ID should start with 'INC-'."""
        assert sample_incident.id.startswith('INC-')
        assert len(sample_incident.id) == 12  # INC- + 8 hex chars

    def test_default_status_is_open(self):
        """Default incident status should be 'open'."""
        inc = Incident()
        assert inc.status == 'open'

    def test_severity_enum_values(self):
        """Severity enum should have all expected values."""
        values = {s.value for s in Severity}
        assert values == {'critical', 'high', 'medium', 'low'}

    def test_incident_type_enum_values(self):
        """IncidentType enum should have all expected values."""
        values = {t.value for t in IncidentType}
        expected = {
            'EVM_MALFUNCTION', 'VVPAT_JAM', 'VOTER_ID_DISPUTE',
            'CROWD_CONTROL', 'ACCESSIBILITY_ISSUE', 'POWER_OUTAGE',
        }
        assert values == expected

    def test_incident_templates_completeness(self):
        """Every IncidentType should have a template."""
        for itype in IncidentType:
            assert itype in INCIDENT_TEMPLATES
            tmpl = INCIDENT_TEMPLATES[itype]
            assert 'severity' in tmpl
            assert 'descriptions' in tmpl
            assert len(tmpl['descriptions']) > 0
