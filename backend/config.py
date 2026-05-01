"""
ElectaVerse — Configuration Module
Loads environment variables and defines simulation parameters.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    """Application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'electaverse-secret-key-dev')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')


class SimulationConfig:
    """Real-time simulation engine parameters."""
    # Booth configuration
    TOTAL_BOOTHS = 200
    CONSTITUENCIES = [
        'New Delhi', 'Mumbai North', 'Bangalore South', 'Chennai Central',
        'Kolkata North', 'Hyderabad', 'Pune', 'Lucknow', 'Jaipur Rural',
        'Ahmedabad East'
    ]
    BOOTHS_PER_CONSTITUENCY = TOTAL_BOOTHS // len(CONSTITUENCIES)

    # Timing
    TICK_INTERVAL_SECONDS = 3          # How often simulation updates
    ELECTION_START_HOUR = 7            # 7 AM
    ELECTION_END_HOUR = 18             # 6 PM
    SIMULATED_MINUTES_PER_TICK = 2     # 2 simulated minutes per 3 real seconds
    # Full election day (11 hours) = 330 ticks = ~16.5 real minutes

    # Queue dynamics (Poisson process)
    BASE_ARRIVAL_RATE = 3.0            # Average voters arriving per simulated 10-min window
    PEAK_MULTIPLIERS = {               # Time-of-day multipliers for arrival rate
        7: 1.2, 8: 2.0, 9: 2.5, 10: 2.2,
        11: 1.5, 12: 1.0, 13: 0.8, 14: 1.0,
        15: 1.5, 16: 2.0, 17: 2.5, 18: 1.0
    }
    BASE_THROUGHPUT = 25               # Voters processed per hour per booth
    THROUGHPUT_VARIANCE = 5            # ± variance in throughput

    # Incident probabilities (per booth per tick)
    INCIDENT_PROBABILITIES = {
        'EVM_MALFUNCTION': 0.0008,
        'VVPAT_JAM': 0.0005,
        'VOTER_ID_DISPUTE': 0.004,
        'CROWD_CONTROL': 0.001,
        'ACCESSIBILITY_ISSUE': 0.0015,
        'POWER_OUTAGE': 0.0003,
    }

    # Queue pressure threshold — increases incident probability
    QUEUE_PRESSURE_THRESHOLD = 50
    QUEUE_PRESSURE_INCIDENT_MULTIPLIER = 2.0

    # Proactive AI sweep interval (in ticks)
    AI_SWEEP_INTERVAL_TICKS = 10  # Every ~30 seconds
