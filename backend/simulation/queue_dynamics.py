"""
ElectaVerse — Queue Dynamics Engine
Models voter arrivals and departures using Poisson process.
All parameters are injected — nothing hardcoded.
"""

import random
import math


class QueueDynamics:
    """Models queue behavior at polling booths using stochastic processes."""

    @staticmethod
    def poisson_sample(lam: float) -> int:
        """Generate a Poisson-distributed random number."""
        if lam <= 0:
            return 0
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1

    @staticmethod
    def compute_arrivals(base_rate: float, minutes_per_tick: int, time_multiplier: float) -> int:
        """Compute voter arrivals for this tick using Poisson distribution."""
        base_rate_per_minute = base_rate / 10
        lam = base_rate_per_minute * minutes_per_tick * time_multiplier
        lam *= random.uniform(0.7, 1.3)
        lam = max(0, lam)
        return QueueDynamics.poisson_sample(lam)

    @staticmethod
    def compute_departures(queue_length: int, throughput_rate: float, minutes_per_tick: int) -> int:
        """Compute how many voters are processed this tick."""
        if queue_length == 0:
            return 0
        voters_per_minute = throughput_rate / 60
        variance = random.uniform(0.8, 1.2)
        expected = voters_per_minute * minutes_per_tick * variance
        return min(queue_length, max(0, int(round(expected))))

    @staticmethod
    def update_queue(
        queue_length: int,
        throughput_rate: float,
        base_arrival_rate: float,
        minutes_per_tick: int,
        time_multiplier: float,
        is_polling_active: bool,
        evm_status: str = 'operational'
    ) -> tuple:
        """Update queue for one tick. Returns (new_queue, arrivals, departures)."""
        if not is_polling_active:
            departures = QueueDynamics.compute_departures(queue_length, throughput_rate, minutes_per_tick)
            return (max(0, queue_length - departures), 0, departures)

        arrivals = QueueDynamics.compute_arrivals(base_arrival_rate, minutes_per_tick, time_multiplier)

        effective_throughput = throughput_rate
        if evm_status == 'faulty':
            effective_throughput = 0
        elif evm_status == 'replaced':
            effective_throughput = throughput_rate * 0.7

        departures = QueueDynamics.compute_departures(queue_length, effective_throughput, minutes_per_tick)
        new_queue = max(0, queue_length + arrivals - departures)
        return (new_queue, arrivals, departures)
