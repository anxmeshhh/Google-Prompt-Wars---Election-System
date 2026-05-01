"""
ElectaVerse — Booth Data Model
Represents a single polling booth with queue state, EVM status, and incidents.
"""

from dataclasses import dataclass, field
from typing import List
import random


@dataclass
class Booth:
    """A single polling booth in the simulation."""
    id: str
    name: str
    constituency: str
    lat: float
    lng: float
    queue_length: int = 0
    throughput_rate: float = 25.0  # voters per hour
    evm_status: str = 'operational'  # operational, faulty, replaced
    vvpat_status: str = 'operational'
    total_votes_cast: int = 0
    is_active: bool = True
    registered_voters: int = 1200
    incidents: List[str] = field(default_factory=list)  # incident IDs

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON response."""
        return {
            'id': self.id,
            'name': self.name,
            'constituency': self.constituency,
            'lat': self.lat,
            'lng': self.lng,
            'queue_length': self.queue_length,
            'throughput_rate': round(self.throughput_rate, 1),
            'evm_status': self.evm_status,
            'vvpat_status': self.vvpat_status,
            'total_votes_cast': self.total_votes_cast,
            'is_active': self.is_active,
            'registered_voters': self.registered_voters,
            'turnout_percent': round(
                (self.total_votes_cast / max(self.registered_voters, 1)) * 100, 1
            ),
            'estimated_wait_minutes': round(
                (self.queue_length / max(self.throughput_rate / 60, 0.1)), 1
            ),
            'status': self._compute_status(),
            'incident_count': len(self.incidents),
        }

    def _compute_status(self) -> str:
        """Compute booth health status."""
        if self.evm_status == 'faulty' or self.vvpat_status == 'faulty':
            return 'critical'
        if self.queue_length > 80:
            return 'danger'
        if self.queue_length > 40:
            return 'warning'
        return 'healthy'


# Coordinate ranges for Indian cities (approximate centers)
CITY_COORDS = {
    'New Delhi': (28.6139, 77.2090),
    'Mumbai North': (19.1760, 72.8777),
    'Bangalore South': (12.9352, 77.6245),
    'Chennai Central': (13.0827, 80.2707),
    'Kolkata North': (22.6128, 88.3630),
    'Hyderabad': (17.3850, 78.4867),
    'Pune': (18.5204, 73.8567),
    'Lucknow': (26.8467, 80.9462),
    'Jaipur Rural': (26.9124, 75.7873),
    'Ahmedabad East': (23.0225, 72.5714),
}


def create_booth(booth_index: int, constituency: str) -> Booth:
    """Factory function to create a booth with realistic defaults."""
    base_lat, base_lng = CITY_COORDS.get(constituency, (20.0, 78.0))
    # Scatter booths within ~0.1 degree of city center
    lat = base_lat + random.uniform(-0.08, 0.08)
    lng = base_lng + random.uniform(-0.08, 0.08)

    return Booth(
        id=f'BOOTH-{constituency[:3].upper()}-{booth_index:03d}',
        name=f'{constituency} Booth #{booth_index}',
        constituency=constituency,
        lat=round(lat, 4),
        lng=round(lng, 4),
        throughput_rate=25 + random.uniform(-5, 5),
        registered_voters=random.randint(800, 1500),
    )
