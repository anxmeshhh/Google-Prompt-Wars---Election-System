"""
ElectaVerse — Election Clock
Manages simulated election day time progression.
All parameters loaded from database.
"""


class ElectionClock:
    """Simulates election day time progression."""

    def __init__(self, start_hour: int = 7, end_hour: int = 18, minutes_per_tick: int = 2):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.minutes_per_tick = minutes_per_tick
        self.current_hour = start_hour
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
        self.current_minute += self.minutes_per_tick

        while self.current_minute >= 60:
            self.current_minute -= 60
            self.current_hour += 1

        self._update_phase()

    def set_time(self, hour: int, minute: int = 0):
        """Manually jump to a specific time."""
        self.current_hour = hour
        self.current_minute = minute
        self.day_complete = False
        self._update_phase()

    def reset(self):
        """Reset the clock back to the start."""
        self.current_hour = self.start_hour
        self.current_minute = 0
        self.total_ticks = 0
        self.day_complete = False
        self._update_phase()


    def _update_phase(self):
        """Update the election phase based on current time."""
        if self.current_hour < self.start_hour:
            self.phase = 'PRE_POLL'
            self.is_polling_active = False
        elif self.current_hour < self.end_hour:
            self.phase = 'ACTIVE_POLLING'
            self.is_polling_active = True
        elif self.current_hour < self.end_hour + 2:
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

    def to_dict(self) -> dict:
        """Serialize clock state."""
        total_minutes = (self.end_hour - self.start_hour) * 60
        elapsed = (self.current_hour - self.start_hour) * 60 + self.current_minute
        return {
            'current_hour': self.current_hour,
            'current_minute': self.current_minute,
            'time_string': self.get_time_string(),
            'phase': self.phase,
            'is_polling_active': self.is_polling_active,
            'day_complete': self.day_complete,
            'total_ticks': self.total_ticks,
            'progress_percent': min(100, round(elapsed / max(total_minutes, 1) * 100, 1)),
        }
