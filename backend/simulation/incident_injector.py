"""
ElectaVerse — Incident Injector
Stochastic generation of election-day incidents.
"""

import random
from models.incident import Incident, IncidentType, INCIDENT_TEMPLATES, Severity
from config import SimulationConfig


class IncidentInjector:
    """Generates realistic election-day incidents based on probability distributions."""

    def __init__(self):
        self.incident_counter = 0

    def check_for_incidents(self, booth, current_hour: int) -> list:
        """
        Check if any incidents should be generated for a booth this tick.
        Returns a list of Incident objects (usually 0 or 1).
        """
        incidents = []

        for incident_type_str, base_prob in SimulationConfig.INCIDENT_PROBABILITIES.items():
            incident_type = IncidentType(incident_type_str)
            probability = base_prob

            # Increase incident probability during peak hours
            if current_hour in [8, 9, 10, 16, 17]:
                probability *= 1.5

            # Queue pressure increases crowd control and accessibility issues
            if booth.queue_length > SimulationConfig.QUEUE_PRESSURE_THRESHOLD:
                if incident_type in [IncidentType.CROWD_CONTROL, IncidentType.ACCESSIBILITY_ISSUE]:
                    probability *= SimulationConfig.QUEUE_PRESSURE_INCIDENT_MULTIPLIER

            # Don't generate EVM incidents if already faulty
            if incident_type == IncidentType.EVM_MALFUNCTION and booth.evm_status == 'faulty':
                continue
            if incident_type == IncidentType.VVPAT_JAM and booth.vvpat_status == 'faulty':
                continue

            # Roll the dice
            if random.random() < probability:
                incident = self._create_incident(incident_type, booth)
                incidents.append(incident)

                # Apply booth-level effects
                if incident_type == IncidentType.EVM_MALFUNCTION:
                    booth.evm_status = 'faulty'
                elif incident_type == IncidentType.VVPAT_JAM:
                    booth.vvpat_status = 'faulty'
                elif incident_type == IncidentType.POWER_OUTAGE:
                    booth.evm_status = 'faulty'

        return incidents

    def _create_incident(self, incident_type: IncidentType, booth) -> Incident:
        """Create a new incident with realistic details."""
        self.incident_counter += 1
        template = INCIDENT_TEMPLATES[incident_type]
        description = random.choice(template['descriptions'])

        return Incident(
            booth_id=booth.id,
            booth_name=booth.name,
            constituency=booth.constituency,
            incident_type=incident_type.value,
            severity=template['severity'].value,
            description=description,
            status='open',
        )

    @staticmethod
    def auto_resolve_check(incident: Incident, ticks_since_creation: int) -> bool:
        """
        Check if an incident should auto-resolve based on time elapsed.
        Simple incidents resolve faster than critical ones.
        """
        resolution_ticks = {
            'low': 5,       # ~15 seconds real-time
            'medium': 15,   # ~45 seconds
            'high': 30,     # ~90 seconds
            'critical': 50, # ~150 seconds
        }
        threshold = resolution_ticks.get(incident.severity, 20)
        # Add randomness: ±30%
        threshold = int(threshold * random.uniform(0.7, 1.3))
        return ticks_since_creation >= threshold
