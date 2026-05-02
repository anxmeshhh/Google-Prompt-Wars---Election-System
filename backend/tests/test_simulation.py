"""
ElectaVerse — Simulation Engine Tests
Tests for ElectionClock, QueueDynamics, and IncidentInjector.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.election_clock import ElectionClock
from simulation.queue_dynamics import QueueDynamics


# ═══════════════════════════════════════════
# ElectionClock Tests
# ═══════════════════════════════════════════

class TestElectionClock:
    """Test the simulated election day clock."""

    def test_initial_state(self):
        """Clock should start in PRE_POLL phase."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        assert clock.current_hour == 7
        assert clock.current_minute == 0
        assert clock.phase == 'PRE_POLL'
        assert clock.is_polling_active is False
        assert clock.day_complete is False
        assert clock.total_ticks == 0

    def test_tick_advances_time(self):
        """Each tick should advance time by minutes_per_tick."""
        clock = ElectionClock(start_hour=7, end_hour=18, minutes_per_tick=2)
        clock.tick()
        assert clock.total_ticks == 1
        assert clock.current_minute == 2

    def test_phase_active_polling(self):
        """Clock should transition to ACTIVE_POLLING during election hours."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        clock.set_time(10, 0)
        assert clock.phase == 'ACTIVE_POLLING'
        assert clock.is_polling_active is True

    def test_phase_post_poll(self):
        """Clock should transition to POST_POLL after election hours."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        clock.set_time(18, 30)
        assert clock.phase == 'POST_POLL'
        assert clock.is_polling_active is False

    def test_phase_counting_and_day_complete(self):
        """Clock should mark day complete in COUNTING phase."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        clock.set_time(20, 0)
        assert clock.phase == 'COUNTING'
        assert clock.day_complete is True

    def test_reset(self):
        """Reset should return clock to initial state."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        clock.set_time(12, 30)
        clock.total_ticks = 100
        clock.reset()
        assert clock.current_hour == 7
        assert clock.current_minute == 0
        assert clock.total_ticks == 0
        assert clock.phase == 'PRE_POLL'

    def test_set_time(self):
        """set_time should jump to the specified hour."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        clock.set_time(14, 30)
        assert clock.current_hour == 14
        assert clock.current_minute == 30

    def test_time_string_format(self):
        """get_time_string should return formatted time."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        clock.set_time(14, 30)
        time_str = clock.get_time_string()
        assert 'PM' in time_str
        assert '2:30' in time_str

    def test_to_dict_has_all_fields(self):
        """to_dict should contain all expected fields."""
        clock = ElectionClock(start_hour=7, end_hour=18)
        d = clock.to_dict()
        assert 'current_hour' in d
        assert 'time_string' in d
        assert 'phase' in d
        assert 'is_polling_active' in d
        assert 'day_complete' in d
        assert 'progress_percent' in d

    def test_minute_overflow_increments_hour(self):
        """When minutes overflow 60, hour should increment."""
        clock = ElectionClock(start_hour=7, end_hour=18, minutes_per_tick=30)
        clock.tick()  # 7:30
        clock.tick()  # 8:00
        assert clock.current_hour == 8
        assert clock.current_minute == 0


# ═══════════════════════════════════════════
# QueueDynamics Tests
# ═══════════════════════════════════════════

class TestQueueDynamics:
    """Test the voter queue simulation engine."""

    def test_poisson_sample_non_negative(self):
        """Poisson samples should always be non-negative."""
        for _ in range(100):
            val = QueueDynamics.poisson_sample(3.0)
            assert val >= 0

    def test_poisson_zero_lambda(self):
        """Poisson with lambda=0 should return 0."""
        assert QueueDynamics.poisson_sample(0) == 0

    def test_poisson_negative_lambda(self):
        """Poisson with negative lambda should return 0."""
        assert QueueDynamics.poisson_sample(-5) == 0

    def test_departures_capped_by_queue(self):
        """Departures should never exceed current queue length."""
        for _ in range(50):
            deps = QueueDynamics.compute_departures(
                queue_length=3, throughput_rate=100.0, minutes_per_tick=10
            )
            assert deps <= 3

    def test_departures_zero_queue(self):
        """Departures from empty queue should be 0."""
        deps = QueueDynamics.compute_departures(
            queue_length=0, throughput_rate=30.0, minutes_per_tick=2
        )
        assert deps == 0

    def test_faulty_evm_stops_departures(self):
        """Faulty EVM should result in zero throughput."""
        new_q, arrivals, deps = QueueDynamics.update_queue(
            queue_length=50, throughput_rate=25.0,
            base_arrival_rate=3.0, minutes_per_tick=2,
            time_multiplier=1.0, is_polling_active=True,
            evm_status='faulty'
        )
        assert deps == 0

    def test_replaced_evm_reduces_throughput(self):
        """Replaced EVM should process at 70% capacity."""
        # Run multiple times and check that departures are produced (not zero)
        total_deps = 0
        for _ in range(20):
            _, _, deps = QueueDynamics.update_queue(
                queue_length=100, throughput_rate=50.0,
                base_arrival_rate=0.0, minutes_per_tick=5,
                time_multiplier=1.0, is_polling_active=True,
                evm_status='replaced'
            )
            total_deps += deps
        assert total_deps > 0  # Should still process some voters

    def test_no_arrivals_when_polling_inactive(self):
        """No arrivals should occur when polling is inactive."""
        new_q, arrivals, deps = QueueDynamics.update_queue(
            queue_length=20, throughput_rate=25.0,
            base_arrival_rate=5.0, minutes_per_tick=2,
            time_multiplier=1.0, is_polling_active=False,
        )
        assert arrivals == 0


# ═══════════════════════════════════════════
# IncidentInjector Tests
# ═══════════════════════════════════════════

class TestIncidentInjector:
    """Test the stochastic incident generation system."""

    def test_auto_resolve_low_severity(self):
        """Low severity incidents should resolve after fewer ticks."""
        from simulation.incident_injector import IncidentInjector
        # Low severity threshold is 5, with variance
        resolved = False
        for _ in range(50):
            if IncidentInjector.auto_resolve_check('low', ticks_elapsed=10):
                resolved = True
                break
        assert resolved, "Low severity incident should resolve within 10 ticks"

    def test_auto_resolve_critical_takes_longer(self):
        """Critical incidents should NOT auto-resolve quickly."""
        from simulation.incident_injector import IncidentInjector
        # Critical threshold is 50, so 5 ticks should never resolve
        result = IncidentInjector.auto_resolve_check('critical', ticks_elapsed=5)
        assert result is False
