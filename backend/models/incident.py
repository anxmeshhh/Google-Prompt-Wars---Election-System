"""
ElectaVerse — Incident Data Model
Represents election-day incidents at polling booths.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class Severity(Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class IncidentType(Enum):
    EVM_MALFUNCTION = 'EVM_MALFUNCTION'
    VVPAT_JAM = 'VVPAT_JAM'
    VOTER_ID_DISPUTE = 'VOTER_ID_DISPUTE'
    CROWD_CONTROL = 'CROWD_CONTROL'
    ACCESSIBILITY_ISSUE = 'ACCESSIBILITY_ISSUE'
    POWER_OUTAGE = 'POWER_OUTAGE'


# Mapping of incident types to their default severity and description templates
INCIDENT_TEMPLATES = {
    IncidentType.EVM_MALFUNCTION: {
        'severity': Severity.CRITICAL,
        'descriptions': [
            'EVM unit not responding to button presses',
            'EVM display showing error code E-402',
            'EVM ballot unit disconnected from control unit',
            'EVM producing beeping sound, votes not registering',
        ],
    },
    IncidentType.VVPAT_JAM: {
        'severity': Severity.HIGH,
        'descriptions': [
            'VVPAT paper slip not printing after vote cast',
            'VVPAT paper jam — machine halted',
            'VVPAT showing incorrect candidate name on slip',
        ],
    },
    IncidentType.VOTER_ID_DISPUTE: {
        'severity': Severity.MEDIUM,
        'descriptions': [
            'Voter name on roll does not match ID card spelling',
            'Voter claims to be registered but not found in electoral roll',
            'Photo mismatch between voter ID and person at booth',
            'Voter presenting expired identification document',
        ],
    },
    IncidentType.CROWD_CONTROL: {
        'severity': Severity.HIGH,
        'descriptions': [
            'Queue exceeding booth premises, blocking road access',
            'Verbal altercation between voters in queue',
            'Unauthorized persons attempting to enter booth area',
        ],
    },
    IncidentType.ACCESSIBILITY_ISSUE: {
        'severity': Severity.MEDIUM,
        'descriptions': [
            'Wheelchair-bound voter unable to access booth entrance',
            'Elderly voter requesting assistance not available',
            'Visually impaired voter — Braille ballot not available',
        ],
    },
    IncidentType.POWER_OUTAGE: {
        'severity': Severity.CRITICAL,
        'descriptions': [
            'Complete power failure at booth — no backup generator',
            'Intermittent power supply causing EVM resets',
            'Generator fuel running low — estimated 30 minutes remaining',
        ],
    },
}


@dataclass
class Incident:
    """A single election-day incident."""
    id: str = field(default_factory=lambda: f'INC-{uuid.uuid4().hex[:8].upper()}')
    booth_id: str = ''
    booth_name: str = ''
    constituency: str = ''
    incident_type: str = ''
    severity: str = 'medium'
    description: str = ''
    status: str = 'open'  # open, triaging, resolved
    ai_recommendation: str = ''
    ai_severity_override: str = ''
    reported_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: str = ''
    resolution_notes: str = ''
    estimated_resolution_minutes: int = 0

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON response."""
        return {
            'id': self.id,
            'booth_id': self.booth_id,
            'booth_name': self.booth_name,
            'constituency': self.constituency,
            'incident_type': self.incident_type,
            'severity': self.severity,
            'description': self.description,
            'status': self.status,
            'ai_recommendation': self.ai_recommendation,
            'ai_severity_override': self.ai_severity_override,
            'reported_at': self.reported_at,
            'resolved_at': self.resolved_at,
            'resolution_notes': self.resolution_notes,
            'estimated_resolution_minutes': self.estimated_resolution_minutes,
        }
