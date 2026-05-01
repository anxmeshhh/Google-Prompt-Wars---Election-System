"""
ElectaVerse — Election Clock
Manages simulated election day time progression.
"""

from config import SimulationConfig


class ElectionClock:
    """Simulates election day time progression."""

    def __init__(self):
        self.current_hour = SimulationConfig.ELECTION_START_HOUR
        self.current_minute = 0
        self.total_ticks = 0
        self.phase = 'PRE_POLL'
        self.is_polling_active = False
        self.day_complete = False

    def tick(self):
        """Advance the simulation clock by one tick."""
        if self.day_complete:
            return

        self.total_ticks += 1
        self.current_minute += SimulationConfig.SIMULATED_MINUTES_PER_TICK

        while self.current_minute >= 60:
            self.current_minute -= 60
            self.current_hour += 1

        self._update_phase()

    def _update_phase(self):
        """Update the election phase based on current time."""
        if self.current_hour < SimulationConfig.ELECTION_START_HOUR:
            self.phase = 'PRE_POLL'
            self.is_polling_active = False
        elif self.current_hour < SimulationConfig.ELECTION_END_HOUR:
            self.phase = 'ACTIVE_POLLING'
            self.is_polling_active = True
        elif self.current_hour < SimulationConfig.ELECTION_END_HOUR + 2:
            self.phase = 'POST_POLL'
            self.is_polling_active = False
        else:
            self.phase = 'COUNTING'
            self.is_polling_active = False
            self.day_complete = True

    def get_time_string(self) -> str:
        """Return formatted time string."""
        period = 'AM' if self.current_hour < 12 else 'PM'
        display_hour = self.current_hour if self.current_hour <= 12 else self.current_hour - 12
        if display_hour == 0:
            display_hour = 12
        return f'{display_hour}:{self.current_minute:02d} {period}'

    def get_arrival_multiplier(self) -> float:
        """Get the time-of-day arrival rate multiplier."""
        return SimulationConfig.PEAK_MULTIPLIERS.get(self.current_hour, 1.0)

    def to_dict(self) -> dict:
        """Serialize clock state."""
        return {
            'current_hour': self.current_hour,
            'current_minute': self.current_minute,
            'time_string': self.get_time_string(),
            'phase': self.phase,
            'is_polling_active': self.is_polling_active,
            'day_complete': self.day_complete,
            'total_ticks': self.total_ticks,
            'progress_percent': min(100, round(
                ((self.current_hour - SimulationConfig.ELECTION_START_HOUR) * 60 + self.current_minute) /
                ((SimulationConfig.ELECTION_END_HOUR - SimulationConfig.ELECTION_START_HOUR) * 60) * 100, 1
            )),
        }
