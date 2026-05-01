"""
ElectaVerse — Queue Dynamics Engine
Models voter arrivals and departures using Poisson process.
"""

import random
import math
from config import SimulationConfig


class QueueDynamics:
    """Models queue behavior at polling booths using stochastic processes."""

    @staticmethod
    def poisson_sample(lam: float) -> int:
        """Generate a Poisson-distributed random number."""
        if lam <= 0:
            return 0
        # Knuth's algorithm for small lambda
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1

    @staticmethod
    def compute_arrivals(time_multiplier: float, booth_variance: float = 0.0) -> int:
        """
        Compute voter arrivals for this tick using Poisson distribution.
        
        Args:
            time_multiplier: Time-of-day multiplier for arrival rate
            booth_variance: Per-booth random variance (-1 to 1)
        """
        # Scale base rate by tick duration
        minutes_per_tick = SimulationConfig.SIMULATED_MINUTES_PER_TICK
        base_rate_per_minute = SimulationConfig.BASE_ARRIVAL_RATE / 10  # rate per minute
        
        lam = base_rate_per_minute * minutes_per_tick * time_multiplier * (1 + booth_variance * 0.3)
        lam = max(0, lam)
        
        return QueueDynamics.poisson_sample(lam)

    @staticmethod
    def compute_departures(queue_length: int, throughput_rate: float) -> int:
        """
        Compute how many voters are processed (leave queue) this tick.
        
        Args:
            queue_length: Current queue length
            throughput_rate: Booth's throughput in voters/hour
        """
        if queue_length == 0:
            return 0

        minutes_per_tick = SimulationConfig.SIMULATED_MINUTES_PER_TICK
        voters_per_minute = throughput_rate / 60
        
        # Add some variance to processing speed
        variance = random.uniform(0.8, 1.2)
        expected_departures = voters_per_minute * minutes_per_tick * variance
        
        # Can't depart more than queue length
        departures = min(queue_length, max(0, int(round(expected_departures))))
        return departures

    @staticmethod
    def update_queue(
        queue_length: int,
        throughput_rate: float,
        time_multiplier: float,
        is_polling_active: bool,
        evm_status: str = 'operational'
    ) -> tuple:
        """
        Update queue for one tick. Returns (new_queue_length, arrivals, departures).
        """
        if not is_polling_active:
            # During non-polling hours, queue drains but no new arrivals
            departures = QueueDynamics.compute_departures(queue_length, throughput_rate)
            return (max(0, queue_length - departures), 0, departures)

        # Compute arrivals
        booth_variance = random.uniform(-1, 1)
        arrivals = QueueDynamics.compute_arrivals(time_multiplier, booth_variance)

        # Compute departures (reduced if EVM is faulty)
        effective_throughput = throughput_rate
        if evm_status == 'faulty':
            effective_throughput = 0  # Booth halted
        elif evm_status == 'replaced':
            effective_throughput = throughput_rate * 0.7  # Slower after replacement

        departures = QueueDynamics.compute_departures(queue_length, effective_throughput)

        new_queue = max(0, queue_length + arrivals - departures)
        return (new_queue, arrivals, departures)
