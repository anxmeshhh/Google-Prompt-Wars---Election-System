"""
ElectaVerse — Incident Injector
Stochastic generation of election-day incidents.
Incident types, probabilities, and templates loaded from database.
"""

import random
import json
from models.incident import Incident


class IncidentInjector:
    """Generates realistic election-day incidents based on DB-driven probabilities."""

    def __init__(self, incident_configs: list[dict]):
        """
        Args:
            incident_configs: List of dicts from incident_config DB table.
                Each has: incident_type, base_probability, default_severity, description_templates (JSON)
        """
        self.configs = {}
        for cfg in incident_configs:
            templates = cfg['description_templates']
            if isinstance(templates, str):
                templates = json.loads(templates)
            self.configs[cfg['incident_type']] = {
                'probability': float(cfg['base_probability']),
                'severity': cfg['default_severity'],
                'descriptions': templates,
            }

    def check_for_incidents(self, booth, current_hour: int, peak_hours: list = None) -> list:
        """Check if any incidents should be generated for a booth this tick."""
        if peak_hours is None:
            peak_hours = [8, 9, 10, 16, 17]

        incidents = []
        for incident_type, cfg in self.configs.items():
            probability = cfg['probability']

            # Peak hour multiplier
            if current_hour in peak_hours:
                probability *= 1.5

            # Queue pressure
            if booth.queue_length > 50:
                if incident_type in ['CROWD_CONTROL', 'ACCESSIBILITY_ISSUE']:
                    probability *= 2.0

            # Don't stack same-type incidents
            if incident_type == 'EVM_MALFUNCTION' and booth.evm_status == 'faulty':
                continue
            if incident_type == 'VVPAT_JAM' and booth.vvpat_status == 'faulty':
                continue

            if random.random() < probability:
                inc = Incident(
                    booth_id=booth.id,
                    booth_name=booth.name,
                    constituency=booth.constituency,
                    incident_type=incident_type,
                    severity=cfg['severity'],
                    description=random.choice(cfg['descriptions']),
                    status='open',
                )
                incidents.append(inc)

                if incident_type == 'EVM_MALFUNCTION':
                    booth.evm_status = 'faulty'
                elif incident_type == 'VVPAT_JAM':
                    booth.vvpat_status = 'faulty'
                elif incident_type == 'POWER_OUTAGE':
                    booth.evm_status = 'faulty'

        return incidents

    @staticmethod
    def auto_resolve_check(incident_severity: str, ticks_elapsed: int) -> bool:
        """Check if an incident should auto-resolve."""
        thresholds = {'low': 5, 'medium': 15, 'high': 30, 'critical': 50}
        threshold = thresholds.get(incident_severity, 20)
        threshold = int(threshold * random.uniform(0.7, 1.3))
        return ticks_elapsed >= threshold
